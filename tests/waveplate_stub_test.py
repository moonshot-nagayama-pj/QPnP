from pnpq.devices.waveplate_stub import WaveplateStub
from pnpq.errors import (
    DeviceDisconnectedError,
    WaveplateInvalidDegreeError,
    WaveplateInvalidMotorChannelError,
    WaveplateInvalidStepsError,
)
import pytest

@pytest.mark.parametrize("f,argc", [("identify", 0), ("home", 0), ("auto_update_start", 0), ("auto_update_stop", 0), ("disable_channel", 1), ("enable_channel", 1), ("rotate", 1), ("getpos", 0), ("step_forward", 1), ("step_backward", 1), ("rotate_relative", 1), ("custom_home", 1), ("custom_rotate", 1)])
def test_access_without_connection(f, argc):
    wp = WaveplateStub()
    with pytest.raises(DeviceDisconnectedError):
        # Since the device is not connected, all methods should raise DeviceDisconnectedError
        # For simplicity, 1 is passed as argument for all methods, the value should be small enough to not raise any other errors
        # TODO: Refactor this to be more flexible in the future
        arg = ",".join(["1"]*argc)
        eval(f"wp.{f}({arg})")

@pytest.fixture
def c_wp():
    """Connected Waveplate Stub Test Fixture"""
    wp = WaveplateStub()
    wp.connect()
    return wp

def test_identify(c_wp):
    c_wp.identify()

def test_home(c_wp):
    c_wp.rotate(90)
    c_wp.home()
    assert c_wp.getpos() == 0

def test_rotate(c_wp):
    c_wp.rotate(90)
    assert c_wp.getpos() == 90 * c_wp.resolution

def test_rotate_invalid_degree(c_wp):
    with pytest.raises(WaveplateInvalidDegreeError):
        c_wp.rotate(361)

def test_disable_and_enable_channels(c_wp):
    c_wp.disable_channel(1)
    c_wp.rotate(90)
    # Should not move
    assert c_wp.getpos() == 0
    c_wp.enable_channel(1)
    c_wp.rotate(90)
    assert c_wp.getpos() == 90 * c_wp.resolution

def test_disable_invalid_channel(c_wp):
    with pytest.raises(WaveplateInvalidMotorChannelError):
        # Waveplates has max channel of 1
        c_wp.disable_channel(2)

def test_enable_duplicate_channel(c_wp):
    c_wp.disable_channel(1)
    c_wp.enable_channel(1)
    c_wp.enable_channel(1)
    # Make sure there is only one channel 1
    assert len(c_wp.enabled_channels) == 1

def test_step_forward(c_wp):
    c_wp.rotate(90)
    orig_pos = c_wp.getpos()
    c_wp.step_forward(10)
    assert c_wp.getpos() == orig_pos + 10

def test_step_backward(c_wp):
    c_wp.rotate(90)
    orig_pos = c_wp.getpos()
    c_wp.step_backward(10)
    assert c_wp.getpos() == orig_pos - 10

def test_invalid_steps_backward(c_wp):
    with pytest.raises(WaveplateInvalidStepsError):
        c_wp.step_backward(1)

def test_invalid_steps_forward(c_wp):
    with pytest.raises(WaveplateInvalidStepsError):
        c_wp.step_forward(c_wp.max_steps + 1)

def test_rotate_relative(c_wp):
    c_wp.rotate(90)
    orig_pos = c_wp.getpos()
    c_wp.rotate_relative(10)
    assert c_wp.getpos() == orig_pos + 10 * c_wp.resolution

def test_custom_home(c_wp):
    c_wp.custom_home(45)
    assert c_wp.getpos() == 45 * c_wp.resolution
    c_wp.custom_rotate(45)
    assert c_wp.getpos() == 90 * c_wp.resolution
