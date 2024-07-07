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

class Waveplate:
    """Stub Waveplate Device Class"""
    resolution: int
    max_steps: int
    relative_home: float

    def __init__(self):
        # Stub Serial Number
        # TODO: Custom serial number from initializer
        self.device_sn = "stubwaveplate"

        self.resolution = 136533
        self.max_steps = 136533
        self.rotate_timeout = 10
        self.home_timeout = 20
        self.max_channel = 1
        self.auto_update = False

        self.logger = logging.getLogger(f"{self}")

        # Stub device parameters
        self.current_position = 0

        # Is connected to the device
        self.connected = False

        # Enabled channels (enable 1 by default)
        self.enabled_channels = [1]

    def __ensure_port_open(self) -> None:
        if not self.connected:
            self.logger.error("Device not connected")
            raise DeviceDisconnectedError(f"{self} is disconnected")

    def __ensure_less_than_max_steps(self, steps: int) -> None:
        if steps > self.max_steps:
            raise WaveplateInvalidStepsError(f"Given steps: {steps} exceeds the maximum steps: {self.max_steps}")

    def __ensure_valid_degree(self, degree: float) -> None:
        if 0 <= degree <= 360:
            return
        raise WaveplateInvalidDegreeError(f"Invalid degree: {degree}. Degree must be in a range [0,360]")

    # Maybe make this into a function wrapper to remove some redundant code?
    def __stub_check_channel(self, chanid: int):
        return chanid in self.enabled_channels

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
        """Perform homing operation on the device"""
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

        if chanid >= self.max_channel:
            raise WaveplateInvalidMotorChannelError(f"Channel {chanid} is not enabled")

        # Remove channel from enabled channels
        self.enabled_channels.remove(chanid)

        # Simulated delay
        time.sleep(0.1)

    def enable_channel(self, chanid: int) -> None:
        """Enable a channel on the device specified by chanid"""
        self.__ensure_port_open()
        self.logger.info("Stub Waveplate Enable Channel: %s", chanid)
        if chanid > self.max_channel:
            raise WaveplateInvalidMotorChannelError(f"Invalid motor channel: {chanid}. Max channel: {self.max_channel}")

        self.enabled_channels.append(chanid)

        # Simulated delay
        time.sleep(0.1)

        # TODO: Return a fake reply from the device

    def device_resolution(self) -> int:
        """Get the device resolution"""
        return self.resolution

    def getpos(self) -> int | float:
        """Get the current position of the device"""
        self.__ensure_port_open()
        self.logger.info("Stub Waveplate Get Position")
        self.logger.info("Current Position: Steps: %s Degrees: %s", self.current_position, self.current_position / self.resolution)
        return self.current_position

    def rotate(self, degree: int | float) -> None:
        """Rotate the device to a specified degree"""
        self.__ensure_port_open()
        self.__ensure_valid_degree(degree)

        if not self.__stub_check_channel(1):
            # Do nothing if channel is not enabled
            return

        self.logger.info("Stub Waveplate Rotate to %s", degree)
        # Calculate number of steps to move
        move_position = degree * self.resolution
        # Update current position
        self.current_position = move_position
        # Delay to simulate rotation (for now: v=1ms/deg)
        time.sleep(abs(move_position - self.current_position) / 1000)
        # TODO: Return a fake reply from the device

    def step_backward(self, steps: int) -> None:
        """Step backward by a specified number of steps"""
        # Convert steps to degrees
        new_steps = self.current_position - steps
        degrees = new_steps / self.resolution
        self.rotate(-degrees)

    def step_forward(self, steps: int) -> None:
        """Step forward by a specified number of steps"""
        # Convert steps to degrees
        new_steps = self.current_position + steps
        degrees = new_steps / self.resolution
        self.rotate(degrees)

    def rotate_relative(self, degree: int | float) -> None:
        """Rotate the device by a specified degree relative to the current position"""
        # Get new rotation degree
        current_degree = self.current_position / self.resolution
        new_degree = current_degree + degree
        self.rotate(new_degree)

    def custom_home(self, degree) -> None:
        """Set custom home position for the device"""
        self.__ensure_port_open()
        self.__ensure_valid_degree(degree)

        self.logger.info("Stub Waveplate Custom Home %s", degree)

        if not self.__stub_check_channel(1):
            # Do nothing if channel is not enabled
            return

        self.home()
        self.relative_home = degree
        self.rotate(degree)

    def custom_rotate(self, degree) -> None:
        """Rotate the device to a specified degree relative to the custom home position"""
        self.__ensure_port_open()
        self.__ensure_valid_degree(degree)

        self.logger.info("Stub Waveplate Custom Rotate %s", degree)

        if not self.relative_home:
            # Do nothing if relative home is not set
            return

        if not self.relative_home:
            self.logger.error("Custom Home not set")
            raise WavePlateCustomRotateError("Waveplate({self}) relative_home not set")

        if not self.__stub_check_channel(1):
            # Do nothing if channel is not enabled
            return

        self.rotate(degree + self.relative_home)

    def __repr__(self) -> str:
        return f"Waveplate(Stub {self.device_sn})"
