import pytest

from pnpq.apt.protocol import ChanIdent
from pnpq.devices.polarization_controller_thorlabs_mpc320 import (
    PolarizationControllerThorlabsMPC320,
)


@pytest.fixture(scope="module")
def device() -> PolarizationControllerThorlabsMPC320:
    return PolarizationControllerThorlabsMPC320(serial_number="ABC")


def test_check_status(device: PolarizationControllerThorlabsMPC320) -> None:
    device.check_status()


def test_move_absolute(device: PolarizationControllerThorlabsMPC320) -> None:
    device.move_absolute(ChanIdent.CHANNEL_1, 90.0)
