import pytest

from pnpq.apt.protocol import ChanIdent
from pnpq.devices.polarization_controller_thorlabs_mpc320 import (
    PolarizationControllerThorlabsMPC320,
)


@pytest.fixture(scope="module")
def device() -> PolarizationControllerThorlabsMPC320:
    return PolarizationControllerThorlabsMPC320(serial_number="38454784")
    # return PolarizationControllerThorlabsMPC320(serial_number="38444954")


# def test_check_status(device: PolarizationControllerThorlabsMPC320) -> None:
#    device.check_status()


def test_move_absolute(device: PolarizationControllerThorlabsMPC320) -> None:
    device.identify(ChanIdent.CHANNEL_1)

    device.home(ChanIdent.CHANNEL_1)
    device.home(ChanIdent.CHANNEL_2)
    device.home(ChanIdent.CHANNEL_3)

    device.move_absolute(ChanIdent.CHANNEL_1, 160)
    device.move_absolute(ChanIdent.CHANNEL_2, 160)
    device.move_absolute(ChanIdent.CHANNEL_3, 160)

    # device.move_absolute(ChanIdent.CHANNEL_2, 30)
    # device.move_absolute(ChanIdent.CHANNEL_1, 90)
    # device.move_absolute(ChanIdent.CHANNEL_3, 90)

    # device.move_absolute(ChanIdent.CHANNEL_3, 165)
    # device.move_absolute(ChanIdent.CHANNEL_2, 90)
    # device.move_absolute(ChanIdent.CHANNEL_1, 0)

    # device.move_absolute(ChanIdent.CHANNEL_1, 10)
    # device.move_absolute(ChanIdent.CHANNEL_1, 100)
    # device.move_absolute(ChanIdent.CHANNEL_1, 50)

    device.home(ChanIdent.CHANNEL_1)
    device.home(ChanIdent.CHANNEL_2)
    device.home(ChanIdent.CHANNEL_3)

    # One of the channels on our test device appears to forget to turn
    # off its motor when it's homed or set to 0 degrees. It just sits
    # there vibrating and whining. It's not really safe to leave the
    # device at degree 0 for this reason. 170 also seems too far (160 seems about the safest)
    # device.move_absolute(ChanIdent.CHANNEL_1, 10)
    # device.move_absolute(ChanIdent.CHANNEL_2, 10)
    # device.move_absolute(ChanIdent.CHANNEL_3, 10)

    # device.set_params(home_position=1000)

    # device.home(ChanIdent.CHANNEL_1)
    # device.home(ChanIdent.CHANNEL_2)
    # device.home(ChanIdent.CHANNEL_3)

    # device.move_absolute(ChanIdent.CHANNEL_1, 10)
    # device.move_absolute(ChanIdent.CHANNEL_2, 10)
    # device.move_absolute(ChanIdent.CHANNEL_3, 10)

    # device.set_params(home_position=0)

    # device.home(ChanIdent.CHANNEL_1)
    # device.home(ChanIdent.CHANNEL_2)
    # device.home(ChanIdent.CHANNEL_3)

    # device.move_absolute(ChanIdent.CHANNEL_1, 0)
    # device.move_absolute(ChanIdent.CHANNEL_2, 0)
    # device.move_absolute(ChanIdent.CHANNEL_3, 0)
