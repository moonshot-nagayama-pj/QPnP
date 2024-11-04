# pylint: disable=C0103
import pytest
from pint import DimensionalityError

from pnpq.apt.protocol import (
    Address,
    AptMessage_MGMSG_HW_DISCONNECT,
    AptMessage_MGMSG_HW_GET_INFO,
    AptMessage_MGMSG_HW_REQ_INFO,
    AptMessage_MGMSG_HW_START_UPDATEMSGS,
    AptMessage_MGMSG_HW_STOP_UPDATEMSGS,
    AptMessage_MGMSG_MOD_GET_CHANENABLESTATE,
    AptMessage_MGMSG_MOD_IDENTIFY,
    AptMessage_MGMSG_MOD_REQ_CHANENABLESTATE,
    AptMessage_MGMSG_MOD_SET_CHANENABLESTATE,
    AptMessage_MGMSG_MOT_ACK_USTATUSUPDATE,
    AptMessage_MGMSG_MOT_GET_POSCOUNTER,
    AptMessage_MGMSG_MOT_GET_USTATUSUPDATE,
    AptMessage_MGMSG_MOT_MOVE_ABSOLUTE,
    AptMessage_MGMSG_MOT_MOVE_COMPLETED,
    AptMessage_MGMSG_MOT_MOVE_HOME,
    AptMessage_MGMSG_MOT_MOVE_HOMED,
    AptMessage_MGMSG_MOT_MOVE_JOG,
    AptMessage_MGMSG_MOT_MOVE_STOP,
    AptMessage_MGMSG_MOT_MOVE_STOPPED,
    AptMessage_MGMSG_MOT_REQ_POSCOUNTER,
    AptMessage_MGMSG_MOT_REQ_USTATUSUPDATE,
    AptMessage_MGMSG_MOT_SET_POSCOUNTER,
    AptMessage_MGMSG_POL_GET_PARAMS,
    AptMessage_MGMSG_POL_REQ_PARAMS,
    AptMessage_MGMSG_POL_SET_PARAMS,
    AptMessage_MGMSG_RESTOREFACTORYSETTINGS,
    ChanIdent,
    EnableState,
    FirmwareVersion,
    HardwareType,
    JogDirection,
    Status,
    StopMode,
)
from pnpq.units import ureg


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


def test_AptMessage_MGMSG_MOD_IDENTIFY_from_bytes() -> None:
    msg = AptMessage_MGMSG_MOD_IDENTIFY.from_bytes(b"\x23\x02\x01\x00\x50\x01")
    assert msg.chan_ident == 0x01
    assert msg.destination == 0x50
    assert msg.message_id == 0x0223
    assert msg.source == 0x01


def test_AptMessage_MGMSG_MOD_IDENTIFY_to_bytes() -> None:
    msg = AptMessage_MGMSG_MOD_IDENTIFY(
        chan_ident=ChanIdent.CHANNEL_1,
        destination=Address.GENERIC_USB,
        source=Address.HOST_CONTROLLER,
    )
    assert msg.to_bytes() == b"\x23\x02\x01\x00\x50\x01"


def test_AptMessage_MGMSG_MOT_GET_POSCOUNTER_from_bytes() -> None:
    msg = AptMessage_MGMSG_MOT_GET_POSCOUNTER.from_bytes(
        bytes.fromhex("1204 0600 A2 01 0100400D0300")
    )

    assert msg.destination == 0x22
    assert msg.message_id == 0x0412
    assert msg.source == 0x01
    assert msg.chan_ident == 0x01
    assert msg.position == 200000


def test_AptMessage_MGMSG_MOT_GET_POSCOUNTER_to_bytes() -> None:
    msg = AptMessage_MGMSG_MOT_GET_POSCOUNTER(
        destination=Address.BAY_1,
        source=Address.HOST_CONTROLLER,
        chan_ident=ChanIdent.CHANNEL_1,
        position=200000,
    )
    assert msg.to_bytes() == bytes.fromhex("1204 0600 A2 01 0100400D0300")


