# pylint: disable=C0103

import dataclasses
import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import STRICT, Enum, IntFlag, StrEnum
from struct import Struct
from typing import ClassVar, Self

from pint import Quantity

from ..units import ureg


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

    MGMSG_MOT_ACK_USTATUSUPDATE = 0x0492
    MGMSG_MOT_GET_USTATUSUPDATE = 0x0491
    MGMSG_MOT_REQ_USTATUSUPDATE = 0x0490

    MGMSG_MOT_MOVE_ABSOLUTE = 0x0453
    MGMSG_MOT_MOVE_COMPLETED = 0x0464
    MGMSG_MOT_MOVE_HOME = 0x0443
    MGMSG_MOT_MOVE_HOMED = 0x0444
    MGMSG_MOT_RESUME_ENDOFMOVEMSGS = 0x046C

    MGMSG_POL_GET_PARAMS = 0x0532
    MGMSG_POL_REQ_PARAMS = 0x0531
    MGMSG_POL_SET_PARAMS = 0x0530

    MGMSG_RESTOREFACTORYSETTINGS = 0x0686


@enum.unique
class UnimplementedAptMessageId(int, Enum):
    """Space to temporarily store message IDs that we know we need for
    our devices but have not yet implemented.
    """

    # TODO (see docstring)
    MGMSG_MOT_GET_POSCOUNTER = 0x0412
    MGMSG_MOT_REQ_POSCOUNTER = 0x0411
    MGMSG_MOT_SET_POSCOUNTER = 0x0410

    MGMSG_MOT_MOVE_JOG = 0x046A
    MGMSG_MOT_MOVE_STOP = 0x0465
    MGMSG_MOT_MOVE_STOPPED = 0x0466

    MGMSG_MOT_SET_EEPROMPARAMS = 0x04B9


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
class HardwareType(IntFlag):
    # pylint: disable=W0213
    """Used in MGMSG_HW_GET_INFO. This is marked as a Flag because we
    expect to receive unknown values. It is not actually a
    bit-mappable flag."""

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
class ChanIdent(IntFlag, boundary=STRICT):
    """Used in IDENTIFY and CHANENABLESTATE commands."""

    CHANNEL_1 = 0x01
    CHANNEL_2 = 0x02
    CHANNEL_3 = 0x04
    CHANNEL_4 = 0x08


@enum.unique
class EnableState(int, Enum):
    """Used in CHANENABLESTATE commands."""

    CHANNEL_ENABLED = 0x01
    CHANNEL_DISABLED = 0x02

    def __bool__(self) -> bool:
        return self.value == 0x01

    @classmethod
    def from_bool(cls, toggle: bool) -> "EnableState":
        if toggle:
            return cls.CHANNEL_ENABLED
        return cls.CHANNEL_DISABLED


@enum.unique
class StatusBits(IntFlag, boundary=STRICT):
    """Bitmask used in MGMSG_MOT_GET_USTATUSUPDATE to indicate motor
    conditions. In the official documentation, all of these names have
    P_MOT_SB prepended to them.

    All spelling errors (e.g. "INITILIZING") are from the official
    documentation.
    """

    CWHARDLIMIT = 0x00000001
    CCWHARDLIMIT = 0x00000002
    CWSOFTLIMIT = 0x00000004
    CCWSOFTLIMIT = 0x00000008
    INMOTIONCW = 0x00000010
    INMOTIONCCW = 0x00000020
    JOGGINGCW = 0x00000040
    JOGGINGCCW = 0x00000080
    CONNECTED = 0x00000100
    HOMING = 0x00000200
    HOMED = 0x00000400
    INITILIZING = 0x00000800
    TRACKING = 0x00001000
    SETTLED = 0x00002000
    POSITIONERROR = 0x00004000
    INSTRERROR = 0x00008000
    INTERLOCK = 0x00010000
    OVERTEMP = 0x00020000
    BUSVOLTFAULT = 0x00040000
    COMMUTATIONERROR = 0x00080000
    DIGIP1 = 0x00100000
    DIGIP2 = 0x00200000
    DIGIP3 = 0x00400000
    DIGIP4 = 0x00800000
    OVERLOAD = 0x01000000
    ENCODERFAULT = 0x02000000
    OVERCURRENT = 0x04000000
    BUSCURRENTFAULT = 0x08000000
    POWEROK = 0x10000000
    ACTIVE = 0x20000000
    ERROR = 0x40000000
    ENABLED = 0x80000000


