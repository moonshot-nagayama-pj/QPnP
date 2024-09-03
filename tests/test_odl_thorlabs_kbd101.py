from pnpq.devices.odl_thorlabs_kbd101 import OdlThorlabs

import pytest


def test_disconnected_initialization() -> None:
    with pytest.raises(RuntimeError):
        OdlThorlabs("ABC", "DEF")
