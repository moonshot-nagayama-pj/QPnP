import dataclasses
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from queue import SimpleQueue
from typing import Callable, Iterator, Optional, Tuple

import serial.tools.list_ports
import structlog
from pint import DimensionalityError, Quantity
from serial import Serial

import pnpq.apt

from ..apt.protocol import (
    Address,
    AptMessage,
    AptMessage_MGMSG_HW_REQ_INFO,
    AptMessage_MGMSG_MOD_IDENTIFY,
    AptMessage_MGMSG_MOD_SET_CHANENABLESTATE,
    AptMessage_MGMSG_MOT_ACK_USTATUSUPDATE,
    AptMessage_MGMSG_MOT_GET_USTATUSUPDATE,
    AptMessage_MGMSG_MOT_MOVE_ABSOLUTE,
    AptMessage_MGMSG_MOT_MOVE_HOME,
    AptMessage_MGMSG_MOT_MOVE_HOMED,
    AptMessage_MGMSG_MOT_REQ_USTATUSUPDATE,
    AptMessage_MGMSG_POL_GET_PARAMS,
    AptMessage_MGMSG_POL_REQ_PARAMS,
    AptMessage_MGMSG_POL_SET_PARAMS,
    AptMessageForStreamParsing,
    AptMessageId,
    ChanIdent,
    EnableState,
)
from ..events import Event
from ..units import ureg
from .utils import timeout


@dataclass(kw_only=True)
class PolarizationControllerParams:
    velocity: int = 0
    home_position: Quantity = 0 * ureg.degree
    jog_step_1: int = 0
    jog_step_2: int = 0
    jog_step_3: int = 0


