from pnpq.devices.switch_thorlabs_osw1310e import Switch

import pytest


def test_disconnected_initialization() -> None:
    with pytest.raises(Exception):
        Switch("ABC", "DEF")