def test_AptMessage_MGMSG_MOT_SET_POSCOUNTER_from_bytes() -> None:
    msg = AptMessage_MGMSG_MOT_SET_POSCOUNTER.from_bytes(
        bytes.fromhex("1004 0600 A2 01 0100400D0300")
    )

    # The official documentation's example refers to this as "Channel 2," but this is actually bay 1.
    assert msg.destination == 0x22

    assert msg.message_id == 0x0410
    assert msg.source == 0x01
    assert msg.chan_ident == 0x01
    assert msg.position == 200000


def test_AptMessage_MGMSG_MOT_SET_POSCOUNTER_to_bytes() -> None:
    msg = AptMessage_MGMSG_MOT_SET_POSCOUNTER(
        destination=Address.BAY_1,
        source=Address.HOST_CONTROLLER,
        chan_ident=ChanIdent.CHANNEL_1,
        position=200000,
    )
    assert msg.to_bytes() == bytes.fromhex("1004 0600 A2 01 0100400D0300")


def test_AptMessage_MGMSG_MOT_REQ_POSCOUNTER_from_bytes() -> None:
    msg = AptMessage_MGMSG_MOT_REQ_POSCOUNTER.from_bytes(b"\x11\x04\x01\x00\x50\x01")
    assert msg.chan_ident == 0x01
    assert msg.message_id == 0x0411
    assert msg.destination == 0x50
    assert msg.source == 0x01


def test_AptMessage_MGMSG_MOT_REQ_POSCOUNTER_to_bytes() -> None:
    msg = AptMessage_MGMSG_MOT_REQ_POSCOUNTER(
        chan_ident=ChanIdent.CHANNEL_1,
        destination=Address.GENERIC_USB,
        source=Address.HOST_CONTROLLER,
    )
    assert msg.to_bytes() == b"\x11\x04\x01\x00\x50\x01"


def test_AptMessage_MGMSG_MOT_ACK_USTATUSUPDATE_from_bytes() -> None:
    msg = AptMessage_MGMSG_MOT_ACK_USTATUSUPDATE.from_bytes(b"\x92\x04\x00\x00\x50\x01")
    assert msg.destination == 0x50
    assert msg.message_id == 0x0492
    assert msg.source == 0x01


def test_AptMessage_MGMSG_MOT_ACK_USTATUSUPDATE_to_bytes() -> None:
    msg = AptMessage_MGMSG_MOT_ACK_USTATUSUPDATE(
        destination=Address.GENERIC_USB,
        source=Address.HOST_CONTROLLER,
    )
    assert msg.to_bytes() == b"\x92\x04\x00\x00\x50\x01"


def test_AptMessage_MGMSG_MOT_GET_USTATUSUPDATE_from_bytes() -> None:
    msg = AptMessage_MGMSG_MOT_GET_USTATUSUPDATE.from_bytes(
        bytes.fromhex("9104 0e00 81 22 0100 00000001 0001 FFFF 07000000")
    )
    assert msg.destination == 0x01
    assert msg.message_id == 0x0491
    assert msg.source == 0x22
    assert msg.position == 16777216
    assert msg.velocity == 256
    assert msg.motor_current == -1 * ureg.milliamp
    assert msg.status == Status(CWHARDLIMIT=True, CCWHARDLIMIT=True, CWSOFTLIMIT=True)


def test_AptMessage_MGMSG_MOT_GET_USTATUSUPDATE_to_bytes() -> None:
    msg = AptMessage_MGMSG_MOT_GET_USTATUSUPDATE(
        destination=Address.HOST_CONTROLLER,
        source=Address.BAY_1,
        chan_ident=ChanIdent.CHANNEL_1,
        position=1,
        velocity=1,
        motor_current=(-1 * ureg.milliamp),
        status=Status(CWHARDLIMIT=True, CCWHARDLIMIT=True, CWSOFTLIMIT=True),
    )
    assert msg.to_bytes() == bytes.fromhex(
        "9104 0e00 81 22 0100 01000000 0100 FFFF 07000000"
    )


