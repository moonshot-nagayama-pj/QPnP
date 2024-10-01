import enum

from enum import auto, StrEnum


@enum.unique
class Event(StrEnum):
    RX_MESSAGE_KNOWN = auto()
    RX_MESSAGE_UNKNOWN = auto()
    TX_MESSAGE_ORDERED = auto()
    TX_MESSAGE_UNORDERED = auto()
    UNCAUGHT_EXCEPTION = auto()
