import threading
import time
from dataclasses import dataclass, field
from typing import TypedDict, cast

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
    AptMessage_MGMSG_MOT_MOVE_COMPLETED_6_BYTES,
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
from ..units import pnpq_ureg


class PolarizationControllerParams(TypedDict):
    #: Dimensionality must be ([angle] / [time]) or mpc320_velocity
    velocity: Quantity
    #: Dimensionality must be [angle] or mpc320_step
    home_position: Quantity
    #: Dimensionality must be [angle] or mpc320_step
    jog_step_1: Quantity
    #: Dimensionality must be [angle] or mpc320_step
    jog_step_2: Quantity
    #: Dimensionality must be [angle] or mpc320_step
    jog_step_3: Quantity


@dataclass(frozen=True, kw_only=True)
class PolarizationControllerThorlabsMPC:
    connection: AptConnection

    log = structlog.get_logger()

    # Polling threads
    tx_poller_thread: threading.Thread = field(init=False)
    tx_poller_thread_lock: threading.Lock = field(default_factory=threading.Lock)

    # Setup channels for the device
    available_channels: frozenset[ChanIdent] = frozenset([])

    def __post_init__(self) -> None:
        # Start polling thread
        object.__setattr__(
            self,
            "tx_poller_thread",
            threading.Thread(target=self.tx_poll, daemon=True),
        )
        self.tx_poller_thread.start()

    # Polling thread for sending status update requests
    def tx_poll(self) -> None:
        with self.tx_poller_thread_lock:
            while not self.connection.stop_event.is_set():
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

    def get_status_all(self) -> tuple[AptMessage_MGMSG_MOT_GET_USTATUSUPDATE, ...]:
        all_status = []
        for channel in self.available_channels:
            status = self.get_status(channel)
            all_status.append(status)
        return tuple(all_status)

    def get_status(
        self, chan_ident: ChanIdent
    ) -> AptMessage_MGMSG_MOT_GET_USTATUSUPDATE:
        msg = self.connection.send_message_expect_reply(
            AptMessage_MGMSG_MOT_REQ_USTATUSUPDATE(
                chan_ident=chan_ident,
                destination=Address.GENERIC_USB,
                source=Address.HOST_CONTROLLER,
            ),
            lambda message: (
                isinstance(message, AptMessage_MGMSG_MOT_GET_USTATUSUPDATE)
                and message.chan_ident == chan_ident
                and message.destination == Address.HOST_CONTROLLER
                and message.source == Address.GENERIC_USB
            ),
        )
        return cast(AptMessage_MGMSG_MOT_GET_USTATUSUPDATE, msg)

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
        """Jogs the device forward or backwards in small steps.
        Experimentally, jog steps of 50 or greater seem to work the
        best.

        The specific number of steps per jog can be set via the
        :py:func:`set_params` function.

        :param chan_ident: The motor channel to jog.
        :param jog_direction: The direction the paddle should move in.

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
                isinstance(message, AptMessage_MGMSG_MOT_MOVE_COMPLETED_6_BYTES)
                and message.chan_ident == chan_ident
                and message.destination == Address.HOST_CONTROLLER
                and message.source == Address.GENERIC_USB
            ),
        )
        self.set_channel_enabled(chan_ident, False)

    def move_absolute(self, chan_ident: ChanIdent, position: Quantity) -> None:
        # Convert distance to mpc320 steps and check for errors
        absolute_distance = position.to("mpc320_step").magnitude
        absolute_degree = position.to("degree").magnitude
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

    def get_params(self) -> PolarizationControllerParams:
        params = self.connection.send_message_expect_reply(
            AptMessage_MGMSG_POL_REQ_PARAMS(
                destination=Address.GENERIC_USB,
                source=Address.HOST_CONTROLLER,
            ),
            lambda message: (isinstance(message, AptMessage_MGMSG_POL_GET_PARAMS)),
        )
        assert isinstance(params, AptMessage_MGMSG_POL_GET_PARAMS)
        result: PolarizationControllerParams = {
            "velocity": params.velocity * pnpq_ureg.mpc320_velocity,
            "home_position": params.home_position * pnpq_ureg.mpc320_step,
            "jog_step_1": params.jog_step_1 * pnpq_ureg.mpc320_step,
            "jog_step_2": params.jog_step_2 * pnpq_ureg.mpc320_step,
            "jog_step_3": params.jog_step_3 * pnpq_ureg.mpc320_step,
        }
        return result

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
        velocity: None | Quantity = None,
        home_position: None | Quantity = None,
        jog_step_1: None | Quantity = None,
        jog_step_2: None | Quantity = None,
        jog_step_3: None | Quantity = None,
    ) -> None:
        # First load existing params

        params = self.get_params()
        # Replace params that need to be changed
        if velocity is not None:
            params["velocity"] = cast(Quantity, velocity.to("mpc320_velocity"))
        if home_position is not None:
            params["home_position"] = cast(Quantity, home_position.to("mpc320_step"))
        if jog_step_1 is not None:
            params["jog_step_1"] = cast(Quantity, jog_step_1.to("mpc320_step"))
        if jog_step_2 is not None:
            params["jog_step_2"] = cast(Quantity, jog_step_2.to("mpc320_step"))
        if jog_step_3 is not None:
            params["jog_step_3"] = cast(Quantity, jog_step_3.to("mpc320_step"))
        # Send params to device
        self.connection.send_message_no_reply(
            AptMessage_MGMSG_POL_SET_PARAMS(
                destination=Address.GENERIC_USB,
                source=Address.HOST_CONTROLLER,
                velocity=round(params["velocity"].magnitude),
                home_position=round(params["home_position"].magnitude),
                jog_step_1=round(params["jog_step_1"].magnitude),
                jog_step_2=round(params["jog_step_2"].magnitude),
                jog_step_3=round(params["jog_step_3"].magnitude),
            )
        )


@dataclass(frozen=True, kw_only=True)
class PolarizationControllerThorlabsMPC320(PolarizationControllerThorlabsMPC):
    # Setup channels for the device
    available_channels: frozenset[ChanIdent] = frozenset(
        [
            ChanIdent.CHANNEL_1,
            ChanIdent.CHANNEL_2,
            ChanIdent.CHANNEL_3,
        ]
    )


@dataclass(frozen=True, kw_only=True)
class PolarizationControllerThorlabsMPC220(PolarizationControllerThorlabsMPC):
    # Setup channels for the device
    available_channels: frozenset[ChanIdent] = frozenset(
        [
            ChanIdent.CHANNEL_1,
            ChanIdent.CHANNEL_2,
        ]
    )
