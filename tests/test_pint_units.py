import pytest

from pnpq.units import ureg


def test_mpc320_step_conversion() -> None:

    for value in [-100, 0, 100]:  # Test few values

        pint_degree = (value * ureg.mpc320_step).to("degrees").magnitude
        decimal_degree = value * (170 / 1370)

        assert pint_degree == pytest.approx(decimal_degree)

        pint_mpc320_step = (value * ureg.degree).to("mpc320_step").magnitude
        decimal_mpc_320_step = value / (170 / 1370)

        assert pint_mpc320_step == pytest.approx(decimal_mpc_320_step)


def test_mpc320_velocity_conversion() -> None:

    velocity = 200 * ureg("degree / second")
    proportion = velocity.to("mpc320_velocity")
    assert 50 == pytest.approx(proportion.magnitude)
    assert "mpc320_velocity" == proportion.units

    proportion = 50 * ureg.mpc320_velocity
    velocity = proportion.to("degree / second")
    assert 200 == pytest.approx(velocity.magnitude)
    assert "degree / second" == velocity.units

    velocity = 300 * ureg("degree / second")
    proportion = velocity.to("mpc320_velocity")
    assert 75 == pytest.approx(proportion.magnitude)
    assert "mpc320_velocity" == proportion.units

    proportion = 75 * ureg.mpc320_velocity
    velocity = proportion.to("degree / second")
    assert 300 == pytest.approx(velocity.magnitude)
    assert "degree / second" == velocity.units
