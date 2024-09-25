import pytest

from pnpq.apt.protocol import ChanIdent
from pnpq.devices.polarization_controller_thorlabs_mpc320 import (
    PolarizationControllerThorlabsMPC320,
)


@pytest.fixture(scope="module")
def device() -> PolarizationControllerThorlabsMPC320:
    return PolarizationControllerThorlabsMPC320(serial_number="38454784")


# def test_check_status(device: PolarizationControllerThorlabsMPC320) -> None:
#    device.check_status()


def test_move_absolute(device: PolarizationControllerThorlabsMPC320) -> None:
    device.home(ChanIdent.CHANNEL_1)
    device.home(ChanIdent.CHANNEL_2)
    device.home(ChanIdent.CHANNEL_3)
