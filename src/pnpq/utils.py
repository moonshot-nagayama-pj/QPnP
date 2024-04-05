from serial.tools.list_ports import comports as list_comports
import logging
import usb

logger = logging.getLogger("utils")


def get_available_port(device_serial_number: str) -> str | None:
    logger.debug(f"get_available_port(serial_number: {device_serial_number})")
    available_ports = list_comports()
    for port in available_ports:
        logger.debug(f"port: {port.device}")
        if port.serial_number == device_serial_number:
            logger.debug(f"port found: {port.device}")
            return port.device
    return None


def check_usb_hub_connected() -> bool:
    logger.debug(f"check_usb_hub_connected")

    usb2_hub = usb.core.find(idVendor=0x2109, idProduct=0x2817)
    usb3_hub = usb.core.find(idVendor=0x2109, idProduct=0x0817)

    if usb2_hub is None and usb3_hub is None:
        logger.debug(f"usb_hub is not detected")
        return False

    else:
        logger.debug(f"usb_hub is detected")
        return True
