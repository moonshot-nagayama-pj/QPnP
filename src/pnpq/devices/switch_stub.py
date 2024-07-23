import logging

from pnpq.errors import (
    DeviceDisconnectedError,
)

class Switch:
    """Stub Switch Device Class"""

    def __init__(self) -> None:
        # Stub Serial Number
        # TODO: Custom serial number from initializer
        self.device_sn: str = "stubswitch"

        # Is connected to the device (used internally)
        self.connected: bool = False

        # State of the optical switch
        # 1 is bar state, 2 is cross state
        self.state: int = 1

        # Logger for this class
        self.logger: logging.Logger = logging.getLogger(f"{self}")

    def __ensure_port_open(self) -> None:
        if not self.connected:
            self.logger.error("Device not connected")
            raise DeviceDisconnectedError(f"{self} is disconnected")

    def connect(self) -> None:
        """Establish connection to the device"""
        self.connected = True
        self.logger.info("Stub Waveplate Connected")

    def bar_state(self) -> None:
        """Sets the optical switch's state to 1 (bar state)"""
        self.__ensure_port_open()
        self.state = 1

    def cross(self) -> None:
        """Sets the optical switch's state to 2 (cross state)"""
        self.__ensure_port_open()
        self.state = 2
