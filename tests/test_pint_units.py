import pytest
from pint import Quantity

from pnpq.units import pnpq_ureg


@pytest.mark.parametrize(
    "test_mpc320_step, expected_angle",
    [
        (-1370, -170),
        (0, 0),
        (1370, 170),
    ],
)
def test_mpc320_step_to_angle_conversion(
    test_mpc320_step: float, expected_angle: float
) -> None:

    angle = (test_mpc320_step * pnpq_ureg.mpc320_step).to("degrees").magnitude
    assert angle == pytest.approx(expected_angle)


@pytest.mark.parametrize(
    "test_angle, expected_mpc320_step",
    [
        (-170, -1370),
        (0, 0),
        (170, 1370),
        (169, 1362),  # This will be able to test the actual rounding
    ],
)
def test_angle_to_mpc320_step_conversion(
    test_angle: float, expected_mpc320_step: float
) -> None:

    mpc320_step = (test_angle * pnpq_ureg.degree).to("mpc320_step").magnitude
    assert mpc320_step == expected_mpc320_step


# Test that [angle] / second quantities accurately convert into mpc320_velocity quantities
@pytest.mark.parametrize(
    "angular_velocity, mpc320_velocity",
    [
        (200 * pnpq_ureg("degree / second"), 50),
        (300 * pnpq_ureg("degree / second"), 75),
        (201 * pnpq_ureg("degree / second"), 50),
        (299 * pnpq_ureg("degree / second"), 75),
        (3.49065850399 * pnpq_ureg("radian / second"), 50),
        (5.23598775598 * pnpq_ureg("radian / second"), 75),
        (3.50811179651 * pnpq_ureg("radian / second"), 50),
        (5.21853446346 * pnpq_ureg("radian / second"), 75),
        (1611.76470588 * pnpq_ureg("mpc320_step / second"), 50),
        (2417.64705882 * pnpq_ureg("mpc320_step / second"), 75),
    ],
)
def test_to_mpc320_velocity_conversion(
    angular_velocity: Quantity, mpc320_velocity: float
) -> None:

    proportion = angular_velocity.to("mpc320_velocity")
    assert mpc320_velocity == proportion.magnitude
    assert "mpc320_velocity" == proportion.units


# Test that mpc320_velocity quantities accurately convert back into [angle] / second quantities
@pytest.mark.parametrize(
    "mpc320_velocity, angular_velocity",
    [
        (50, 200 * pnpq_ureg("degree / second")),
        (75, 300 * pnpq_ureg("degree / second")),
        (50, 3.49065850399 * pnpq_ureg("radian / second")),
        (75, 5.23598775598 * pnpq_ureg("radian / second")),
        (50, 1611.76470588 * pnpq_ureg("mpc320_step / second")),
        (75, 2417.64705882 * pnpq_ureg("mpc320_step / second")),
    ],
)
def test_from_mpc320_velocity_conversion(
    mpc320_velocity: float, angular_velocity: Quantity
) -> None:

    proportion = mpc320_velocity * pnpq_ureg.mpc320_velocity
    velocity = proportion.to(angular_velocity.units)
    assert angular_velocity.magnitude == pytest.approx(velocity.magnitude)
    assert angular_velocity.units == velocity.units


@pytest.mark.parametrize(
    "velocity",
    [
        5 * (pnpq_ureg.degree / pnpq_ureg.second),  # Too low
        450 * (pnpq_ureg.degree / pnpq_ureg.second),  # Too high
    ],
)
def test_to_mpc320_velocity_out_of_bounds(velocity: Quantity) -> None:
    with pytest.raises(ValueError, match="Rounded mpc320_velocity .* is out of range"):
        velocity.to(pnpq_ureg.mpc320_velocity)