def test_AptMessage_MGMSG_MOT_GET_USTATUSUPDATE_invalid_unit() -> None:
    with pytest.raises(DimensionalityError):
        AptMessage_MGMSG_MOT_GET_USTATUSUPDATE(
            destination=Address.HOST_CONTROLLER,
            source=Address.BAY_1,
            chan_ident=ChanIdent.CHANNEL_1,
            position=1,
            velocity=1,
            motor_current=(-1 * ureg.meter),
            status=Status(CWHARDLIMIT=True, CCWHARDLIMIT=True, CWSOFTLIMIT=True),
        )


def test_AptMessage_MGMSG_MOT_REQ_USTATUSUPDATE_from_bytes() -> None:
    msg = AptMessage_MGMSG_MOT_REQ_USTATUSUPDATE.from_bytes(b"\x90\x04\x01\x00\x50\x01")
    assert msg.chan_ident == 0x01
    assert msg.destination == 0x50
    assert msg.message_id == 0x0490
    assert msg.source == 0x01


def test_AptMessage_MGMSG_MOT_REQ_USTATUSUPDATE_to_bytes() -> None:
    msg = AptMessage_MGMSG_MOT_REQ_USTATUSUPDATE(
        chan_ident=ChanIdent.CHANNEL_1,
        destination=Address.GENERIC_USB,
        source=Address.HOST_CONTROLLER,
    )
    assert msg.to_bytes() == b"\x90\x04\x01\x00\x50\x01"


def test_AptMessage_MGMSG_MOT_MOVE_ABSOLUTE_from_bytes() -> None:
    msg = AptMessage_MGMSG_MOT_MOVE_ABSOLUTE.from_bytes(
        bytes.fromhex("5304 0600 A2 01 0100 400D0300")
    )
    assert msg.destination == 0x22
    assert msg.message_id == 0x0453
    assert msg.source == 0x01
    assert msg.chan_ident == 0x01
    assert msg.absolute_distance == 200000


def test_AptMessage_MGMSG_MOT_MOVE_ABSOLUTE_to_bytes() -> None:
    msg = AptMessage_MGMSG_MOT_MOVE_ABSOLUTE(
        destination=Address.BAY_1,
        source=Address.HOST_CONTROLLER,
        chan_ident=ChanIdent.CHANNEL_1,
        absolute_distance=200000,
    )
    assert msg.to_bytes() == bytes.fromhex("5304 0600 A2 01 0100 400D0300")


def test_AptMessage_MGMSG_MOT_MOVE_COMPLETED_from_bytes() -> None:
    msg = AptMessage_MGMSG_MOT_MOVE_COMPLETED.from_bytes(
        bytes.fromhex("6404 0100 01 22")
    )
    assert msg.destination == 0x01
    assert msg.message_id == 0x0464
    assert msg.source == 0x22
    assert msg.chan_ident == 0x01


def test_AptMessage_MGMSG_MOT_MOVE_COMPLETED_to_bytes() -> None:
    msg = AptMessage_MGMSG_MOT_MOVE_COMPLETED(
        destination=Address.HOST_CONTROLLER,
        source=Address.BAY_1,
        chan_ident=ChanIdent.CHANNEL_1,
    )
    assert msg.to_bytes() == bytes.fromhex("6404 0100 01 22")


def test_AptMessage_MGMSG_MOT_MOVE_HOME_from_bytes() -> None:
    msg = AptMessage_MGMSG_MOT_MOVE_HOME.from_bytes(b"\x43\x04\x01\x00\x50\x01")
    assert msg.chan_ident == 0x01
    assert msg.destination == 0x50
    assert msg.message_id == 0x0443
    assert msg.source == 0x01


