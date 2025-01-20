import pytest

from pnpq.apt.connection import AptConnection
from pnpq.devices.refactored_waveplate_thorlabs_k10cr1 import WaveplateThorlabsK10CR1
from pnpq.units import pnpq_ureg


@pytest.fixture(name="device", scope="module")
def device_fixture() -> WaveplateThorlabsK10CR1:
    connection = AptConnection(serial_number="55407714")
    return WaveplateThorlabsK10CR1(connection=connection)


def test_move_absolute(device: WaveplateThorlabsK10CR1) -> None:
    device.move_absolute(0 * pnpq_ureg.degree)
