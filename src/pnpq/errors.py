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
    """Raised when a invalid degree specified. degree must be in a range 0-360"""

    pass
