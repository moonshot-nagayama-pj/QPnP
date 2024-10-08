from pnpq.devices import utils


def test_get_available_port_no_available_ports() -> None:
    assert utils.get_available_port("ABC") is None


def test_usb_hub_connected_no_hubs() -> None:
    assert not utils.check_usb_hub_connected()
