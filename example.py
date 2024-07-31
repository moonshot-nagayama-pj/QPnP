from pnpq import Waveplate
from pnpq import Switch
from pnpq import OdlThorlabs
from pnpq import OdlOzOptics
from pnpq.devices.optical_delay_line import OpticalDelayLine
import logging

logging.basicConfig(level=logging.DEBUG)

print("hello world")
# wp = Waveplate(serial_number='00AAABBB')
# wp = Waveplate()
# wp.connect()
# print(Waveplate())

# print(Switch())
# sw = Switch()


# print(OpticalDelayLine("/dev/test"))
# print(OdlThorlabs())
# tlodl = OdlThorlabs("/dev/ttyUSB0")
# tlodl = OdlThorlabs(serial_number="28252054")
# tlodl.connect()


print(OdlOzOptics)
oz = OdlOzOptics(serial_number="CKBEe12CJ06")
oz.home()
oz.move(20)

oz.get_step()
oz.move(49.9)
oz.get_step()
oz.move(0)
oz.get_step()
oz.set_step(1200)
oz.get_step()
