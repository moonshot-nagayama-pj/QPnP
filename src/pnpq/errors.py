class DeviceDisconnectedError(Exception):
    """Exception raised for the device is disconnected"""

    pass


class DevicePortNotFoundError(Exception):
    """Rasied when a port not found"""

    pass


class WaveplateInvalidStepsError(Exception):
    """Raised when a specified step value is more than the device's maximum steps"""

    pass


class WavePlateHomedNotCompleted(Exception):
    """Raised when a Homed response has not been received from WavePlate Rotator device"""

    pass


class WavePlateCustomRotateError(Exception):
    """Raised when custom rotation failed"""

    pass


class WavePlateMoveNotCompleted(Exception):
    """Raised when Moved Complete response has not been receieved from WavePlate Rotator device"""

    pass


class WavePlateGetPosNotCompleted(Exception):
    """Raised when GetPos response has not been received from Waveplate Rotator Device"""

    pass


class WaveplateEnableChannelError(Exception):
    """Raised when no response has been received from Enable Channel Command"""

    pass


class WaveplateInvalidDegreeError(Exception):
    """Raised when an invalid degree specified. degree must be in a range 0-360"""

    pass


class WaveplateInvalidMotorChannelError(Exception):
    """Raised when trying to access an invalid motor channel number. check max_channel"""

    pass


class OdlMoveNotComepleted(Exception):
    """Raised when Move complete response has not been received from ODL device"""

    pass


class OdlHomeNotCompleted(Exception):
    """Raised when Homed response has not been received from ODL device"""

    pass


class OdlMoveOutofRangeError(Exception):
    """Raised when the requesed move is our of range of the odl device"""

    pass


class OdlGetPosNotCompleted(Exception):
    """Raised when no response has been received for GetPos command"""

    pass
