from pnpq.devices.waveplate_thorlabs_kb10crm import Waveplate
from pnpq.errors import DevicePortNotFoundError

import pytest


def test_disconnected_initialization() -> None:
    with pytest.raises(DevicePortNotFoundError):
        Waveplate("ABC", "DEF")
