class DeviceDisconnectedError(Exception):
    """Exception raised for the device is disconnected"""


class DevicePortNotFoundError(Exception):
    """Rasied when a port not found"""


class WaveplateInvalidStepsError(Exception):
    """Raised when a specified step value is more than the device's maximum steps"""


class WavePlateHomedNotCompleted(Exception):
    """Raised when a Homed response has not been received from WavePlate Rotator device"""


class WavePlateCustomRotateError(Exception):
    """Raised when custom rotation failed"""


class WavePlateMoveNotCompleted(Exception):
    """Raised when Moved Complete response has not been receieved from WavePlate Rotator device"""


class WavePlateGetPosNotCompleted(Exception):
    """Raised when GetPos response has not been received from Waveplate Rotator Device"""


class WaveplateEnableChannelError(Exception):
    """Raised when no response has been received from Enable Channel Command"""


class WaveplateInvalidDegreeError(Exception):
    """Raised when an invalid degree specified. degree must be in a range 0-360"""


class WaveplateInvalidMotorChannelError(Exception):
    """Raised when trying to access an invalid motor channel number. check max_channel"""


class OdlMoveNotCompleted(Exception):
    """Raised when Move complete response has not been received from ODL device"""


class OdlHomeNotCompleted(Exception):
    """Raised when Homed response has not been received from ODL device"""


class OdlMoveOutofRangeError(Exception):
    """Raised when the requesed move is our of range of the odl device"""


class OdlGetPosNotCompleted(Exception):
    """Raised when no response has been received for GetPos command"""


class InvalidStateException(Exception):
    """Thrown when a method is called on an object, but the object is
    not in an appropriate state for that function to be called.

    For example, if an object processes streams of data, and those
    streams have already been closed, it should not be possible to
    re-open them.

    """
