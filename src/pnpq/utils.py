from serial.tools.list_ports import comports as list_comports
import logging

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
