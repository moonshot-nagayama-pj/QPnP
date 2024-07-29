# ODL STUB
import time, logging
from pnpq.devices.optical_delay_line import OpticalDelayLine

from pnpq.errors import (
    DevicePortNotFoundError,
    DeviceDisconnectedError,
    OdlMoveNotCompleted,
    OdlHomeNotCompleted,
    OdlGetPosNotCompleted,
    OdlMoveOutofRangeError,
)

ODL_HOMED_POSITION = 0

class OdlThorlabsStub(OpticalDelayLine):
    """Stub ODL Device Class"""
    max_move: int
    """represents maximum specified length for moving on the stage"""

    min_move: int
    """represents minimum specified length for moving on the stage: usually zero"""

    resolution: int
    """represents minimum specified length for moving on the stage: usually zero"""

    home_timeout: int
    """required time for completing home in seconds"""

    move_timeout: int
    """required time for completing home in seconds"""

    auto_update: bool
    """a flag for checking automatic update is active or inactive"""

    currrent_steps: int | None
    """current position of optical delay line in steps"""

    def __init__(self) -> None:
        # Stub Serial Number
        # TODO: Custom serial number from initializer
        self.name = "Thorlabs Stub ODL"
        self.model = "KBD101 driver DDS100/M Stage"

        self.home_timeout = 25
        self.move_timeout = 4
        self.resolution = 2000
        self.auto_update = False
        self.max_move = 100
        self.min_move = 0
        self.logger = logging.getLogger(f"{self}")

        # Current Position of the device in steps
        self.current_position: int = 0

        # Is connected to the device (used internally)
        self.connected: bool = False

        # Enabled channels (enable 1 by default, used internally)
        self.enabled_channels: set = {1}

    def __stub_check_channel(self, chanid: int) -> bool:
        return chanid in self.enabled_channels

    def __ensure_port_open(self) -> None:
        if not self.conn.is_open:
            self.logger.error("disconnected")
            raise DeviceDisconnectedError(f"{self} is disconnected")

    def __ensure_steps_in_range(self, steps: int) -> None:
        max_threshold = self.max_move * self.resolution
        min_threshold = self.min_move * self.resolution

        if min_threshold <= steps <= max_threshold:
            return

        self.logger.error(f"ODL({self}) required steps:({steps}) is out of range")
        raise OdlMoveOutofRangeError(
            f"Move request for device{self} is out of range min({self.min_move}) - max({self.max_move})"
        )

    def connect(self) -> None:
        if self.conn.is_open:
            self.logger.warning("ODL ({self}) serial connection is already open")
        self.conn.open()

        if not self.conn.is_open:
            raise DeviceDisconnectedError(f"ODL device is disconneced")
        self.logger.info(f"({self}): Connecting to Thorlabs ODL module")
        # Enable Channel ID (0)
        self.conn.write(ENABLE_CHANNEL_SET_COMMAND)
        time.sleep(0.1)
        self.conn.write(ENABLE_CHANNEL_GET_COMMAND)
        enable_channel_result = self.__wait_for_reply(b"\x12\x02", 5)
        if enable_channel_result is None:
            self.logger.error(f"can not enable odl channel")

    def identify(self) -> None:
        self.__ensure_port_open()
        self.conn.write(ODL_IDENTIFY_COMMAND)

    def __wait_for_reply(self, sequence: bytes | None, timeout: int) -> bytes | None:
        retries = timeout
        result = b""
        while retries > 0:
            num_read_bytes = self.conn.in_waiting

            result = self.conn.read(num_read_bytes)

            self.logger.debug(
                f"ODL wait for reply: {sequence}, results: {result}, retry count: {retries}"
            )
            if num_read_bytes > 0 and result.find(sequence) != -1:
                self.logger.info(f"The response found: {result} ")
                return result
            time.sleep(1)
            retries -= 1

    def move(self, move_mm: int) -> None:
        move_steps = move_mm * self.resolution
        self.logger.debug(
            f"move command recieved: move_mm:({move_mm})->move_steps:({move_steps})"
        )
        self.__ensure_port_open()
        self.__ensure_steps_in_range(move_steps)

        msg = ODL_MOVE_COMMAND + (move_steps).to_bytes(4, byteorder="little")
        self.conn.write(msg)

        move_result = self.__wait_for_reply(b"\x64\04", self.move_timeout)
        if not move_result:
            self.logger.error(f"move command is not completed")
            # raise OdlMoveNotCompleted(
            #    f"ODL({self}): No moved_completed response has been received"
            # )
        self.currrent_steps = move_steps
        self.logger.debug(f"Move completed position_steps({self.currrent_steps})!")

    def step_forward(self, steps: int) -> None:
        """Move forward by a specified number of steps"""
        self.__ensure_port_open()
        self.__ensure_steps_in_range(steps)
        self.__ensure_final_in_range(self.current_position, steps)
        if not self.__stub_check_channel(1):
            # Do nothing if channel is not enabled
            return
        self.logger.info(f"Step forward position_steps: {steps}")
        self.current_position += steps
        # Delay to simulate move forward (for now: v=1ms/step)
        time.sleep(abs(steps) / 1000)
        # TODO: Return a fake reply from the device

    def __ensure_final_in_range(self, current_position: int, steps: int) -> None:

        max_threshold = self.max_move * self.resolution
        min_threshold = self.min_move * self.resolution

        next_position = current_position + steps
        if min_threshold <= next_position <= max_threshold:
            return
        raise OdlMoveOutofRangeError(
            f"The relative change position request for device{self} is out of range min({self.min_move}) - max({self.max_move})"
        )

    def step_backward(self, steps: int) -> None:
        """Move backward by a specified number of steps"""
        self.__ensure_port_open()
        self.__ensure_steps_in_range(steps)
        # negate steps
        steps = -steps
        self.__ensure_final_in_range(self.current_position, steps)
        if not self.__stub_check_channel(1):
            # Do nothing if channel is not enabled
            return
        self.logger.info(f"Step backward position_steps: {-steps}")
        self.current_position += steps
        # Delay to simulate move forward (for now: v=1ms/step)
        time.sleep(abs(steps) / 1000)
        # TODO: Return a fake reply from the device

    def auto_update_start(self) -> bytes | None:
        self.logger.info("call auto update start cmd")
        self.__ensure_port_open()
        self.conn.write(START_UPDATE_COMMAND)
        result = self.__wait_for_reply(b"\x91\x04", self.move_timeout)

        self.logger.debug(f"auto_update_start result: {result}")
        if result is None:
            self.logger.warning("auto update start command is not completed")
        else:
            self.auto_update = True
        return result

    def auto_update_stop(self) -> bytes | None:
        self.logger.info("cal auto update stop cmd")
        self.__ensure_port_open()

        self.conn.write(STOP_UPDATE_COMMAND)
        result = self.__wait_for_reply(b"\x91\x04", 2)

        self.logger.debug(f"auto_update_stop result: {result}")
        if result is not None:
            self.logger.warning("auto update stop command is not completed")
        else:
            self.auto_update = False
        return result

    def getpos(self) -> int | None:
        self.logger.info("call getpos cmd")
        self.__ensure_port_open()
        self.conn.write(MGMSG_MOT_REQ_USTATUSUPDATE)
        result = self.__wait_for_reply(b"\x91\x04", self.move_timeout)
        self.logger.debug(f"getpos all byte sequence results: {result}")

        if result is None:
            self.logger.error("getpos command is not completed")
            raise OdlGetPosNotCompleted(
                f"ODL{self}: No update response has been received for determining the position"
            )

        pos_seq = result[8:12]
        self.logger.debug(f"getpos byte result: {pos_seq}")

        steps = int.from_bytes(pos_seq, byteorder="little")
        position = steps / self.resolution
        self.logger.info(f"getpos extracted result: pos:{position} steps:{steps}")
        self.currrent_steps = steps
        return steps

    def home(self) -> bytes | None:
        self.__ensure_port_open()

        self.conn.write(ODL_HOME_COMMAND)
        time.sleep(0.5)

        homed = self.__wait_for_reply(b"\x44\x04", self.home_timeout)
        self.logger.debug(f"home result: {homed}")
        if homed is None:
            self.logger.error("home command is not completed in ODL")
            raise OdlHomeNotCompleted(f"Odl{self}: Homed response can not be received")
        self.currrent_steps = ODL_HOMED_POSITION
        return homed
