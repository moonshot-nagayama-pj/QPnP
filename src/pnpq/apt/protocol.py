import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, StrEnum
from struct import Struct
from typing import ClassVar, Self


@enum.unique
class AptMessageId(int, Enum):
    MGMSG_HW_DISCONNECT = 0x0002
    MGMSG_HW_GET_INFO = 0x0006
    MGMSG_HW_REQ_INFO = 0x0005
    MGMSG_HW_START_UPDATEMSGS = 0x0011
    MGMSG_HW_STOP_UPDATEMSGS = 0x0012

    MGMSG_MOD_GET_CHANENABLESTATE = 0x0212
    MGMSG_MOD_REQ_CHANENABLESTATE = 0x0211
    MGMSG_MOD_SET_CHANENABLESTATE = 0x0210

    MGMSG_MOD_IDENTIFY = 0x0223

    MGMSG_MOT_GET_DCSTATUSUPDATE = 0x0491
    MGMSG_MOT_GET_POSCOUNTER = 0x0412
    MGMSG_MOT_MOVE_ABSOLUTE = 0x0453
    MGMSG_MOT_MOVE_COMPLETED = 0x0464
    MGMSG_MOT_MOVE_HOME = 0x0443
    MGMSG_MOT_MOVE_HOMED = 0x0444
    MGMSG_MOT_MOVE_JOG = 0x046A
    MGMSG_MOT_MOVE_STOP = 0x0465
    MGMSG_MOT_MOVE_STOPPED = 0x0466
    MGMSG_MOT_REQ_DCSTATUSUPDATE = 0x0490
    MGMSG_MOT_REQ_POSCOUNTER = 0x0411
    MGMSG_MOT_SET_EEPROMPARAMS = 0x04B9
    MGMSG_MOT_SET_POSCOUNTER = 0x0410
    MGMSG_POL_GET_PARAMS = 0x0532
    MGMSG_POL_REQ_PARAMS = 0x0531
    MGMSG_POL_SET_PARAMS = 0x0530
    MGMSG_RESTOREFACTORYSETTINGS = 0x0686


@enum.unique
class Address(int, Enum):
    BAY_0 = 0x21
    BAY_1 = 0x22
    BAY_2 = 0x23
    BAY_3 = 0x24
    BAY_4 = 0x25
    BAY_5 = 0x26
    BAY_6 = 0x27
    BAY_7 = 0x28
    BAY_8 = 0x29
    BAY_9 = 0x2A
    GENERIC_USB = 0x50
    HOST_CONTROLLER = 0x01
    RACK_CONTROLLER = 0x11


@enum.unique
class HardwareType(int, Enum):
    """Used in MGMSG_HW_GET_INFO"""

    BRUSHLESS_DC_CONTROLLER = 44
    MULTI_CHANNEL_CONTROLLER_MOTHERBOARD = 45


@dataclass(frozen=True, kw_only=True)
class FirmwareVersion:
    """Used in MGMSG_HW_GET_INFO.

    Judging by the order in the documentation, "interim revision" comes betwen major and minor.

    On the other hand, judging by the example in the documentation,
    this is intended to be read as a 3-byte unsigned integer. It's
    unclear which representation is correct.
    """

    major_revision: int
    interim_revision: int
    minor_revision: int
    unused: int = 0


@enum.unique
class ChanIdent(int, Enum):
    """Used in CHANENABLESTATE commands."""

    CHANNEL_1 = 0x01
    CHANNEL_2 = 0x02
    CHANNEL_3 = 0x04
    CHANNEL_4 = 0x08


@enum.unique
class EnableState(int, Enum):
    """Used in CHANENABLESTATE commands."""

    CHANNEL_ENABLED = 0x01
    CHANNEL_DISABLED = 0x02


@enum.unique
class ATS(StrEnum):
    """ATS = Apt To Struct

    Map Python struct format strings to the names used by the APT
    documentation. Unfortunately, those names are not used
    consistently.
    """

    WORD = "H"  # Unsigned 16-bit integer
    SHORT = "h"  # Signed twos-complement 16-bit integer
    DWORD = "I"  # Unsigned 32-bit integer
    LONG = "i"  # Signed twos-complement 32-bit integer
    CHAR = "c"  # One byte that should be represented using the bytes() type
    CHAR_N = "s"  # Many bytes that should be represented using the bytes() type
    BYTE = "b"  # Signed twos-complement 8-bit integer
    U_BYTE = "B"  # Unsigned 8-bit integer