def test_AptMessage_MGMSG_MOT_MOVE_HOME_to_bytes() -> None:
    msg = AptMessage_MGMSG_MOT_MOVE_HOME(
        chan_ident=ChanIdent.CHANNEL_1,
        destination=Address.GENERIC_USB,
        source=Address.HOST_CONTROLLER,
    )
    assert msg.to_bytes() == b"\x43\x04\x01\x00\x50\x01"


def test_AptMessage_MGMSG_MOT_MOVE_HOMED_from_bytes() -> None:
    msg = AptMessage_MGMSG_MOT_MOVE_HOMED.from_bytes(b"\x44\x04\x01\x02\x50\x01")
    assert msg.chan_ident == 0x01
    assert msg.destination == 0x50
    assert msg.message_id == 0x0444
    assert msg.source == 0x01


def test_AptMessage_MGMSG_MOT_MOVE_HOMED_to_bytes() -> None:
    msg = AptMessage_MGMSG_MOT_MOVE_HOMED(
        chan_ident=ChanIdent.CHANNEL_1,
        destination=Address.GENERIC_USB,
        source=Address.HOST_CONTROLLER,
    )
    assert msg.to_bytes() == b"\x44\x04\x01\x00\x50\x01"


def test_AptMessage_MGMSG_POL_GET_PARAMS_to_bytes() -> None:
    msg = AptMessage_MGMSG_POL_GET_PARAMS(
        destination=Address.GENERIC_USB,
        source=Address.HOST_CONTROLLER,
        velocity=50,
        home_position=0,
        jog_step_1=25,
        jog_step_2=25,
        jog_step_3=25,
    )
    assert msg.to_bytes() == bytes.fromhex(
        "3205 0C00 D0 01 0000 3200 0000 1900 1900 1900"
    )


def test_AptMessage_MGMSG_POL_GET_PARAMS_from_bytes() -> None:
    msg = AptMessage_MGMSG_POL_GET_PARAMS.from_bytes(
        bytes.fromhex("3205 0C00 D0 01 0000 3200 0000 1900 1900 1900")
    )
    assert msg.destination == 0x50
    assert msg.message_id == 0x0532
    assert msg.source == 0x01
    assert msg.unused == 0
    assert msg.velocity == 50
    assert msg.home_position == 0
    assert msg.jog_step_1 == 25
    assert msg.jog_step_2 == 25
    assert msg.jog_step_3 == 25


def test_AptMessage_AptMessage_MGMSG_POL_REQ_PARAMS_from_bytes() -> None:
    msg = AptMessage_MGMSG_POL_REQ_PARAMS.from_bytes(b"\x31\x05\x00\x00\x50\x01")
    assert msg.destination == 0x50
    assert msg.message_id == 0x0531
    assert msg.source == 0x01


def test_AptMessage_AptMessage_MGMSG_POL_REQ_PARAMS_to_bytes() -> None:
    msg = AptMessage_MGMSG_POL_REQ_PARAMS(
        destination=Address.GENERIC_USB,
        source=Address.HOST_CONTROLLER,
    )
    assert msg.to_bytes() == b"\x31\x05\x00\x00\x50\x01"


def test_AptMessage_MGMSG_POL_SET_PARAMS_to_bytes() -> None:
    msg = AptMessage_MGMSG_POL_SET_PARAMS(
        destination=Address.GENERIC_USB,
        source=Address.HOST_CONTROLLER,
        velocity=50,
        home_position=0,
        jog_step_1=25,
        jog_step_2=25,
        jog_step_3=25,
    )
    assert msg.to_bytes() == bytes.fromhex(
        "3005 0C00 D0 01 0000 3200 0000 1900 1900 1900"
    )


