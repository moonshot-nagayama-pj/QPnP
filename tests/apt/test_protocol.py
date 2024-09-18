from pnpq.apt.protocol import (
    Address,
    AptMessage_MGMSG_HW_DISCONNECT,
    AptMessage_MGMSG_HW_GET_INFO,
    AptMessage_MGMSG_HW_REQ_INFO,
    AptMessage_MGMSG_HW_START_UPDATEMSGS,
    AptMessage_MGMSG_HW_STOP_UPDATEMSGS,
    AptMessage_MGMSG_MOD_GET_CHANENABLESTATE,
    AptMessage_MGMSG_MOD_REQ_CHANENABLESTATE,
    AptMessage_MGMSG_MOD_SET_CHANENABLESTATE,
    ChanIdent,
    EnableState,
    FirmwareVersion,
    HardwareType,
)


def test_AptMessage_MGMSG_HW_DISCONNECT_from_bytes() -> None:
    msg = AptMessage_MGMSG_HW_DISCONNECT.from_bytes(b"\x02\x00\x00\x00\x50\x01")
    assert msg.message_id == 0x0002
    assert msg.destination == 0x50
    assert msg.source == 0x01


def test_AptMessage_MGMSG_HW_DISCONNECT_to_bytes() -> None:
    msg = AptMessage_MGMSG_HW_DISCONNECT(
        destination=Address.GENERIC_USB, source=Address.HOST_CONTROLLER
    )
    assert msg.to_bytes() == b"\x02\x00\x00\x00\x50\x01"


def test_AptMessage_MGMSG_HW_GET_INFO_from_bytes() -> None:
    # Example message from official documentation, page 53 of issue
    # 37. The sample message doesn't match the example value for
    # modification state afterwards; we use the latter value here.
    msg = AptMessage_MGMSG_HW_GET_INFO.from_bytes(
        bytes.fromhex("0600 5400 81 22 89539A05 494F4E3030312000 2C00 02013900")
        + bytes(60)
        + bytes.fromhex("0100 0300 0100")
    )
    assert msg.message_id == 0x0006
    assert msg.destination == 0x01
    assert msg.source == 0x22
    assert msg.firmware_version == FirmwareVersion(
        major_revision=57,
        interim_revision=1,
        minor_revision=2,
        unused=0,
    )
    assert msg.hardware_type == HardwareType.BRUSHLESS_DC_CONTROLLER
    assert msg.hardware_version == 1
    assert msg.internal_use == bytes(60)
    assert msg.model_number == "ION001 "
    assert msg.modification_state == 3
    assert msg.number_of_channels == 1
    assert msg.serial_number == 94000009


def test_AptMessage_MGMSG_HW_GET_INFO_to_bytes() -> None:
    msg = AptMessage_MGMSG_HW_GET_INFO(
        destination=Address.HOST_CONTROLLER,
        source=Address.BAY_1,
        firmware_version=FirmwareVersion(
            major_revision=57,
            interim_revision=1,
            minor_revision=2,
            unused=0,
        ),
        hardware_type=HardwareType.BRUSHLESS_DC_CONTROLLER,
        hardware_version=1,
        internal_use=bytes(60),
        model_number="ION001 ",
        modification_state=3,
        number_of_channels=1,
        serial_number=94000009,
    )
    assert msg.to_bytes() == bytes.fromhex(
        "0600 5400 81 22 89539A05 494F4E3030312000 2C00 02013900"
    ) + bytes(60) + bytes.fromhex("0100 0300 0100")


def test_AptMessage_MGMSG_HW_REQ_INFO_from_bytes() -> None:
    msg = AptMessage_MGMSG_HW_REQ_INFO.from_bytes(b"\x05\x00\x00\x00\x50\x01")
    assert msg.message_id == 0x0005
    assert msg.destination == 0x50
    assert msg.source == 0x01


def test_AptMessage_MGMSG_HW_REQ_INFO_to_bytes() -> None:
    msg = AptMessage_MGMSG_HW_REQ_INFO(
        destination=Address.GENERIC_USB, source=Address.HOST_CONTROLLER
    )
    assert msg.to_bytes() == b"\x05\x00\x00\x00\x50\x01"


