import pint

ureg = pint.UnitRegistry()

# Custom unit definitions
ureg.define("mpc320_step = (170 / 1370) degree")  # MPC320