# Abstract and partial parent classes for building concrete message
# classes


@dataclass(frozen=True, kw_only=True)
class AptMessage(ABC):
    destination: Address
    source: Address

    message_id: ClassVar[AptMessageId]

    @property
    @abstractmethod
    def destination_serialization(self) -> int:
        pass

    @classmethod
    @abstractmethod
    def from_bytes(cls, raw: bytes) -> Self:
        pass

    @abstractmethod
    def to_bytes(self) -> bytes:
        pass


@dataclass(frozen=True, kw_only=True)
class AptMessageHeaderOnly(AptMessage):
    @property
    def destination_serialization(self) -> int:
        return self.destination


@dataclass(frozen=True, kw_only=True)
class AptMessageHeaderOnlyNoParams(AptMessageHeaderOnly):
    message_struct: ClassVar[Struct] = Struct(f"<{ATS.WORD}2{ATS.CHAR}2{ATS.U_BYTE}")
    param1: bytes = bytes(1)
    param2: bytes = bytes(1)

    @classmethod
    def from_bytes(cls, raw: bytes) -> Self:
        message_id, param1, param2, destination, source = cls.message_struct.unpack(raw)
        if message_id != cls.message_id:
            raise ValueError(
                f"Expected message ID {cls.message_id.value}, but received {message_id} instead. Full raw message was {raw!r}"
            )
        return cls(
            param1=param1,
            param2=param2,
            destination=Address(destination),
            source=Address(source),
        )

    def to_bytes(self) -> bytes:
        return self.message_struct.pack(
            self.message_id,
            self.param1,
            self.param2,
            self.destination_serialization,
            self.source,
        )


@dataclass(frozen=True, kw_only=True)
class AptMessageWithData(AptMessage):
    header_struct_str: ClassVar[str] = f"<{ATS.WORD}{ATS.WORD}2{ATS.U_BYTE}"

    @property
    def destination_serialization(self) -> int:
        return self.destination | 0x80


@dataclass(frozen=True, kw_only=True)
class AptMessageHeaderOnlyChanEnableState(AptMessageHeaderOnly):
    message_struct: ClassVar[Struct] = Struct(f"<{ATS.WORD}2{ATS.U_BYTE}2{ATS.U_BYTE}")

    chan_ident: ChanIdent
    enable_state: EnableState

    @classmethod
    def from_bytes(cls, raw: bytes) -> Self:
        message_id, chan_ident, enable_state, destination, source = (
            cls.message_struct.unpack(raw)
        )
        if message_id != cls.message_id:
            raise ValueError(
                f"Expected message ID {cls.message_id.value}, but received {message_id} instead. Full raw message was {raw!r}"
            )
        return cls(
            chan_ident=ChanIdent(chan_ident),
            destination=Address(destination),
            enable_state=EnableState(enable_state),
            source=Address(source),
        )

    def to_bytes(self) -> bytes:
        return self.message_struct.pack(
            self.message_id,
            self.chan_ident,
            self.enable_state,
            self.destination_serialization,
            self.source,
        )


# Concrete message implementation classes


@dataclass(frozen=True, kw_only=True)
class AptMessage_MGMSG_HW_DISCONNECT(AptMessageHeaderOnlyNoParams):
    message_id = AptMessageId.MGMSG_HW_DISCONNECT


