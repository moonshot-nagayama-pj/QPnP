import pytest
from pint import DimensionalityError

from pnpq.apt.connection import AptConnection
from pnpq.apt.protocol import ChanIdent, JogDirection
from pnpq.devices.polarization_controller_thorlabs_mpc320 import (
    PolarizationControllerThorlabsMPC320,
)
from pnpq.units import pnpq_ureg


@pytest.fixture(name="device", scope="module")
def device_fixture() -> PolarizationControllerThorlabsMPC320:
    connection = AptConnection(serial_number="38454784")
    return PolarizationControllerThorlabsMPC320(connection=connection)


# def test_check_status(device: PolarizationControllerThorlabsMPC320) -> None:
#    device.check_status()


def test_move_absolute(device: PolarizationControllerThorlabsMPC320) -> None:
    device.identify(ChanIdent.CHANNEL_1)

    device.home(ChanIdent.CHANNEL_1)
    device.home(ChanIdent.CHANNEL_2)
    device.home(ChanIdent.CHANNEL_3)

    device.move_absolute(ChanIdent.CHANNEL_1, 160 * pnpq_ureg.degree)
    device.move_absolute(ChanIdent.CHANNEL_2, 160 * pnpq_ureg.degree)
    device.move_absolute(ChanIdent.CHANNEL_3, 160 * pnpq_ureg.degree)

    # device.move_absolute(ChanIdent.CHANNEL_2, 30 * pnpq_ureg.degree)
    # device.move_absolute(ChanIdent.CHANNEL_1, 90 * pnpq_ureg.degree)
    # device.move_absolute(ChanIdent.CHANNEL_3, 90 * pnpq_ureg.degree)

    # device.move_absolute(ChanIdent.CHANNEL_3, 165 * pnpq_ureg.degree)
    # device.move_absolute(ChanIdent.CHANNEL_2, 90 * pnpq_ureg.degree)
    # device.move_absolute(ChanIdent.CHANNEL_1, 0 * pnpq_ureg.degree)

    # device.move_absolute(ChanIdent.CHANNEL_1, 10 * pnpq_ureg.degree)
    # device.move_absolute(ChanIdent.CHANNEL_1, 100 * pnpq_ureg.degree)
    # device.move_absolute(ChanIdent.CHANNEL_1, 50 * pnpq_ureg.degree)

    device.home(ChanIdent.CHANNEL_1)
    device.home(ChanIdent.CHANNEL_2)
    device.home(ChanIdent.CHANNEL_3)

    # One of the channels on our test device appears to forget to turn
    # off its motor when it's homed or set to 0 degrees. It just sits
    # there vibrating and whining. It's not really safe to leave the
    # device at degree 0 for this reason. 170 also seems too far (160 seems about the safest)
    # device.move_absolute(ChanIdent.CHANNEL_1, 10 * pnpq_ureg.degree)
    # device.move_absolute(ChanIdent.CHANNEL_2, 10 * pnpq_ureg.degree)
    # device.move_absolute(ChanIdent.CHANNEL_3, 10 * pnpq_ureg.degree)

    # device.set_params(home_position=1000)

    # device.home(ChanIdent.CHANNEL_1)
    # device.home(ChanIdent.CHANNEL_2)
    # device.home(ChanIdent.CHANNEL_3)

    # device.move_absolute(ChanIdent.CHANNEL_1, 10 * pnpq_ureg.degree)
    # device.move_absolute(ChanIdent.CHANNEL_2, 10 * pnpq_ureg.degree)
    # device.move_absolute(ChanIdent.CHANNEL_3, 10 * pnpq_ureg.degree)

    # device.set_params(home_position=0 * pnpq_ureg.degree)

    # device.home(ChanIdent.CHANNEL_1)
    # device.home(ChanIdent.CHANNEL_2)
    # device.home(ChanIdent.CHANNEL_3)

    # device.move_absolute(ChanIdent.CHANNEL_1, 0 * pnpq_ureg.degree)
    # device.move_absolute(ChanIdent.CHANNEL_2, 0 * pnpq_ureg.degree)
    # device.move_absolute(ChanIdent.CHANNEL_3, 0 * pnpq_ureg.degree)


def test_jog(device: PolarizationControllerThorlabsMPC320) -> None:

    params = device.get_params()
    old_jog_step_1 = params["jog_step_1"]
    old_jog_step_2 = params["jog_step_2"]
    old_jog_step_3 = params["jog_step_3"]

    device.home(ChanIdent.CHANNEL_1)
    device.home(ChanIdent.CHANNEL_2)
    device.home(ChanIdent.CHANNEL_3)

    jog_step = 50 * pnpq_ureg.mpc320_step
    jog_count = 5

    device.set_params(jog_step_1=jog_step, jog_step_2=jog_step, jog_step_3=jog_step)

    # Home should be set to 0 for this test to work
    # device.set_params(home_position=0*pnpq_ureg.degree)

    try:
        for _ in range(jog_count):
            device.jog(ChanIdent.CHANNEL_1, JogDirection.FORWARD)
            device.jog(ChanIdent.CHANNEL_2, JogDirection.FORWARD)
            device.jog(ChanIdent.CHANNEL_3, JogDirection.FORWARD)
    finally:
        device.set_params(
            jog_step_1=old_jog_step_1,
            jog_step_2=old_jog_step_2,
            jog_step_3=old_jog_step_3,
        )

    # Validate that we jogged to the expected position.
    # If we are at the correct position, this move_absolute command should not cause the device to move.
    device.move_absolute(ChanIdent.CHANNEL_1, jog_count * jog_step)
    device.move_absolute(ChanIdent.CHANNEL_2, jog_count * jog_step)
    device.move_absolute(ChanIdent.CHANNEL_3, jog_count * jog_step)


def test_invalid_angle_inputs(device: PolarizationControllerThorlabsMPC320) -> None:
    device.identify(ChanIdent.CHANNEL_1)

    with pytest.raises(ValueError):
        device.move_absolute(ChanIdent.CHANNEL_1, 171 * pnpq_ureg.degree)
        device.move_absolute(ChanIdent.CHANNEL_1, -1 * pnpq_ureg.degree)

    with pytest.raises(DimensionalityError):
        device.move_absolute(ChanIdent.CHANNEL_1, 1 * pnpq_ureg.meter)


def test_set_params(device: PolarizationControllerThorlabsMPC320) -> None:
    device.identify(ChanIdent.CHANNEL_1)

    device.home(ChanIdent.CHANNEL_1)
    device.home(ChanIdent.CHANNEL_2)
    device.home(ChanIdent.CHANNEL_3)

    # Set a custom home position
    params = device.get_params()
    params["home_position"] = 100 * pnpq_ureg.degree
    device.set_params(**params)

    device.home(ChanIdent.CHANNEL_1)
    device.home(ChanIdent.CHANNEL_2)
    device.home(ChanIdent.CHANNEL_3)

    # Reset the home position
    params = device.get_params()
    params["home_position"] = 0 * pnpq_ureg.degree
    device.set_params(**params)

    device.home(ChanIdent.CHANNEL_1)
    device.home(ChanIdent.CHANNEL_2)
    device.home(ChanIdent.CHANNEL_3)
