from math import pi

import pytest
from pint import Quantity

from pnpq.units import pnpq_ureg


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

    angle = (test_mpc320_step * pnpq_ureg.mpc320_step).to("degrees").magnitude
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

    mpc320_step = (test_angle * pnpq_ureg.degree).to("mpc320_step").magnitude
    assert mpc320_step == pytest.approx(expected_mpc320_step)


# Test that [angle] / second quantities accurately convert into mpc320_velocity quantities
@pytest.mark.parametrize(
    "angular_velocity, unit, mpc320_velocity",
    [
        (200, pnpq_ureg("degree / second"), 50),
        (300, pnpq_ureg("degree / second"), 75),
        (201, pnpq_ureg("degree / second"), 50),
        (299, pnpq_ureg("degree / second"), 75),
        (200 * (pi / 180), pnpq_ureg("radian / second"), 50),
        (300 * (pi / 180), pnpq_ureg("radian / second"), 75),
        (201 * (pi / 180), pnpq_ureg("radian / second"), 50),
        (299 * (pi / 180), pnpq_ureg("radian / second"), 75),
        (200 / (170 / 1370), pnpq_ureg("mpc320_step / second"), 50),
        (300 / (170 / 1370), pnpq_ureg("mpc320_step / second"), 75),
    ],
)
def test_to_mpc320_velocity_conversion(
    angular_velocity: float, unit: Quantity, mpc320_velocity: float
) -> None:

    velocity = angular_velocity * unit
    proportion = velocity.to("mpc320_velocity")
    assert mpc320_velocity == pytest.approx(proportion.magnitude)
    assert "mpc320_velocity" == proportion.units


# Test that mpc320_velocity quantities accurately convert back into [angle] / second quantities
@pytest.mark.parametrize(
    "angular_velocity, unit, mpc320_velocity",
    [
        (200, pnpq_ureg("degree / second"), 50),
        (300, pnpq_ureg("degree / second"), 75),
        (200 * (pi / 180), pnpq_ureg("radian / second"), 50),
        (300 * (pi / 180), pnpq_ureg("radian / second"), 75),
        (200 / (170 / 1370), pnpq_ureg("mpc320_step / second"), 50),
        (300 / (170 / 1370), pnpq_ureg("mpc320_step / second"), 75),
    ],
)
def test_from_mpc320_velocity_conversion(
    angular_velocity: float, unit: Quantity, mpc320_velocity: float
) -> None:

    proportion = mpc320_velocity * pnpq_ureg.mpc320_velocity
    velocity = proportion.to(unit)
    assert angular_velocity == pytest.approx(velocity.magnitude)
    assert unit.units == velocity.units


def test_to_mpc320_velocity_out_of_bounds() -> None:

    with pytest.raises(ValueError, match="Rounded mpc320_velocity .* is out of range"):
        velocity = 5 * (pnpq_ureg.degree / pnpq_ureg.second)  # Too low
        velocity.to(pnpq_ureg.mpc320_velocity)

    with pytest.raises(ValueError, match="Rounded mpc320_velocity .* is out of range"):
        velocity = 450 * (pnpq_ureg.degree / pnpq_ureg.second)  # Too high
        velocity.to(pnpq_ureg.mpc320_velocity)
