import dataclasses
import threading
import time
from dataclasses import dataclass, field

import structlog
from pint import Quantity

from ..apt.connection import AptConnection
from ..apt.protocol import (
    Address,
    AptMessage_MGMSG_MOD_IDENTIFY,
    AptMessage_MGMSG_MOD_SET_CHANENABLESTATE,
    AptMessage_MGMSG_MOT_ACK_USTATUSUPDATE,
    AptMessage_MGMSG_MOT_GET_USTATUSUPDATE,
    AptMessage_MGMSG_MOT_MOVE_ABSOLUTE,
    AptMessage_MGMSG_MOT_MOVE_COMPLETED,
    AptMessage_MGMSG_MOT_MOVE_HOME,
    AptMessage_MGMSG_MOT_MOVE_HOMED,
    AptMessage_MGMSG_MOT_MOVE_JOG,
    AptMessage_MGMSG_MOT_REQ_USTATUSUPDATE,
    AptMessage_MGMSG_POL_GET_PARAMS,
    AptMessage_MGMSG_POL_REQ_PARAMS,
    AptMessage_MGMSG_POL_SET_PARAMS,
    ChanIdent,
    EnableState,
    JogDirection,
)
from ..units import ureg


@dataclass(kw_only=True)
class PolarizationControllerParams:
    velocity: int = 0
    home_position: Quantity = 0 * ureg.degree
    jog_step_1: int = 0
    jog_step_2: int = 0
    jog_step_3: int = 0


@dataclass(frozen=True, kw_only=True)
class PolarizationControllerThorlabsMPC320:
    connection: AptConnection

    log = structlog.get_logger()

    # Polling threads
    tx_poller_thread: threading.Thread = field(init=False)
    tx_poller_thread_lock: threading.Lock = field(default_factory=threading.Lock)

    # Setup channels for the device
    available_channels: frozenset[ChanIdent] = frozenset(
        [
            ChanIdent.CHANNEL_1,
            ChanIdent.CHANNEL_2,
            ChanIdent.CHANNEL_3,
        ]
    )

    # Stored in a non-frozen dataclass so that we can refresh them as
    # the configuration changes
    params: PolarizationControllerParams = field(
        default_factory=PolarizationControllerParams
    )

    def __post_init__(self) -> None:
        # Start polling thread
        object.__setattr__(
            self,
            "tx_poller_thread",
            threading.Thread(target=self.tx_poll, daemon=True),
        )
        self.tx_poller_thread.start()

        self.refresh_params()

    # Polling thread for sending status update requests
    def tx_poll(self) -> None:
        with self.tx_poller_thread_lock:
            while True:
                for chan in self.available_channels:
                    self.connection.send_message_unordered(
                        AptMessage_MGMSG_MOT_REQ_USTATUSUPDATE(
                            chan_ident=chan,
                            destination=Address.GENERIC_USB,
                            source=Address.HOST_CONTROLLER,
                        )
                    )
                self.connection.send_message_unordered(
                    AptMessage_MGMSG_MOT_ACK_USTATUSUPDATE(
                        destination=Address.GENERIC_USB,
                        source=Address.HOST_CONTROLLER,
                    )
                )
                # If we are currently waiting for a reply to a message
                # we sent, poll every 0.2 seconds to ensure a
                # relatively quick response to state changes that we
                # observe using status update messages. If we are not
                # waiting for a reply, poll at least once every second
                # to reduce the amount of noise in logs.
                #
                # The tx_ordered_sender thread can request a faster
                # update by setting the
                # tx_ordered_sender_awaiting_reply event.
                if self.connection.tx_ordered_sender_awaiting_reply.is_set():
                    time.sleep(0.2)
                else:
                    # The documentation for
                    # MGMSG_MOT_ACK_USTATUSUPDATE suggests that it
                    # should be sent at least once a second. This will
                    # probably send slightly less frequently than once
                    # a second, so, if we start having issues, we
                    # should decrease this interval.
                    self.connection.tx_ordered_sender_awaiting_reply.wait(1)

    def home(self, chan_ident: ChanIdent) -> None:
        self.set_channel_enabled(chan_ident, True)
        start_time = time.perf_counter()
        self.connection.send_message_expect_reply(
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
        self.connection.send_message_no_reply(
            AptMessage_MGMSG_MOD_IDENTIFY(
                chan_ident=chan_ident,
                destination=Address.GENERIC_USB,
                source=Address.HOST_CONTROLLER,
            )
        )

    def jog(self, chan_ident: ChanIdent, jog_direction: JogDirection) -> None:
        """
        Jogs the device forward or backwards in small steps.

        The specific amount of steps per jog can be set via the PolarizationcontrollerThorlabsMPC320.set_params() function.
        """

        self.set_channel_enabled(chan_ident, True)
        self.connection.send_message_expect_reply(
            AptMessage_MGMSG_MOT_MOVE_JOG(
                chan_ident=chan_ident,
                jog_direction=jog_direction,
                destination=Address.GENERIC_USB,
                source=Address.HOST_CONTROLLER,
            ),
            lambda message: (
                isinstance(message, AptMessage_MGMSG_MOT_MOVE_COMPLETED)
                and message.chan_ident == chan_ident
                and message.destination == Address.HOST_CONTROLLER
                and message.source == Address.GENERIC_USB
            ),
        )
        self.set_channel_enabled(chan_ident, False)

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
        self.connection.send_message_expect_reply(
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
        params = self.connection.send_message_expect_reply(
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
        self.connection.send_message_expect_reply(
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
        self.connection.send_message_no_reply(
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
