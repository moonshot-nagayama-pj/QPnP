#
# Thorlanbs ODL module driver
#       Brushless Motor Driver: KBD101
#       Stage:                  DDS100/M
#       Stub mode:              True
#
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

class OdlThorlabs(OpticalDelayLine):
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

    def __init__(self):
        # Stub Serial Number
        # TODO: Custom serial number from initalizer
        self.device_sn = "stubodl_thorlabs"
        self.name = "Thorlabs"
        self.model = "KBD101 driver DDS100/M Stage"

        self.home_timeout = 25
        self.move_timeout = 4
        self.resolution = 2000
        self.auto_update = False
        self.max_move = 100
        self.min_move = 0
        self.logger = logging.getLogger(f"{self}")

        # Stub device parameters
        self.current_position = 0

        # Is connected to the device
        self.connected = False

        # Enabled channels (enable 1 by default)
        self.enabled_channels = [1]

    def __ensure_port_open(self) -> None:
        if not self.connected:
            self.logger.warning("Device not connected")
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

    def connect(self):
        self.connected = True
        self.logger.info("Stub Odl_Thorlabs Connected")

    def identify(self):
        self.__ensure_port_open()
        # TODO: For Stub device, no need to implement. logger.info("Identify command is called")
        self.logger.info("Stub Odl_Thorlabs Identify")

    def __wait_for_reply(self, sequence: bytes | None, timeout: int):
        # TODO: For Stub device, no need to implement. logger.info("Wait for reply command is called")
        result = "Stub ODL Thorlabs Response"
        self.logger.info(f"The response found: {result} ")
        time.sleep(1)
        return result

    def move(self, move_mm: int):
        move_steps = move_mm * self.resolution
        self.logger.debug(
            f"move command recieved: move_mm:({move_mm})->move_steps:({move_steps})"
        )
        self.__ensure_port_open()
        self.__ensure_steps_in_range(move_steps)

        # TODO: For Stub device, no need to implement. logger.info("Move command is called")
        self.__wait_for_reply(b"\x64\04", self.move_timeout)
        self.currrent_steps = move_steps
        self.logger.debug(f"Move completed position_steps({self.currrent_steps})!")

    def step_forward(self, steps):
        self.__ensure_port_open()
        self.__ensure_steps_in_range(steps)
        self.__ensure_final_in_range(self.currrent_steps, steps)

        # TODO: For Stub device, no need to implement. logger.info("Step forward command is called")
        # relative move
        self.__wait_for_reply(b"\x64\x04", self.move_timeout)
        self.currrent_steps += steps
        self.logger.debug(f"Step forward completed position_steps({self.currrent_steps})!")

    def __ensure_final_in_range(self, current_position, steps: int):

        max_threshold = self.max_move * self.resolution
        min_threshold = self.min_move * self.resolution

        next_position = current_position + steps
        if min_threshold <= next_position <= max_threshold:
            return
        raise OdlMoveOutofRangeError(
            f"The relative change position request for device{self} is out of range min({self.min_move}) - max({self.max_move})"
        )

    def step_backward(self, steps):
        self.__ensure_port_open()
        self.__ensure_steps_in_range(steps)

        # negate steps
        steps = -steps
        self.__ensure_final_in_range(self.currrent_steps, steps)

        # TODO: For Stub device, no need to implement. logger.info("Step backward command is called")
        # relative move
        self.__wait_for_reply(b"\x64\x04", self.move_timeout)
        self.currrent_steps += steps
        self.logger.debug(f"Step backward completed position_steps({self.currrent_steps})!")

    def auto_update_start(self):
        self.logger.info("call auto update start cmd")
        self.__ensure_port_open()
        # Stub auto update start(NOT IMPLEMENTED)
        result = self.__wait_for_reply(b"\x91\x04", self.move_timeout)

        self.logger.debug(f"auto_update_start result: {result}")
        if result is None:
            self.logger.warning("auto update start command is not completed")
        else:
            self.auto_update = True
        return result

    def auto_update_stop(self):
        self.logger.info("cal auto update stop cmd")
        self.__ensure_port_open()
        # Stub auto update stop(NOT IMPLEMENTED)
        result = self.__wait_for_reply(b"\x91\x04", 2)

        self.logger.debug(f"auto_update_stop result: {result}")
        if result is not None:
            self.logger.warning("auto update stop command is not completed")
        else:
            self.auto_update = False
        return result

    def getpos(self):
        self.logger.info("call getpos cmd")
        self.__ensure_port_open()
        # TODO: For Stub device, no need to implement. logger.info("Getpos command is called")
        self.__wait_for_reply(b"\x91\x04", self.move_timeout)
        result = bytes(self.current_position)
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

    def home(self):
        self.__ensure_port_open()
        time.sleep(0.5)

        homed = self.__wait_for_reply(b"\x44\x04", self.home_timeout)
        self.logger.debug(f"home result: {homed}")
        if homed is None:
            self.logger.error("home command is not completed in ODL")
            raise OdlHomeNotCompleted(f"Odl{self}: Homed response can not be received")
        self.currrent_steps = ODL_HOMED_POSITION
        return homed


if __name__ == "__main__":
    dev = OdlThorlabs()
    print("Stub Mode Under Test")