@dataclass(frozen=True, kw_only=True)
class Status:
    """Dataclass-based representation of StatusBits to enable more
    legible output formats such as JSON.
    """

    CWHARDLIMIT: bool = False
    CCWHARDLIMIT: bool = False
    CWSOFTLIMIT: bool = False
    CCWSOFTLIMIT: bool = False
    INMOTIONCW: bool = False
    INMOTIONCCW: bool = False
    JOGGINGCW: bool = False
    JOGGINGCCW: bool = False
    CONNECTED: bool = False
    HOMING: bool = False
    HOMED: bool = False
    INITILIZING: bool = False
    TRACKING: bool = False
    SETTLED: bool = False
    POSITIONERROR: bool = False
    INSTRERROR: bool = False
    INTERLOCK: bool = False
    OVERTEMP: bool = False
    BUSVOLTFAULT: bool = False
    COMMUTATIONERROR: bool = False
    DIGIP1: bool = False
    DIGIP2: bool = False
    DIGIP3: bool = False
    DIGIP4: bool = False
    OVERLOAD: bool = False
    ENCODERFAULT: bool = False
    OVERCURRENT: bool = False
    BUSCURRENTFAULT: bool = False
    POWEROK: bool = False
    ACTIVE: bool = False
    ERROR: bool = False
    ENABLED: bool = False

    @classmethod
    def from_bits(cls, bits: StatusBits) -> Self:
        kwargs = {}
        for bit in iter(bits):
            kwargs[bit.name] = True
        # See bug https://github.com/python/mypy/issues/13674
        return cls(**kwargs)  # type: ignore

    def to_bits(self) -> StatusBits:
        bits = StatusBits(0)
        for field in dataclasses.fields(self):
            if getattr(self, field.name):
                bits = bits | StatusBits[field.name]
        return bits


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
class AptMessageForStreamParsing:
    """This is used to parse streams of incoming messages and
    understand if they are header-only or data-attached messages. Note
    that it does NOT implement the AptMessage abstract base class."""

    header_struct: ClassVar[Struct] = Struct(f"<{ATS.WORD}{ATS.WORD}2{ATS.U_BYTE}")

    message_id: int
    data_length: int

    @classmethod
    def from_bytes(cls, raw: bytes) -> Self:
        message_id, data_length, destination, _ = cls.header_struct.unpack(raw)
        if destination & 0x80 != 0x80:
            # This is not a message with data following
            data_length = 0
        return cls(
            message_id=message_id,
            data_length=data_length,
        )


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
class AptMessageHeaderOnlyChanIdent(AptMessageHeaderOnly):
    message_struct: ClassVar[Struct] = Struct(
        f"<{ATS.WORD}{ATS.U_BYTE}{ATS.CHAR}2{ATS.U_BYTE}"
    )

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


