from math import pi

import pytest
from pint import Quantity

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
    "angular_velocity, unit, mpc320_velocity",
    [
        (200, ureg("degree / second"), 50),
        (300, ureg("degree / second"), 75),
        (200 * (pi / 180), ureg("radian / second"), 50),
        (300 * (pi / 180), ureg("radian / second"), 75),
        (200 / (170 / 1370), ureg("mpc320_step / second"), 50),
        (300 / (170 / 1370), ureg("mpc320_step / second"), 75),
    ],
)
def test_to_mpc320_velocity_conversion(
    angular_velocity: float, unit: Quantity, mpc320_velocity: float
) -> None:

    # Test that [angle] / second quantities accurately convert into mpc320_velocity quantities
    velocity = angular_velocity * unit
    proportion = velocity.to("mpc320_velocity")
    assert mpc320_velocity == pytest.approx(proportion.magnitude)
    assert "mpc320_velocity" == proportion.units


@pytest.mark.parametrize(
    "angular_velocity, unit, mpc320_velocity",
    [
        (200, ureg("degree / second"), 50),
        (300, ureg("degree / second"), 75),
        (200 * (pi / 180), ureg("radian / second"), 50),
        (300 * (pi / 180), ureg("radian / second"), 75),
        (200 / (170 / 1370), ureg("mpc320_step / second"), 50),
        (300 / (170 / 1370), ureg("mpc320_step / second"), 75),
    ],
)
def test_from_mpc320_velocity_conversion(
    angular_velocity: float, unit: Quantity, mpc320_velocity: float
) -> None:
    # Test that mpc320_velocity quantities accurately convert back into [angle] / second quantities
    proportion = mpc320_velocity * ureg.mpc320_velocity
    velocity = proportion.to(unit)
    assert angular_velocity == pytest.approx(velocity.magnitude)
    assert unit.units == velocity.units
