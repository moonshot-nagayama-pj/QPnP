# ODL STUB
import time, logging
from pnpq.devices.optical_delay_line import OpticalDelayLine

from pnpq.errors import (
    DeviceDisconnectedError,
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
        # Basic parameters
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
        if not self.connected:
            self.logger.error("Device not connected")
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

    def __ensure_final_in_range(self, current_position: int, steps: int) -> None:

        max_threshold = self.max_move * self.resolution
        min_threshold = self.min_move * self.resolution

        next_position = current_position + steps
        if min_threshold <= next_position <= max_threshold:
            return
        raise OdlMoveOutofRangeError(
            f"The relative change position request for device{self} is out of range min({self.min_move}) - max({self.max_move})"
        )

    def move(self, move_mm: int) -> None:
        move_steps = move_mm * self.resolution
        self.logger.debug(
            f"move command recieved: move_mm:({move_mm})->move_steps:({move_steps})"
        )
        self.__ensure_port_open()
        self.__ensure_steps_in_range(move_steps)
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
