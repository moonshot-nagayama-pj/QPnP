import pytest

from pnpq.devices.waveplate_thorlabs_kb10crm import Waveplate
from pnpq.errors import DevicePortNotFoundError


def test_disconnected_initialization() -> None:
    with pytest.raises(DevicePortNotFoundError):
        Waveplate("ABC", "DEF")
