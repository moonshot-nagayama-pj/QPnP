import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from queue import Queue, ShutDown
from types import TracebackType
from typing import Callable, Iterator, Optional, Tuple

import serial.tools.list_ports
import structlog
from serial import Serial

import pnpq.apt
from pnpq.errors import InvalidStateException

from ..devices.utils import timeout
from ..events import Event
from .protocol import (
    Address,
    AptMessage,
    AptMessage_MGMSG_HW_REQ_INFO,
    AptMessage_MGMSG_HW_STOP_UPDATEMSGS,
    AptMessageForStreamParsing,
    AptMessageId,
)


@dataclass(frozen=True, kw_only=True)
class AptConnection:
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

    connection: Serial = field(init=False)

    rx_dispatcher_thread: threading.Thread = field(init=False)
    rx_dispatcher_thread_lock: threading.Lock = field(default_factory=threading.Lock)
    rx_dispatcher_subscribers: dict[int, Queue[AptMessage]] = field(
        default_factory=dict
    )
    rx_dispatcher_subscribers_lock: threading.Lock = field(
        default_factory=threading.Lock
    )

    tx_connection_lock: threading.Lock = field(default_factory=threading.Lock)

    tx_ordered_sender_awaiting_reply: threading.Event = field(
        default_factory=threading.Event
    )
    tx_ordered_sender_queue: Queue[
        Tuple[
            AptMessage,
            None
            | Callable[
                [
                    AptMessage,
                ],
                bool,
            ],
            None | Queue[AptMessage],
        ]
    ] = field(default_factory=Queue)
    tx_ordered_sender_thread: threading.Thread = field(init=False)
    tx_ordered_sender_thread_lock: threading.Lock = field(
        default_factory=threading.Lock
    )

    log = structlog.get_logger()

    stop_event: threading.Event = field(default_factory=threading.Event)

    # Required inputs are defined below.
    serial_number: str

    def __enter__(self) -> "AptConnection":
        self.open()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()

    def open(self) -> None:
        self.log.debug("Opening connection...")

        # Throw error if connection is attempted to be re-opened after being closed once
        if self.stop_event.is_set():
            self.log.error(
                "Connection that was already closed was tried to be re-opened."
            )
            raise InvalidStateException

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

        self.send_message_no_reply(
            AptMessage_MGMSG_HW_STOP_UPDATEMSGS(
                destination=Address.GENERIC_USB,
                source=Address.HOST_CONTROLLER,
            )
        )
        time.sleep(0.1)
        self.connection.flush()

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

        self.log.debug("Finished opening connection...")

    def close(self) -> None:
        self.send_message_unordered(
            AptMessage_MGMSG_HW_STOP_UPDATEMSGS(
                destination=Address.GENERIC_USB,
                source=Address.HOST_CONTROLLER,
            )
        )
        self.stop_event.set()

        self.tx_ordered_sender_queue.shutdown()
        self.tx_ordered_sender_thread.join()

        self.connection.flush()
        self.connection.close()

        self.rx_dispatcher_thread.join()

        self.log.debug("Successfully closed the APTConnection.")

    def is_closed(self) -> bool:
        return self.stop_event.is_set()

    def rx_dispatch(self) -> None:
        with self.rx_dispatcher_thread_lock:
            while not self.stop_event.is_set():
                partial_message: None | AptMessageForStreamParsing = None
                full_message: Optional[AptMessage] = None

                try:
                    message_bytes = self.connection.read(6)
                # Serial bus not connected error
                except Exception as e:  # pylint: disable=W0718
                    self.log.debug(
                        event="Shutting down rx dispatcher. Received expected error.",
                        exc_info=e,
                    )
                    break
                try:
                    partial_message = AptMessageForStreamParsing.from_bytes(
                        message_bytes
                    )
                    message_id = partial_message.message_id
                    if partial_message.data_length != 0:
                        try:
                            message_bytes = message_bytes + self.connection.read(
                                partial_message.data_length
                            )
                        # Serial bus not connected error
                        except Exception as e:  # pylint: disable=W0718
                            self.log.debug(
                                event="Shutting down rx dispatcher. Received expected error.",
                                exc_info=e,
                            )
                            break

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

    @contextmanager
    def rx_subscribe(self) -> Iterator[Queue[AptMessage]]:
        thread_id = threading.get_ident()
        queue: Queue[AptMessage] = Queue()
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
            while not self.stop_event.is_set():
                try:
                    message, match_reply, reply_queue = (
                        self.tx_ordered_sender_queue.get()
                    )
                except ShutDown:
                    break
                self.log.debug(
                    event=Event.TX_MESSAGE_ORDERED,
                    message=message,
                )
                if match_reply is None:
                    with self.tx_connection_lock:
                        self.connection.write(message.to_bytes())
                        # Some no-reply commands take time to
                        # complete. Sending other messages while this
                        # is happening could cause the device's
                        # internal software to fail until a hard reset
                        # is peformed.
                        #
                        # This behavior has been observed with the
                        # MGMSG_MOD_SET_CHANENABLESTATE message on the
                        # MPC320, where rapidly toggling a channel off
                        # and then on again seems to cause the device
                        # to stop responding to commands.
                        #
                        # Unlike with reply-expected commands, below,
                        # this also blocks any users of
                        # send_message_unordered.
                        #
                        # The sleep time set here is just a reasonable
                        # guess based on observation of device
                        # behavior. It is not based on information
                        # from the APT specification.
                        time.sleep(0.2)
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
                    # It doesn't seem to cause harm to let the sort of
                    # messages we typically poll for using
                    # send_message_unordered (REQ_USTATUSUPDATE,
                    # ACK_USTATUSUPDATE) continue to be sent while we
                    # wait for replies to messages, so we release the
                    # connection lock here. Compare this to no-reply
                    # messages above, where we block the sending of
                    # all messages for a short period of time out of
                    # an abundance of caution.
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
        reply_queue: Queue[AptMessage] = Queue()
        self.tx_ordered_sender_queue.put((message, match_reply, reply_queue))
        return reply_queue.get()
