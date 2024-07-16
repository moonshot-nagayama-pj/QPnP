import logging
import time

from pnpq.errors import (
    DevicePortNotFoundError,
    DeviceDisconnectedError,
    WavePlateMoveNotCompleted,
    WavePlateHomedNotCompleted,
    WavePlateGetPosNotCompleted,
    WavePlateCustomRotateError,
    WaveplateInvalidStepsError,
    WaveplateInvalidDegreeError,
    WaveplateEnableChannelError,
    WaveplateInvalidMotorChannelError,
)

class WaveplateStub:
    """Stub Waveplate Device Class"""

    def __init__(self):
        # Stub Serial Number
        # TODO: Custom serial number from initializer
        self.device_sn: str = "stubwaveplate"

        # Resolution of the device in steps per degree
        self.resolution: int = 136533
        # Maximum steps the device can move (360 degrees)
        self.max_steps: int = 136533*360
        # Maximum channel the device can control
        self.max_channel: int = 1
        # Flag for auto updating device information
        self.auto_update: bool = False

        # Logger for this class
        self.logger: logging.Logger = logging.getLogger(f"{self}")

        # Current Position of the device in steps
        self.current_position: int = 0

        # Is connected to the device (used internally)
        self.connected: bool = False

        # Enabled channels (enable 1 by default, used internally)
        self.enabled_channels: set = {1}

    def __ensure_port_open(self) -> None:
        if not self.connected:
            self.logger.error("Device not connected")
            raise DeviceDisconnectedError(f"{self} is disconnected")

    def __ensure_valid_steps(self, steps: int) -> None:
        if 0 <= steps <= self.max_steps:
            return
        raise WaveplateInvalidStepsError(f"Invalid steps: {steps}. Steps must be in a range [0,{self.max_steps}]")

    def __ensure_valid_degree(self, degree: float) -> None:
        if 0 <= degree <= 360:
            return
        raise WaveplateInvalidDegreeError(f"Invalid degree: {degree}. Degree must be in a range [0,360]")

    def __stub_check_channel(self, chanid: int):
        return chanid in self.enabled_channels

    def __set_steps(self, steps: int) -> None:
        self.__ensure_valid_steps(steps)
        self.current_position = steps

    def connect(self) -> None:
        """Establish connection to the device"""
        self.connected = True
        self.logger.info("Stub Waveplate Connected")

    def identify(self) -> None:
        """Identify the device by flashing the on-device LED"""
        self.__ensure_port_open()
        # Flashes LED on real device, for stub, we will do nothing
        self.logger.info("Stub Waveplate Identify")

    def home(self) -> None:
        """Return the device to home: absolute position 0"""
        self.__ensure_port_open()
        self.logger.info("Stub Waveplate Home")

        if not self.__stub_check_channel(1):
            # Do nothing if channel is not enabled
            return

        self.current_position = 0
        # Simulated delay for homing
        # TODO: Delay calculation
        time.sleep(1)
        self.logger.info("Home position: %s", self.current_position)

    def auto_update_start(self) -> None:
        """Start automatically logging device information"""
        self.__ensure_port_open()
        self.logger.info("Stub Waveplate Auto Update Start")
        # TODO: Auto updating logging

    def auto_update_stop(self) -> None:
        """Stop automatically logging device information"""
        self.__ensure_port_open()
        self.logger.info("Stub Waveplate Auto Update Stop")
        # TODO: Auto updating logging

    def disable_channel(self, chanid: int) -> None:
        """Disable a channel on the device specified by chanid"""
        self.__ensure_port_open()
        self.logger.info("Stub Waveplate Disable Channel: %s", chanid)

        if chanid > self.max_channel:
            raise WaveplateInvalidMotorChannelError(f"Invalid motor channel: {chanid}.")

        # Remove channel from enabled channels
        self.enabled_channels.remove(chanid)

        # Simulated delay
        time.sleep(0.1)

    def enable_channel(self, chanid: int) -> None:
        """Enable a channel on the device specified by chanid"""
        self.__ensure_port_open()
        self.logger.info("Stub Waveplate Enable Channel: %s", chanid)
        if chanid > self.max_channel:
            raise WaveplateInvalidMotorChannelError(f"Invalid motor channel: {chanid}.")

        self.enabled_channels.add(chanid)

        # Simulated delay
        time.sleep(0.1)

        # TODO: Return a fake reply from the device

    def device_resolution(self) -> int:
        """Get the device resolution"""
        return self.resolution

    def getpos(self) -> int:
        """Get the current position of the device in steps"""
        self.__ensure_port_open()
        self.logger.info("Stub Waveplate Get Position")
        self.logger.info("Current Position: Steps: %s Degrees: %s", self.current_position, self.current_position / self.resolution)
        return self.current_position

    def get_degree(self) -> float:
        """Get the current position of the device in degrees"""
        self.__ensure_port_open()
        self.logger.info("Stub Waveplate Get Degree")
        return self.current_position / self.resolution

    def rotate(self, degree: int | float) -> None:
        """Rotate the device to a specified absolute degree"""
        self.__ensure_port_open()
        self.__ensure_valid_degree(degree)

        if not self.__stub_check_channel(1):
            # Do nothing if channel is not enabled
            return

        self.logger.info("Stub Waveplate Rotate to %s", degree)
        # Calculate number of steps to move (truncate to nearest integer)
        move_position = int(degree * self.resolution)
        # Update current position
        self.__set_steps(move_position)
        # Delay to simulate rotation (for now: v=1ms/deg)
        time.sleep(abs(move_position - self.current_position) / 1000)
        # TODO: Return a fake reply from the device

    def step_backward(self, steps: int) -> None:
        """Step backward by a specified number of steps"""
        self.__ensure_port_open()

        # Get new position and set steps
        new_steps = self.current_position - steps
        self.__set_steps(new_steps)

    def step_forward(self, steps: int) -> None:
        """Step forward by a specified number of steps"""
        self.__ensure_port_open()

        # Get new position and set steps
        new_steps = self.current_position + steps
        self.__set_steps(new_steps)

    def rotate_relative(self, degree: int | float) -> None:
        """Rotate the device by a specified degree relative to the current position"""
        # Get new rotation degree
        current_degree = self.get_degree()
        new_degree = current_degree + degree
        self.rotate(new_degree)

    def custom_home(self, degree: int | float) -> None:
        """Set custom home position in degrees for the device and rotate to that position"""
        self.__ensure_port_open()
        self.__ensure_valid_degree(degree)

        self.logger.info("Stub Waveplate Custom Home %s", degree)

        if not self.__stub_check_channel(1):
            # Do nothing if channel is not enabled
            return

        self.home()
        self.relative_home = degree
        self.rotate(degree)

    def custom_rotate(self, degree: int | float) -> None:
        """Rotate the device to a specified degree relative to the custom home position"""
        self.__ensure_port_open()

        self.logger.info("Stub Waveplate Custom Rotate %s", degree)

        if not self.relative_home:
            self.logger.error("Custom Home not set")
            raise WavePlateCustomRotateError("Waveplate({self}) relative_home not set")

        if not self.__stub_check_channel(1):
            # Do nothing if channel is not enabled
            return

        # TODO: Support overflow rotation
        # 1. Accept a relative degree between 0 and 360
        # 2. Calculate what absolute degree this corresponds to, e.g., if degree + self.relative_home > 360, then overflow back to 0.
        self.rotate(degree + self.relative_home)

    def __repr__(self) -> str:
        return f"Waveplate(Stub {self.device_sn})"
