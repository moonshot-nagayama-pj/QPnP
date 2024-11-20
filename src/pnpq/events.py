import enum
from enum import StrEnum, auto


@enum.unique
class Event(StrEnum):
    RX_MESSAGE_KNOWN = auto()
    RX_MESSAGE_UNKNOWN = auto()
    TX_MESSAGE_ORDERED = auto()
    TX_MESSAGE_UNORDERED = auto()
    UNCAUGHT_EXCEPTION = auto()

    # Common events used by most device types
    DEVICE_CONNECTED = auto()
    DEVICE_NOT_CONNECTED = auto()
    DEVICE_IDENTIFY = auto()

    # Optical Switch Events
    SWITCH_BAR_STATE = auto()
    SWITCH_CROSS_STATE = auto()

    # Waveplate Events
    WAVEPLATE_HOME = auto()
    WAVEPLATE_ROTATE = auto()