def test_AptMessage_MGMSG_HW_START_UPDATEMSGS_from_bytes() -> None:
    msg = AptMessage_MGMSG_HW_START_UPDATEMSGS.from_bytes(b"\x11\x00\x00\x00\x50\x01")
    assert msg.message_id == 0x0011
    assert msg.destination == 0x50
    assert msg.source == 0x01


def test_AptMessage_MGMSG_HW_START_UPDATEMSGS_to_bytes() -> None:
    msg = AptMessage_MGMSG_HW_START_UPDATEMSGS(
        destination=Address.GENERIC_USB, source=Address.HOST_CONTROLLER
    )
    assert msg.to_bytes() == b"\x11\x00\x00\x00\x50\x01"


def test_AptMessage_MGMSG_HW_STOP_UPDATEMSGS_from_bytes() -> None:
    msg = AptMessage_MGMSG_HW_STOP_UPDATEMSGS.from_bytes(b"\x12\x00\x00\x00\x50\x01")
    assert msg.message_id == 0x0012
    assert msg.destination == 0x50
    assert msg.source == 0x01


def test_AptMessage_MGMSG_HW_STOP_UPDATEMSGS_to_bytes() -> None:
    msg = AptMessage_MGMSG_HW_STOP_UPDATEMSGS(
        destination=Address.GENERIC_USB, source=Address.HOST_CONTROLLER
    )
    assert msg.to_bytes() == b"\x12\x00\x00\x00\x50\x01"


def test_AptMessage_MGMSG_MOD_GET_CHANENABLESTATE_from_bytes() -> None:
    msg = AptMessage_MGMSG_MOD_GET_CHANENABLESTATE.from_bytes(
        b"\x12\x02\x01\x02\x50\x01"
    )
    assert msg.chan_ident == 0x01
    assert msg.destination == 0x50
    assert msg.enable_state == 0x02
    assert msg.message_id == 0x0212
    assert msg.source == 0x01


def test_AptMessage_MGMSG_MOD_GET_CHANENABLESTATE_to_bytes() -> None:
    msg = AptMessage_MGMSG_MOD_GET_CHANENABLESTATE(
        chan_ident=ChanIdent.CHANNEL_1,
        destination=Address.GENERIC_USB,
        enable_state=EnableState.CHANNEL_DISABLED,
        source=Address.HOST_CONTROLLER,
    )
    assert msg.to_bytes() == b"\x12\x02\x01\x02\x50\x01"


def test_AptMessage_MGMSG_MOD_REQ_CHANENABLESTATE_from_bytes() -> None:
    msg = AptMessage_MGMSG_MOD_REQ_CHANENABLESTATE.from_bytes(
        b"\x11\x02\x01\x00\x50\x01"
    )
    assert msg.chan_ident == 0x01
    assert msg.destination == 0x50
    assert msg.message_id == 0x0211
    assert msg.source == 0x01


def test_AptMessage_MGMSG_MOD_REQ_CHANENABLESTATE_to_bytes() -> None:
    msg = AptMessage_MGMSG_MOD_REQ_CHANENABLESTATE(
        chan_ident=ChanIdent.CHANNEL_1,
        destination=Address.GENERIC_USB,
        source=Address.HOST_CONTROLLER,
    )
    assert msg.to_bytes() == b"\x11\x02\x01\x00\x50\x01"


def test_AptMessage_MGMSG_MOD_SET_CHANENABLESTATE_from_bytes() -> None:
    msg = AptMessage_MGMSG_MOD_SET_CHANENABLESTATE.from_bytes(
        b"\x10\x02\x01\x02\x50\x01"
    )
    assert msg.chan_ident == 0x01
    assert msg.destination == 0x50
    assert msg.enable_state == 0x02
    assert msg.message_id == 0x0210
    assert msg.source == 0x01


def test_AptMessage_MGMSG_MOD_SET_CHANENABLESTATE_to_bytes() -> None:
    msg = AptMessage_MGMSG_MOD_SET_CHANENABLESTATE(
        chan_ident=ChanIdent.CHANNEL_1,
        destination=Address.GENERIC_USB,
        enable_state=EnableState.CHANNEL_DISABLED,
        source=Address.HOST_CONTROLLER,
    )
    assert msg.to_bytes() == b"\x10\x02\x01\x02\x50\x01"
