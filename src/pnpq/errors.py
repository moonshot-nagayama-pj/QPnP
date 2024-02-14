class DeviceDisconnectedError(Exception):
    """Exception raised for the device is disconnected"""

    pass


class DevicePortNotFoundError(Exception):
    """Rasied when a port not found"""

    pass


class WaveplateInvalidStepsError(Exception):
    """Raised when a specified step value is more than the device's maximum steps"""

    pass


class WaveplateInvalidDegreeError(Exception):
    """Raised when an invalid degree specified. degree must be in a range 0-360"""

    pass


class WavePlateInvalidMotorChannelError(Exception):
    """Raised when trying to access an invalid motor channel number. check max_channel"""

    pass