@dataclass(frozen=True, kw_only=True)
class AptMessage_MGMSG_HW_GET_INFO(AptMessageWithData):
    data_length: ClassVar[int] = 84
    message_id: ClassVar[AptMessageId] = AptMessageId.MGMSG_HW_GET_INFO
    message_struct: ClassVar[Struct] = Struct(
        f"{AptMessageWithData.header_struct_str}{ATS.LONG}8{ATS.CHAR_N}{ATS.WORD}4{ATS.U_BYTE}60{ATS.CHAR_N}3{ATS.WORD}"
    )

    firmware_version: FirmwareVersion
    hardware_type: HardwareType  # Labeled "type" in the documentation
    hardware_version: int
    internal_use: bytes
    model_number: str
    modification_state: int
    number_of_channels: int  # Labeled "nchs" in the documentation
    serial_number: int

    @classmethod
    def from_bytes(cls, raw: bytes) -> "AptMessage_MGMSG_HW_GET_INFO":
        (
            message_id,
            data_length,
            destination,
            source,
            serial_number,
            model_number,
            hardware_type,
            minor_revision,
            interim_revision,
            major_revision,
            unused_revision,
            internal_use,
            hardware_version,
            modification_state,
            number_of_channels,
        ) = cls.message_struct.unpack(raw)

        if message_id != cls.message_id:
            raise ValueError(
                f"Expected message ID {cls.message_id.value}, but received {message_id} instead. Full raw data was {raw!r}"
            )
        if data_length != cls.data_length:
            raise ValueError(
                f"Expected data packet length {cls.data_length}, but received {data_length} instead. Full raw data was {raw!r}"
            )
        if destination & 0x80 != 0x80:
            raise ValueError(
                f"Expected the destination's highest bit to be 1, indicating that a data packet follows, but it was 0. Full raw data was {raw!r}"
            )

        return AptMessage_MGMSG_HW_GET_INFO(
            destination=Address(destination & 0x7F),
            firmware_version=FirmwareVersion(
                interim_revision=interim_revision,
                major_revision=major_revision,
                minor_revision=minor_revision,
                unused=unused_revision,
            ),
            hardware_type=HardwareType(hardware_type),
            hardware_version=hardware_version,
            internal_use=internal_use,
            model_number=model_number.decode("latin_1").rstrip("\x00"),
            modification_state=modification_state,
            number_of_channels=number_of_channels,
            serial_number=serial_number,
            source=Address(source),
        )

    def to_bytes(self) -> bytes:
        return self.message_struct.pack(
            self.message_id,
            self.data_length,
            self.destination_serialization,
            self.source,
            self.serial_number,
            self.model_number.encode("latin_1"),
            self.hardware_type,
            self.firmware_version.minor_revision,
            self.firmware_version.interim_revision,
            self.firmware_version.major_revision,
            self.firmware_version.unused,
            self.internal_use,
            self.hardware_version,
            self.modification_state,
            self.number_of_channels,
        )


@dataclass(frozen=True, kw_only=True)
class AptMessage_MGMSG_HW_REQ_INFO(AptMessageHeaderOnlyNoParams):
    message_id = AptMessageId.MGMSG_HW_REQ_INFO


@dataclass(frozen=True, kw_only=True)
class AptMessage_MGMSG_HW_START_UPDATEMSGS(AptMessageHeaderOnlyNoParams):
    message_id = AptMessageId.MGMSG_HW_START_UPDATEMSGS


@dataclass(frozen=True, kw_only=True)
class AptMessage_MGMSG_HW_STOP_UPDATEMSGS(AptMessageHeaderOnlyNoParams):
    message_id = AptMessageId.MGMSG_HW_STOP_UPDATEMSGS


@dataclass(frozen=True, kw_only=True)
class AptMessage_MGMSG_MOD_GET_CHANENABLESTATE(AptMessageHeaderOnlyChanEnableState):
    message_id = AptMessageId.MGMSG_MOD_GET_CHANENABLESTATE


@dataclass(frozen=True, kw_only=True)
class AptMessage_MGMSG_MOD_REQ_CHANENABLESTATE(AptMessageHeaderOnly):
    message_struct: ClassVar[Struct] = Struct(
        f"<{ATS.WORD}{ATS.U_BYTE}{ATS.CHAR}2{ATS.U_BYTE}"
    )

    message_id = AptMessageId.MGMSG_MOD_REQ_CHANENABLESTATE
    chan_ident: ChanIdent
    param2: bytes = bytes(1)

    @classmethod
    def from_bytes(cls, raw: bytes) -> Self:
        message_id, chan_ident, param2, destination, source = cls.message_struct.unpack(
            raw
        )
        if message_id != cls.message_id:
            raise ValueError(
                f"Expected message ID {cls.message_id.value}, but received {message_id} instead. Full raw message was {raw!r}"
            )
        return cls(
            chan_ident=ChanIdent(chan_ident),
            destination=Address(destination),
            param2=param2,
            source=Address(source),
        )

    def to_bytes(self) -> bytes:
        return self.message_struct.pack(
            self.message_id,
            self.chan_ident,
            self.param2,
            self.destination_serialization,
            self.source,
        )


@dataclass(frozen=True, kw_only=True)
class AptMessage_MGMSG_MOD_SET_CHANENABLESTATE(AptMessageHeaderOnlyChanEnableState):
    message_id = AptMessageId.MGMSG_MOD_SET_CHANENABLESTATE