def test_AptMessage_MGMSG_POL_SET_PARAMS_from_bytes() -> None:
    msg = AptMessage_MGMSG_POL_SET_PARAMS.from_bytes(
        bytes.fromhex("3005 0C00 D0 01 0000 3200 0000 1900 1900 1900")
    )
    assert msg.destination == 0x50
    assert msg.message_id == 0x0530
    assert msg.source == 0x01
    assert msg.unused == 0
    assert msg.velocity == 50
    assert msg.home_position == 0
    assert msg.jog_step_1 == 25
    assert msg.jog_step_2 == 25
    assert msg.jog_step_3 == 25


def test_AptMessage_MGMSG_MOT_MOVE_JOG_from_bytes() -> None:
    msg = AptMessage_MGMSG_MOT_MOVE_JOG.from_bytes(b"\x6A\x04\x01\x02\x01\x50")
    assert msg.message_id == 0x046A
    assert msg.chan_ident == 0x01
    assert msg.jog_direction == 0x02
    assert msg.destination == 0x01
    assert msg.source == 0x50


def test_AptMessage_MGMSG_MOT_MOVE_JOG_to_bytes() -> None:
    msg = AptMessage_MGMSG_MOT_MOVE_JOG(
        chan_ident=ChanIdent.CHANNEL_1,
        destination=Address.GENERIC_USB,
        jog_direction=JogDirection.FORWARD,
        source=Address.HOST_CONTROLLER,
    )
    assert msg.to_bytes() == b"\x6A\x04\x01\x01\x50\x01"


def test_AptMessage_MGMSG_MOT_MOVE_STOP_from_bytes() -> None:
    msg = AptMessage_MGMSG_MOT_MOVE_STOP.from_bytes(b"\x65\x04\x01\x01\x50\x01")
    assert msg.message_id == 0x0465
    assert msg.chan_ident == 0x01
    assert msg.stop_mode == 0x01
    assert msg.destination == 0x50
    assert msg.source == 0x01


def test_AptMessage_MGMSG_MOT_MOVE_STOP_to_bytes() -> None:
    msg = AptMessage_MGMSG_MOT_MOVE_STOP(
        chan_ident=ChanIdent.CHANNEL_1,
        destination=Address.GENERIC_USB,
        stop_mode=StopMode.IMMEDIATE,
        source=Address.HOST_CONTROLLER,
    )
    assert msg.to_bytes() == b"\x65\x04\x01\x01\x50\x01"


def test_AptMessage_MGMSG_MOT_MOVE_STOPPED_from_bytes() -> None:
    msg = AptMessage_MGMSG_MOT_MOVE_STOPPED.from_bytes(bytes.fromhex("6604 0100 01 22"))
    assert msg.destination == 0x01
    assert msg.message_id == 0x0466
    assert msg.source == 0x22
    assert msg.chan_ident == 0x01


def test_AptMessage_MGMSG_MOT_MOVE_STOPPED_to_bytes() -> None:
    msg = AptMessage_MGMSG_MOT_MOVE_STOPPED(
        destination=Address.HOST_CONTROLLER,
        source=Address.BAY_1,
        chan_ident=ChanIdent.CHANNEL_1,
    )
    assert msg.to_bytes() == bytes.fromhex("6604 0100 01 22")


def test_AptMessage_MGMSG_RESTOREFACTORYSETTINGS_from_bytes() -> None:
    msg = AptMessage_MGMSG_RESTOREFACTORYSETTINGS.from_bytes(
        b"\x86\x06\x00\x00\x50\x01"
    )
    assert msg.message_id == 0x0686
    assert msg.destination == 0x50
    assert msg.source == 0x01


def test_AptMessage_MGMSG_RESTOREFACTORYSETTINGS_to_bytes() -> None:
    msg = AptMessage_MGMSG_RESTOREFACTORYSETTINGS(
        destination=Address.GENERIC_USB, source=Address.HOST_CONTROLLER
    )
    assert msg.to_bytes() == b"\x86\x06\x00\x00\x50\x01"
