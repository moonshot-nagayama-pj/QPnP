from pnpq.devices.waveplate_stub import WaveplateStub
from pnpq.errors import (
    DeviceDisconnectedError,
    WaveplateInvalidDegreeError,
    WaveplateInvalidMotorChannelError,
    WaveplateInvalidStepsError,
)
import pytest

def test_access_without_connection():
    wp = WaveplateStub()
    with pytest.raises(DeviceDisconnectedError):
        wp.identify()

def test_connect():
    wp = WaveplateStub()
    wp.connect()
    wp.identify()

def test_home():
    wp = WaveplateStub()
    wp.connect()
    wp.rotate(90)
    wp.home()
    pos = wp.getpos()
    assert pos == 0

def test_rotate():
    wp = WaveplateStub()
    wp.connect()
    wp.rotate(90)
    pos = wp.getpos()
    res = wp.resolution
    assert pos == 90*res

def test_rotate_invalid_degree():
    wp = WaveplateStub()
    wp.connect()
    with pytest.raises(WaveplateInvalidDegreeError):
        wp.rotate(361)

def test_disable_and_enable_channels():
    wp = WaveplateStub()
    wp.connect()
    wp.disable_channel(1)
    wp.rotate(90)
    # Should not move
    pos = wp.getpos()
    assert pos == 0
    wp.enable_channel(1)
    wp.rotate(90)
    pos = wp.getpos()
    res = wp.resolution
    assert pos == 90*res

def test_disable_invalid_channel():
    wp = WaveplateStub()
    wp.connect()
    with pytest.raises(WaveplateInvalidMotorChannelError):
        # Waveplates has max channel of 1
        wp.disable_channel(2)

def test_enable_duplicate_channel():
    wp = WaveplateStub()
    wp.connect()
    wp.disable_channel(1)
    wp.enable_channel(1)
    wp.enable_channel(1)
    # Make sure there is only one channel 1
    assert len(wp.enabled_channels) == 1

def test_step_forward_backward():
    wp = WaveplateStub()
    wp.connect()
    wp.rotate(90)
    pos = wp.getpos()
    wp.step_forward(10)
    newPos = wp.getpos()
    assert newPos == pos + 10
    wp.step_backward(10)
    newPos = wp.getpos()
    assert newPos == pos

def test_invalid_steps():
    wp = WaveplateStub()
    wp.connect()
    with pytest.raises(WaveplateInvalidStepsError):
        wp.step_backward(1)
        wp.step_forward(wp.max_steps + 1)

def test_rotate_relative():
    wp = WaveplateStub()
    wp.connect()
    wp.rotate(90)
    pos = wp.getpos()
    wp.rotate_relative(10)
    newPos = wp.getpos()
    assert newPos == pos + 10*wp.resolution

def test_custom_home():
    wp = WaveplateStub()
    wp.connect()
    wp.custom_home(45)
    pos = wp.getpos()
    assert pos == 45*wp.resolution
    wp.custom_rotate(45)
    pos = wp.getpos()
    assert pos == 90*wp.resolution
