from pnpq.units import pnpq_ureg

# test = 169 * pnpq_ureg.degree
test = (169 * pnpq_ureg.degree)#.to("mpc320_step").magnitude
print(test)

test_radians = test.to("radian")
print(test_radians)

print('mpc320_step' in pnpq_ureg)

test_mpc320_steps = test.to("mpc320_steps")
print(test_mpc320_steps)

print(test_mpc320_steps.magnitude)
print(type(test_mpc320_steps.magnitude))
