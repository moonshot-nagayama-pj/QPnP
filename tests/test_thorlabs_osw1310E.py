from pnpq.devices.switch_thorlabs_osw1310E import Switch

import pytest


def test_disconnected_initialization():
    with pytest.raises(Exception):
        Switch("ABC", "DEF")
