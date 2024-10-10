import logging
import time
from contextlib import contextmanager
from typing import Callable, Iterator

from serial.tools.list_ports import comports as list_comports

logger = logging.getLogger("utils")


AVAILABLE_USB_HUBS: list[tuple[str, str]] = [
    ("2109", "0817"),  # USB3.0 HUB
    ("2109", "2817"),  # USB2.0 HUB
]


def get_available_port(device_serial_number: str) -> str | None:
    logger.debug("get_available_port(serial_number: %s)", device_serial_number)
    available_ports = list_comports()
    for port in available_ports:
        if port.serial_number == device_serial_number:
            logger.debug("port found: %s", port.device)
            return str(port.device)
    return None


def check_usb_hub_connected() -> bool:
    logger.debug("check_usb_hub_connected")
    available_ports = list_comports()
    for port in available_ports:
        pair_tuple = (port.vid, port.pid)
        if pair_tuple in AVAILABLE_USB_HUBS:
            logger.debug("compatible USB HUB %s is found", port)
            return True
    return False


class TimeoutException(Exception):
    pass


@contextmanager
def timeout(timeout_seconds: float) -> Iterator[Callable[[], bool]]:
    """Context manager that yields a function that returns True if the
    timeout has not been exceeded and throws TimeoutException
    otherwise, making it suitable for use in loops.

    timeout_seconds: float length of timeout, in seconds
    """
    deadline = time.perf_counter() + timeout_seconds

    def check_timeout() -> bool:
        if time.perf_counter() < deadline:
            return True
        raise TimeoutException()

    yield check_timeout
