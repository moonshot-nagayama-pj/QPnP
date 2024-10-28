import dataclasses
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from queue import SimpleQueue
from typing import Callable, Iterator, Optional, Tuple

import serial.tools.list_ports
import structlog
from pint import Quantity
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

from ..apt.connection import AptConnection
@dataclass(frozen=True, kw_only=True)
class PolarizationControllerThorlabsMPC320:
    connection: AptConnection

    log = structlog.get_logger()

    # Stored in a non-frozen dataclass so that we can refresh them as
    # the configuration changes
    params: PolarizationControllerParams = field(
        default_factory=PolarizationControllerParams
    )

    def __post_init__(self) -> None:
        self.refresh_params()

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
