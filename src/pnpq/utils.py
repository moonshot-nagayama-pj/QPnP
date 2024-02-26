from serial.tools.list_ports import comports as list_comports
import logging
import subprocess
import os

logger = logging.getLogger("utils")

USB_HUB_PID = {"2109:0817", "2109:2817"}

# USB_HUB_iVENDOR = 0x2109
# USB_HUB_iPRODUCT = [0x0817, 0x2817]


def get_available_port(device_serial_number: str) -> str | None:
    logger.debug(f"get_available_port(serial_number: {device_serial_number})")
    available_ports = list_comports()
    for port in available_ports:
        logger.debug(f"port: {port.device}")
        if port.serial_number == device_serial_number:
            logger.debug(f"port found: {port.device}")
            return port.device
    return None


def check_usb_hub_connected() -> bool | None:
    logger.debug(f"check_usb_hub_connected")

    lsusb_result = subprocess.run(
        ["lsusb"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    if lsusb_result.returncode is not 0:
        logger.error("can not execute lsusb to find USB hub")

    else:
        usb_devices = [
            line.strip() for line in lsusb_result.stdout.split("\n") if line.strip()
        ]
        for device in usb_devices:
            device_parts = device.split()
            if len(device_parts) >= 5:
                pid = device_parts[5]
                if pid in USB_HUB_PID:
                    logger.debug(f"USB Hub found PID {pid}")
                    return True
        return False
