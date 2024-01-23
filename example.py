from pnpq import Waveplate
from pnpq import Switch
from pnpq import OdlThorlabs
from pnpq import OdlOzOptics
from pnpq.devices.optical_delay_line import OpticalDelayLine

print("hello world")
# wp = Waveplate(serial_number='00AAABBB')
# wp = Waveplate()
# wp.connect()
print(Waveplate())

print(Switch())
# sw = Switch()

print(OpticalDelayLine("/dev/test"))
# print(OdlThorlabs())
tlodl = OdlThorlabs("/dev/test2")
# tlodl.connect()


print(OdlOzOptics)
# oz = OdlOzOptics(serial_number='CKBEe12CJ06')
# oz.connect()
