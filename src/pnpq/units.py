import pint

ureg = pint.UnitRegistry()

# Initialize the UnitRegistry
ureg = pint.UnitRegistry()

# Custom unit definitions for MPC320
ureg.define("mpc320_step = (170 / 1370) degree")
ureg.define("mpc320_max_velocity = 400 degree / second")
ureg.define("mpc320_velocity = []")

context = pint.Context("mpc320_proportional_velocity")

context.add_transformation(
    "degree / second",
    "mpc320_velocity",
    lambda ureg, value, **kwargs: value / ureg.mpc320_max_velocity * 100,
)

context.add_transformation(
    "mpc320_velocity",
    "degree / second",
    lambda ureg, value, **kwargs: value * ureg.mpc320_max_velocity / 100,
)

ureg.add_context(context)
ureg.enable_contexts("mpc320_proportional_velocity")
