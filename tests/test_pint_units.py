import pytest

from pnpq.units import ureg


@pytest.mark.parametrize(
    "test_mpc320_step, expected_angle",
    [
        (-100, -100 * (170 / 1370)),
        (0, 0),
        (100, 100 * (170 / 1370)),
    ],
)
def test_mpc320_step_to_angle_conversion(
    test_mpc320_step: float, expected_angle: float
) -> None:

    angle = (test_mpc320_step * ureg.mpc320_step).to("degrees").magnitude
    assert angle == pytest.approx(expected_angle)


@pytest.mark.parametrize(
    "test_angle, expected_mpc320_step",
    [
        (-100, -100 / (170 / 1370)),
        (0, 0),
        (100, 100 / (170 / 1370)),
    ],
)
def test_angle_to_mpc320_step_conversion(
    test_angle: float, expected_mpc320_step: float
) -> None:

    mpc320_step = (test_angle * ureg.degree).to("mpc320_step").magnitude
    assert mpc320_step == pytest.approx(expected_mpc320_step)


@pytest.mark.parametrize(
    "deg_per_sec_velocity, mpc320_velocity",
    [
        (200, 50),
        (300, 75),
    ],
)
def test_mpc320_velocity_conversion(
    deg_per_sec_velocity: float, mpc320_velocity: float
) -> None:

    # Test that degrees / second quantities accurately convert into mpc320_velocity quantities
    velocity = deg_per_sec_velocity * ureg("degree / second")
    proportion = velocity.to("mpc320_velocity")
    assert mpc320_velocity == pytest.approx(proportion.magnitude)
    assert "mpc320_velocity" == proportion.units

    # Test that mpc320_velocity quantities accurately convert back into degrees / second quantities
    proportion = mpc320_velocity * ureg.mpc320_velocity
    velocity = proportion.to("degree / second")
    assert deg_per_sec_velocity == pytest.approx(velocity.magnitude)
    assert "degree / second" == velocity.units
