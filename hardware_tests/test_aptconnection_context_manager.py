

from src.pnpq.apt.connection import AptConnection
from src.pnpq.apt.protocol import ChanIdent
from src.pnpq.devices.polarization_controller_thorlabs_mpc import PolarizationControllerThorlabsMPC320


def test_aptconnection_context_manager() -> None:
    connection = AptConnection(serial_number="38454784")

    assert connection.is_closed()
    
    with connection:
        device = PolarizationControllerThorlabsMPC320(connection=connection)

        device.identify(ChanIdent.CHANNEL_1)

        device.home(ChanIdent.CHANNEL_1)
        device.home(ChanIdent.CHANNEL_2)
        device.home(ChanIdent.CHANNEL_3)

        device.move_absolute(ChanIdent.CHANNEL_1, 160 * pnpq_ureg.degree)
        device.move_absolute(ChanIdent.CHANNEL_2, 160 * pnpq_ureg.degree)
        device.move_absolute(ChanIdent.CHANNEL_3, 160 * pnpq_ureg.degree)
