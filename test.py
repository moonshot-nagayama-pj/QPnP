from pnpq.units import pnpq_ureg

# test = 169 * pnpq_ureg.degree
test = (169 * pnpq_ureg.degree)
print(test)

test_mpc320_steps = test.to("mpc320_step")
print(test_mpc320_steps)

print(test_mpc320_steps.magnitude)
print(type(test_mpc320_steps.magnitude))

# test_radians = test.to("radian")
# print(test_radians)

print('mpc320_step' in pnpq_ureg)

back_to_degrees = test_mpc320_steps.to("degree")
back_to_radians = test_mpc320_steps.to("radian")
print(back_to_degrees)
print(back_to_radians)

test_velocity = 200 * pnpq_ureg("degree / second")
print(test_velocity)
mpc320_velocity = test_velocity.to("mpc320_velocity")
print(mpc320_velocity)
back_to_velocity = mpc320_velocity.to("degree / second")
print(back_to_velocity)
to_mpc_step_speed = mpc320_velocity.to("mpc320_step / second")
print(to_mpc_step_speed)
back_to_velocity = to_mpc_step_speed.to("mpc320_velocity")
print(back_to_velocity)


