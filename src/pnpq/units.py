import pint
from pint import Quantity
from typing import cast

ureg = pint.UnitRegistry()

# Custom unit definitions for MPC320
ureg.define("mpc320_step = (170 / 1370) degree")

# According to the protocol, velocity is expressed as a percentage of the maximum speed, ranging from 10% to 100%.
# The maximum velocity is defined as 400 degrees per second, so we store velocity as a dimensionless proportion of this value.
# Thus, the unit for mpc_velocity will be set as dimensionless.
# A transformation function (defined below) will convert other units, like degrees per second, into this proportional form.
ureg.define("mpc320_velocity = []")


context = pint.Context("mpc320_proportional_velocity")

mpc320_max_velocity = 400 * (ureg.degree / ureg.second)


context.add_transformation(
    "degree / second",
    "mpc320_velocity",
    lambda ureg, value, **kwargs: (value / mpc320_max_velocity) * 100, # Convert value to percent
)

context.add_transformation(
    "mpc320_velocity",
    "degree / second",
    lambda ureg, value, **kwargs: (value * mpc320_max_velocity) / 100, # Convert value from percent
)

ureg.add_context(context)
ureg.enable_contexts("mpc320_proportional_velocity")
