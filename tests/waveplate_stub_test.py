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
        arg = ",".join(["1"] * argc)
        eval(f"wp.{f}({arg})")

@pytest.fixture
def connected_waveplate():
    wp = WaveplateStub()
    wp.connect()
    return wp

def test_identify(connected_waveplate):
    connected_waveplate.identify()

def test_home(connected_waveplate):
    connected_waveplate.rotate(90)
    connected_waveplate.home()
    assert connected_waveplate.getpos() == 0

def test_rotate(connected_waveplate):
    connected_waveplate.rotate(90)
    assert connected_waveplate.getpos() == 90 * connected_waveplate.resolution

def test_rotate_invalid_degree(connected_waveplate):
    with pytest.raises(WaveplateInvalidDegreeError):
        connected_waveplate.rotate(361)

def test_disable_and_enable_channels(connected_waveplate):
    connected_waveplate.disable_channel(1)
    connected_waveplate.rotate(90)
    # Should not move
    assert connected_waveplate.getpos() == 0
    connected_waveplate.enable_channel(1)
    connected_waveplate.rotate(90)
    assert connected_waveplate.getpos() == 90 * connected_waveplate.resolution

def test_disable_invalid_channel(connected_waveplate):
    with pytest.raises(WaveplateInvalidMotorChannelError):
        # Waveplates has max channel of 1
        connected_waveplate.disable_channel(2)

def test_enable_duplicate_channel(connected_waveplate):
    connected_waveplate.disable_channel(1)
    connected_waveplate.enable_channel(1)
    connected_waveplate.enable_channel(1)
    # Make sure there is only one channel 1
    assert len(connected_waveplate.enabled_channels) == 1

def test_step_forward(connected_waveplate):
    connected_waveplate.rotate(90)
    original_position = connected_waveplate.getpos()
    connected_waveplate.step_forward(10)
    assert connected_waveplate.getpos() == original_position + 10

def test_step_backward(connected_waveplate):
    connected_waveplate.rotate(90)
    original_position = connected_waveplate.getpos()
    connected_waveplate.step_backward(10)
    assert connected_waveplate.getpos() == original_position - 10

def test_invalid_steps_backward(connected_waveplate):
    with pytest.raises(WaveplateInvalidStepsError):
        connected_waveplate.step_backward(1)

def test_invalid_steps_forward(connected_waveplate):
    with pytest.raises(WaveplateInvalidStepsError):
        connected_waveplate.step_forward(connected_waveplate.max_steps + 1)

def test_rotate_relative(connected_waveplate):
    connected_waveplate.rotate(90)
    original_position = connected_waveplate.getpos()
    connected_waveplate.rotate_relative(10)
    assert connected_waveplate.getpos() == original_position + 10 * connected_waveplate.resolution

def test_custom_home(connected_waveplate):
    connected_waveplate.custom_home(45)
    assert connected_waveplate.getpos() == 45 * connected_waveplate.resolution
    connected_waveplate.custom_rotate(45)
    assert connected_waveplate.getpos() == 90 * connected_waveplate.resolution