@dataclass(frozen=True, kw_only=True)
class AptMessageWithDataMotorStatus(AptMessageWithData):
    data_length: ClassVar[int] = 14

    # The official documentation for this struct does not follow the
    # official vocabulary established at the beginning of the manual
    # to indicate which fields are signed and which are unsigned. The
    # below is a best guess, assuming that position and velocity can
    # possibly be negative. Motor current can clearly be negative.
    message_struct: ClassVar[Struct] = Struct(
        f"{AptMessageWithData.header_struct_str}{ATS.WORD}{ATS.LONG}{ATS.SHORT}{ATS.SHORT}{ATS.DWORD}"
    )

    chan_ident: ChanIdent
    position: int
    velocity: int
    motor_current: Quantity
    status: Status

    def __post_init__(self) -> None:
        self.motor_current.check("[current]")

    @classmethod
    def from_bytes(cls, raw: bytes) -> Self:
        (
            message_id,
            data_length,
            destination,
            source,
            chan_ident,
            position,
            velocity,
            motor_current,
            status_flag,
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

        return cls(
            destination=Address(destination & 0x7F),
            source=Address(source),
            chan_ident=ChanIdent(chan_ident),
            position=position,
            velocity=velocity,
            motor_current=(motor_current * ureg.milliamp),
            status=Status.from_bits(StatusBits(status_flag)),
        )

    def to_bytes(self) -> bytes:
        return self.message_struct.pack(
            self.message_id,
            self.data_length,
            self.destination_serialization,
            self.source,
            self.chan_ident,
            self.position,
            self.velocity,
            round(self.motor_current.to(ureg.milliamp).magnitude),
            self.status.to_bits(),
        )


@dataclass(frozen=True, kw_only=True)
class AptMessageWithDataPolParams(AptMessageWithData):
    data_length: ClassVar[int] = 12

    message_struct: ClassVar[Struct] = Struct(
        f"{AptMessageWithData.header_struct_str}6{ATS.WORD}"
    )

    unused: int = 0
    velocity: int
    home_position: int
    jog_step_1: int
    jog_step_2: int
    jog_step_3: int

    @classmethod
    def from_bytes(cls, raw: bytes) -> Self:
        (
            message_id,
            data_length,
            destination,
            source,
            unused,
            velocity,
            home_position,
            jog_step_1,
            jog_step_2,
            jog_step_3,
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

        return cls(
            destination=Address(destination & 0x7F),
            source=Address(source),
            unused=unused,
            velocity=velocity,
            home_position=home_position,
            jog_step_1=jog_step_1,
            jog_step_2=jog_step_2,
            jog_step_3=jog_step_3,
        )

    def to_bytes(self) -> bytes:
        return self.message_struct.pack(
            self.message_id,
            self.data_length,
            self.destination_serialization,
            self.source,
            self.unused,
            self.velocity,
            self.home_position,
            self.jog_step_1,
            self.jog_step_2,
            self.jog_step_3,
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
class AptMessage_MGMSG_MOD_REQ_CHANENABLESTATE(AptMessageHeaderOnlyChanIdent):
    message_id = AptMessageId.MGMSG_MOD_REQ_CHANENABLESTATE


@dataclass(frozen=True, kw_only=True)
class AptMessage_MGMSG_MOD_SET_CHANENABLESTATE(AptMessageHeaderOnlyChanEnableState):
    message_id = AptMessageId.MGMSG_MOD_SET_CHANENABLESTATE


@dataclass(frozen=True, kw_only=True)
class AptMessage_MGMSG_MOD_IDENTIFY(AptMessageHeaderOnlyChanIdent):
    message_id = AptMessageId.MGMSG_MOD_IDENTIFY


@dataclass(frozen=True, kw_only=True)
class AptMessage_MGMSG_MOT_ACK_USTATUSUPDATE(AptMessageHeaderOnlyNoParams):
    message_id = AptMessageId.MGMSG_MOT_ACK_USTATUSUPDATE


@dataclass(frozen=True, kw_only=True)
class AptMessage_MGMSG_MOT_GET_USTATUSUPDATE(AptMessageWithDataMotorStatus):
    message_id: ClassVar[AptMessageId] = AptMessageId.MGMSG_MOT_GET_USTATUSUPDATE


@dataclass(frozen=True, kw_only=True)
class AptMessage_MGMSG_MOT_REQ_USTATUSUPDATE(AptMessageHeaderOnlyChanIdent):
    message_id = AptMessageId.MGMSG_MOT_REQ_USTATUSUPDATE


@dataclass(frozen=True, kw_only=True)
class AptMessage_MGMSG_MOT_MOVE_ABSOLUTE(AptMessageWithData):
    data_length: ClassVar[int] = 6
    message_id: ClassVar[AptMessageId] = AptMessageId.MGMSG_MOT_MOVE_ABSOLUTE
    message_struct: ClassVar[Struct] = Struct(
        f"{AptMessageWithData.header_struct_str}{ATS.WORD}{ATS.LONG}"
    )

    chan_ident: ChanIdent
    absolute_distance: int

    @classmethod
    def from_bytes(cls, raw: bytes) -> "AptMessage_MGMSG_MOT_MOVE_ABSOLUTE":
        (
            message_id,
            data_length,
            destination,
            source,
            chan_ident,
            absolute_distance,
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

        return AptMessage_MGMSG_MOT_MOVE_ABSOLUTE(
            destination=Address(destination & 0x7F),
            source=Address(source),
            chan_ident=ChanIdent(chan_ident),
            absolute_distance=absolute_distance,
        )

    def to_bytes(self) -> bytes:
        return self.message_struct.pack(
            self.message_id,
            self.data_length,
            self.destination_serialization,
            self.source,
            self.chan_ident,
            self.absolute_distance,
        )


@dataclass(frozen=True, kw_only=True)
class AptMessage_MGMSG_MOT_MOVE_COMPLETED(AptMessageHeaderOnlyChanIdent):
    """Note that the APT documentation indicates that this should be
    followed by a full USTATUS data packet. In reality, for the
    MPC320, no data packet follows."""

    message_id: ClassVar[AptMessageId] = AptMessageId.MGMSG_MOT_MOVE_COMPLETED


@dataclass(frozen=True, kw_only=True)
class AptMessage_MGMSG_MOT_MOVE_HOME(AptMessageHeaderOnlyChanIdent):
    message_id = AptMessageId.MGMSG_MOT_MOVE_HOME


@dataclass(frozen=True, kw_only=True)
class AptMessage_MGMSG_MOT_MOVE_HOMED(AptMessageHeaderOnlyChanIdent):
    message_id = AptMessageId.MGMSG_MOT_MOVE_HOMED


@dataclass(frozen=True, kw_only=True)
class AptMessage_MGMSG_MOT_RESUME_ENDOFMOVEMSGS(AptMessageHeaderOnlyNoParams):
    message_id = AptMessageId.MGMSG_MOT_RESUME_ENDOFMOVEMSGS


@dataclass(frozen=True, kw_only=True)
class AptMessage_MGMSG_POL_GET_PARAMS(AptMessageWithDataPolParams):
    message_id = AptMessageId.MGMSG_POL_GET_PARAMS


@dataclass(frozen=True, kw_only=True)
class AptMessage_MGMSG_POL_REQ_PARAMS(AptMessageHeaderOnlyNoParams):
    message_id = AptMessageId.MGMSG_POL_REQ_PARAMS


@dataclass(frozen=True, kw_only=True)
class AptMessage_MGMSG_POL_SET_PARAMS(AptMessageWithDataPolParams):
    message_id = AptMessageId.MGMSG_POL_SET_PARAMS


@dataclass(frozen=True, kw_only=True)
class AptMessage_MGMSG_RESTOREFACTORYSETTINGS(AptMessageHeaderOnlyNoParams):
    message_id = AptMessageId.MGMSG_RESTOREFACTORYSETTINGS
