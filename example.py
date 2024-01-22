from pnpq import Waveplate
from pnpq import Switch
from pnpq import OdlThorlabs
from pnpq import OdlOzOptics

print("hello world")
wp = Waveplate(serial_number='00AAABBB')
wp.connect()
print(Waveplate())

print(Switch())
sw = Switch()

print(OdlThorlabs())
odl = OdlThorlabs()
odl.connect()

print(OdlOzOptics)
oz = OdlOzOptics(serial_number='CKBEe12CJ06')
oz.connect()

