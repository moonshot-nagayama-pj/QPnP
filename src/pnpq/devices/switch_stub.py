import structlog

from pnpq.errors import DeviceDisconnectedError

from ..events import Event


class Switch:
    """Stub Switch Device Class"""

    log = structlog.get_logger()

    def __init__(self) -> None:
        # Stub Serial Number
        # TODO: Custom serial number from initializer
        self.device_sn: str = "stubswitch"

        # Is connected to the device (used internally)
        self.connected: bool = False

        # State of the optical switch
        # 1 is bar state, 2 is cross state. These are the numbers used to represent these states in the Thorlabs Optical Switch 1310E driver.
        self.state: int = 1

    def __ensure_port_open(self) -> None:
        if not self.connected:
            self.log.error(event=Event.DEVICE_NOT_CONNECTED_ERROR)
            raise DeviceDisconnectedError(f"{self} is disconnected")

    def connect(self) -> None:
        """Establish connection to the device"""
        self.connected = True
        self.log.debug("Stub Waveplate Connected")

    def bar_state(self) -> None:
        """Sets the optical switch's state to 1 (bar state)"""
        self.__ensure_port_open()
        self.state = 1
        self.log.info(event=Event.SWITCH_BAR_STATE)

    def cross(self) -> None:
        """Sets the optical switch's state to 2 (cross state)"""
        self.__ensure_port_open()
        self.state = 2
        self.log.info(event=Event.SWITCH_CROSS_STATE)