@dataclass(frozen=True, kw_only=True)
class PolarizationControllerThorlabsMPC320:
    # Serial connection parameters
    baudrate: int = 115200
    bytesize: int = serial.EIGHTBITS
    exclusive: bool = True
    parity: str = serial.PARITY_NONE
    rtscts: bool = True
    stopbits: int = serial.STOPBITS_ONE
    timeout: None | int = (
        None  # None means wait forever, until the requested number of bytes are received
    )

    active_channels: frozenset[ChanIdent] = frozenset(
        [
            ChanIdent.CHANNEL_1,
            ChanIdent.CHANNEL_2,
            ChanIdent.CHANNEL_3,
        ]
    )

    connection: Serial = field(init=False)

    rx_dispatcher_thread: threading.Thread = field(init=False)
    rx_dispatcher_thread_lock: threading.Lock = field(default_factory=threading.Lock)
    rx_dispatcher_subscribers: dict[int, SimpleQueue[AptMessage]] = field(
        default_factory=dict
    )
    rx_dispatcher_subscribers_lock: threading.Lock = field(
        default_factory=threading.Lock
    )

    tx_connection_lock: threading.Lock = field(default_factory=threading.Lock)

    tx_ordered_sender_awaiting_reply: threading.Event = field(
        default_factory=threading.Event
    )
    tx_ordered_sender_queue: SimpleQueue[
        Tuple[
            AptMessage,
            None
            | Callable[
                [
                    AptMessage,
                ],
                bool,
            ],
            None | SimpleQueue[AptMessage],
        ]
    ] = field(default_factory=SimpleQueue)
    tx_ordered_sender_thread: threading.Thread = field(init=False)
    tx_ordered_sender_thread_lock: threading.Lock = field(
        default_factory=threading.Lock
    )

    tx_poller_thread: threading.Thread = field(init=False)
    tx_poller_thread_lock: threading.Lock = field(default_factory=threading.Lock)

    log = structlog.get_logger()

    # The actual properties of the device start here.

    serial_number: str

    # Retrieved with MGMSG_POL_REQ_PARAMS

    # Stored in a non-frozen dataclass so that we can refresh them as
    # the configuration changes
    params: PolarizationControllerParams = field(
        default_factory=PolarizationControllerParams
    )

    def __post_init__(self) -> None:
        self.log.debug("Starting post-init...")

        # These devices tend to take a few seconds to start up, and
        # this library tends to be used as part of services that start
        # automatically on computer boot. For safety, wait here before
        # continuing initialization.
        time.sleep(1)

        port_found = False
        port = None
        for port in serial.tools.list_ports.comports():
            if port.serial_number == self.serial_number:
                port_found = True
                break
        if not port_found:
            raise ValueError(
                f"Serial number {self.serial_number} could not be found, failing intialization."
            )

        # Initializing the connection by passing a port to the Serial
        # constructor immediately opens the connection. It is not
        # necessary to call open() separately.
        object.__setattr__(
            self,
            "connection",
            Serial(
                baudrate=self.baudrate,
                bytesize=self.bytesize,
                exclusive=self.exclusive,
                parity=self.parity,
                port=port.device,
                rtscts=self.rtscts,
                stopbits=self.stopbits,
                timeout=self.timeout,
            ),
        )

        # Remove anything that might be left over in the buffer from
        # previous runs
        self.connection.reset_input_buffer()
        self.connection.reset_output_buffer()

        # Start background threads.
        #
        # TODO use some sort of thread manager to safely deal with
        # uncaught exceptions and other errors.
        object.__setattr__(
            self,
            "tx_poller_thread",
            threading.Thread(target=self.tx_poll, daemon=True),
        )
        self.tx_poller_thread.start()

        object.__setattr__(
            self,
            "rx_dispatcher_thread",
            threading.Thread(target=self.rx_dispatch, daemon=True),
        )
        self.rx_dispatcher_thread.start()

        object.__setattr__(
            self,
            "tx_ordered_sender_thread",
            threading.Thread(target=self.tx_ordered_send, daemon=True),
        )
        self.tx_ordered_sender_thread.start()

        self.send_message_no_reply(
            AptMessage_MGMSG_HW_REQ_INFO(
                destination=Address.GENERIC_USB,
                source=Address.HOST_CONTROLLER,
            )
        )

        self.refresh_params()

        self.log.debug("Finishing post-init...")

    # TODO from a multi-threading point of view, it might be much
    # easier to assume that, for the lifetime of a program, a
    # connection is held by a single object that cannot be
    # closed. However, we should still probably implement a context
    # manager for this object.
    #
    # The tricky part is managing the threads; they will all need to
    # be paused before closing the serial connection... and then how
    # do we clean up the child threads if this object gets cleaned up?

    # def __enter__(self) -> None:
    #     self.open()

    # def __exit__(self, exc_type, exc_value, exc_tb) -> None:
    #     self.close()

    # def open(self) -> None:
    #     self.connection.open()

    # def close(self) -> None:
    #     self.connection.flush()
    #     self.connection.close()

    def rx_dispatch(self) -> None:
        with self.rx_dispatcher_thread_lock:
            while True:
                partial_message: None | AptMessageForStreamParsing = None
                full_message: Optional[AptMessage] = None
                try:
                    message_bytes = self.connection.read(6)
                    partial_message = AptMessageForStreamParsing.from_bytes(
                        message_bytes
                    )
                    message_id = partial_message.message_id
                    if partial_message.data_length != 0:
                        message_bytes = message_bytes + self.connection.read(
                            partial_message.data_length
                        )
                    if partial_message.message_id in AptMessageId:
                        message_id = AptMessageId(partial_message.message_id)
                        full_message = getattr(
                            pnpq.apt.protocol, f"AptMessage_{message_id.name}"
                        ).from_bytes(message_bytes)
                        assert isinstance(full_message, AptMessage)
                        self.log.debug(
                            event=Event.RX_MESSAGE_KNOWN,
                            message=full_message,
                        )
                        with self.rx_dispatcher_subscribers_lock:
                            for queue in self.rx_dispatcher_subscribers.values():
                                queue.put(full_message)
                    else:
                        # Log and discard unknown messages
                        self.log.debug(
                            event=Event.RX_MESSAGE_UNKNOWN,
                            message=partial_message,
                            bytes=message_bytes,
                        )
                # TODO this is too general, do not catch Exception
                except Exception as e:  # pylint: disable=W0718
                    self.log.error(
                        event=Event.UNCAUGHT_EXCEPTION,
                        exc_info=e,
                        partial_message=partial_message,
                        full_message=full_message,
                    )

    def tx_poll(self) -> None:
        with self.tx_poller_thread_lock:
            while True:
                for chan in self.active_channels:
                    self.send_message_unordered(
                        AptMessage_MGMSG_MOT_REQ_USTATUSUPDATE(
                            chan_ident=chan,
                            destination=Address.GENERIC_USB,
                            source=Address.HOST_CONTROLLER,
                        )
                    )
                self.send_message_unordered(
                    AptMessage_MGMSG_MOT_ACK_USTATUSUPDATE(
                        destination=Address.GENERIC_USB,
                        source=Address.HOST_CONTROLLER,
                    )
                )
                # If we are currently waiting for a reply to a message
                # we sent, poll every 0.2 seconds to ensure quick
                # response to state changes. If we are not waiting for
                # a reply, poll at least once every second to reduce
                # the amount of noise in logs.
                #
                # The tx_ordered_sender thread can request a faster
                # update by setting the
                # tx_ordered_sender_awaiting_reply event.
                if self.tx_ordered_sender_awaiting_reply.is_set():
                    time.sleep(0.2)
                else:
                    # The documentation for
                    # MGMSG_MOT_ACK_USTATUSUPDATE suggests that it
                    # should be sent at least once a second. This will
                    # probably send slightly _less_ than once a
                    # second, so, if we start having issues, we should
                    # decrease this interval.
                    self.tx_ordered_sender_awaiting_reply.wait(1)

    @contextmanager
    def rx_subscribe(self) -> Iterator[SimpleQueue[AptMessage]]:
        thread_id = threading.get_ident()
        queue: SimpleQueue[AptMessage] = SimpleQueue()
        with self.rx_dispatcher_subscribers_lock:
            self.rx_dispatcher_subscribers[thread_id] = queue
        try:
            yield queue
        finally:
            with self.rx_dispatcher_subscribers_lock:
                self.rx_dispatcher_subscribers.pop(thread_id)

    def tx_ordered_send(self) -> None:
        # TODO wrap in exception handler
        with self.tx_ordered_sender_thread_lock:
            while True:
                message, match_reply, reply_queue = self.tx_ordered_sender_queue.get()
                self.log.debug(
                    event=Event.TX_MESSAGE_ORDERED,
                    message=message,
                )
                if match_reply is None:
                    with self.tx_connection_lock:
                        self.connection.write(message.to_bytes())
                    continue
                assert reply_queue is not None
                # TODO We are subscribing to incoming messages just
                # *before* sending our message. Ideally we should
                # subscribe immediately *after* sending the
                # message. This is a little tricky to coordinate in
                # the current architecture.
                with timeout(10) as check_timeout, self.rx_subscribe() as receive_queue:
                    with self.tx_connection_lock:
                        self.connection.write(message.to_bytes())
                    self.tx_ordered_sender_awaiting_reply.set()
                    while check_timeout():
                        message = receive_queue.get(timeout=10)
                        if match_reply(message):
                            self.tx_ordered_sender_awaiting_reply.clear()
                            reply_queue.put(message)
                            break

    def send_message_unordered(self, message: AptMessage) -> None:
        """Send a message as soon as the connection lock will allow,
        bypassing the message queue. This allows us to poll for status
        messages while the main message thread is blocked waiting for
        a reply.

        """
        with self.tx_connection_lock:
            self.log.debug(event=Event.TX_MESSAGE_UNORDERED, message=message)
            self.connection.write(message.to_bytes())

    def send_message_no_reply(self, message: AptMessage) -> None:
        """Send a message and return immediately, without waiting for any reply."""
        self.tx_ordered_sender_queue.put((message, None, None))

    def send_message_expect_reply(
        self,
        message: AptMessage,
        match_reply: Callable[
            [
                AptMessage,
            ],
            bool,
        ],
    ) -> AptMessage:
        """Send a message and block until an expected reply is
        received.

        message: AptMessage - The message to send

        match_reply: Callable - A function that returns True if a
        received message should be recognized as a reply to this
        message, and False otherwise.
        """

        # There's probably a way to pool queues for re-use, creating
        # one per thread, rather than creating a new queue for every
        # request. However, considering that we send very few
        # commands, this is probably fine.
        reply_queue: SimpleQueue[AptMessage] = SimpleQueue()
        self.tx_ordered_sender_queue.put((message, match_reply, reply_queue))
        return reply_queue.get()

    def home(self, chan_ident: ChanIdent) -> None:
        self.set_channel_enabled(chan_ident, True)
        start_time = time.perf_counter()
        self.send_message_expect_reply(
            AptMessage_MGMSG_MOT_MOVE_HOME(
                chan_ident=chan_ident,
                destination=Address.GENERIC_USB,
                source=Address.HOST_CONTROLLER,
            ),
            lambda message: (
                isinstance(message, AptMessage_MGMSG_MOT_MOVE_HOMED)
                and message.chan_ident == chan_ident
                and message.destination == Address.HOST_CONTROLLER
                and message.source == Address.GENERIC_USB
            ),
        )
        elapsed_time = time.perf_counter() - start_time
        self.log.debug("home command finished", elapsed_time=elapsed_time)
        self.set_channel_enabled(chan_ident, False)

    def identify(self, chan_ident: ChanIdent) -> None:
        self.send_message_no_reply(
            AptMessage_MGMSG_MOD_IDENTIFY(
                chan_ident=chan_ident,
                destination=Address.GENERIC_USB,
                source=Address.HOST_CONTROLLER,
            )
        )

    def move_absolute(self, chan_ident: ChanIdent, position: Quantity) -> None:
        # Convert distance to mpc320 steps and check for errors
        absolute_distance = round(position.to("mpc320_step").magnitude)
        absolute_degree = round(position.to("degree").magnitude)
        if absolute_degree < 0 or absolute_degree > 170:
            raise ValueError(
                f"Absolute position must be between 0 and 170 degrees (or equivalent). Value given was {absolute_degree} degrees."
            )
        self.set_channel_enabled(chan_ident, True)
        self.log.debug("Sending move_absolute command...")
        start_time = time.perf_counter()
        self.send_message_expect_reply(
            AptMessage_MGMSG_MOT_MOVE_ABSOLUTE(
                chan_ident=chan_ident,
                absolute_distance=absolute_distance,
                destination=Address.GENERIC_USB,
                source=Address.HOST_CONTROLLER,
            ),
            lambda message: (
                isinstance(message, AptMessage_MGMSG_MOT_GET_USTATUSUPDATE)
                and message.chan_ident == chan_ident
                and message.position == absolute_distance
                and message.destination == Address.HOST_CONTROLLER
                and message.source == Address.GENERIC_USB
            ),
        )
        elapsed_time = time.perf_counter() - start_time
        self.log.debug("move_absolute command finished", elapsed_time=elapsed_time)
        self.set_channel_enabled(chan_ident, False)

    def refresh_params(self) -> None:
        params = self.send_message_expect_reply(
            AptMessage_MGMSG_POL_REQ_PARAMS(
                destination=Address.GENERIC_USB,
                source=Address.HOST_CONTROLLER,
            ),
            lambda message: (isinstance(message, AptMessage_MGMSG_POL_GET_PARAMS)),
        )
        assert isinstance(params, AptMessage_MGMSG_POL_GET_PARAMS)
        self.params.velocity = params.velocity
        self.params.home_position = params.home_position * ureg.mpc320_step
        self.params.jog_step_1 = params.jog_step_1
        self.params.jog_step_2 = params.jog_step_2
        self.params.jog_step_3 = params.jog_step_3

    def set_channel_enabled(self, chan_ident: ChanIdent, enabled: bool) -> None:
        if enabled:
            chan_bitmask = chan_ident
        else:
            chan_bitmask = ChanIdent(0)
        self.send_message_expect_reply(
            AptMessage_MGMSG_MOD_SET_CHANENABLESTATE(
                chan_ident=chan_bitmask,
                enable_state=EnableState.CHANNEL_ENABLED,
                destination=Address.GENERIC_USB,
                source=Address.HOST_CONTROLLER,
            ),
            lambda message: (
                isinstance(message, AptMessage_MGMSG_MOT_GET_USTATUSUPDATE)
                and message.chan_ident == chan_ident
                and message.status.ENABLED == enabled
                and message.destination == Address.HOST_CONTROLLER
                and message.source == Address.GENERIC_USB
            ),
        )

    def set_params(
        self,
        velocity: None | int = None,
        home_position: None | Quantity = None,
        jog_step_1: None | int = None,
        jog_step_2: None | int = None,
        jog_step_3: None | int = None,
    ) -> None:
        replaced_params: dict[str, int | Quantity] = {}
        if velocity is not None:
            replaced_params["velocity"] = velocity
        if home_position is not None:
            replaced_params["home_position"] = home_position
        if jog_step_1 is not None:
            replaced_params["jog_step_1"] = jog_step_1
        if jog_step_2 is not None:
            replaced_params["jog_step_2"] = jog_step_2
        if jog_step_3 is not None:
            replaced_params["jog_step_3"] = jog_step_3
        new_params = dataclasses.replace(self.params, **replaced_params)  # type: ignore
        self.send_message_no_reply(
            AptMessage_MGMSG_POL_SET_PARAMS(
                destination=Address.GENERIC_USB,
                source=Address.HOST_CONTROLLER,
                velocity=new_params.velocity,
                home_position=new_params.home_position.magnitude,
                jog_step_1=new_params.jog_step_1,
                jog_step_2=new_params.jog_step_2,
                jog_step_3=new_params.jog_step_3,
            )
        )
        time.sleep(1)
        self.refresh_params()
