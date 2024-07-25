from pnpq import Waveplate
from pnpq import Switch
from pnpq import OdlThorlabs
from pnpq import OdlOzOptics
from pnpq.devices.optical_delay_line import OpticalDelayLine
import logging

logging.basicConfig(level=logging.DEBUG)
print("Check OzOptics Odl")
# wp = Waveplate(serial_number='00AAABBB')
# wp = Waveplate()
# wp.connect()
# print(Waveplate())

# print(Switch())
# sw = Switch()


# print(OpticalDelayLine("/dev/test"))
# print(OdlThorlabs())
# tlodl = OdlThorlabs("/dev/ttyUSB0")
ozodl = OdlOzOptics(serial_number="CKBEe12CJ06")
ozodl.reconnect()

ozodl.home()

ozodl.move(20)
ozodl.get_step()

ozodl.home()
ozodl.get_step()

print(OdlOzOptics)
# oz = OdlOzOptics(serial_number='CKBEe12CJ06')
# oz.connect()
