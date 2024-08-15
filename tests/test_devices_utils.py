import pnpq.devices.utils as utils


def test_get_available_port_no_available_ports():
    assert utils.get_available_port("ABC") is None


def test_usb_hub_connected_no_hubs():
    assert not utils.check_usb_hub_connected()
