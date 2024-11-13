import pint
import pytest

from pnpq.units import ureg


@pytest.fixture(name="custom_ureg")
def ureg_fixture() -> pint.UnitRegistry:
    return ureg


def test_mpc320_step_conversion(custom_ureg: pint.UnitRegistry) -> None:

    for value in [-100, 0, 100]:  # Test few values

        pint_degree = (value * custom_ureg.mpc320_step).to("degrees").magnitude
        decimal_degree = value * (170 / 1370)

        assert pint_degree == pytest.approx(decimal_degree)

        pint_mpc320_step = (value * custom_ureg.degree).to("mpc320_step").magnitude
        decimal_mpc_320_step = value / (170 / 1370)

        assert pint_mpc320_step == pytest.approx(decimal_mpc_320_step)


def test_mpc320_velocity_conversion(custom_ureg: pint.UnitRegistry) -> None:

    velocity = 200 * custom_ureg("degree / second")
    assert 50 == pytest.approx(velocity.to("mpc320_velocity").magnitude)

    proportion = 50 * custom_ureg.mpc320_velocity
    assert 200 == pytest.approx(proportion.to("degree / second").magnitude)

    velocity = 300 * custom_ureg("degree / second")
    assert 75 == pytest.approx(velocity.to("mpc320_velocity").magnitude)

    proportion = 75 * custom_ureg.mpc320_velocity
    assert 300 == pytest.approx(proportion.to("degree / second").magnitude)
