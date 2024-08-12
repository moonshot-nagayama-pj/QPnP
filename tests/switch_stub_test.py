from pnpq.devices.switch_stub import Switch
from pnpq.errors import (
    DeviceDisconnectedError
)
import pytest

@pytest.fixture
def connected_switch():
    switch = Switch()
    switch.connect()
    return switch

@pytest.mark.parametrize("f", [("bar_state"), ("cross")])
def test_access_without_connection(f):
    switch = Switch() # noqa: F841
    with pytest.raises(DeviceDisconnectedError):
        eval(f"switch.{f}()")

def test_set_bar_state(connected_switch):
    connected_switch.bar_state()
    assert connected_switch.state == 1

def test_set_cross_state(connected_switch):
    connected_switch.cross()
    assert connected_switch.state == 2
