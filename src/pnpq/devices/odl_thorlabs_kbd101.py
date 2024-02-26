#
# Thorlanbs ODL module driver
#       Brushless Motor Driver: KBD101
#       Stage:                  DDS100/M
#
import serial
import time, logging
from serial import Serial
from pnpq.devices.optical_delay_line import OpticalDelayLine

from pnpq.errors import (
    DevicePortNotFoundError,
    DeviceDisconnectedError,
    OdlMoveNotComepleted,
    OdlHomeNotCompleted,
    OdlGetPosNotCompleted,
    OdlMoveOutofRangeError,
)

ENABLE_CHANNEL_COMMAND = b"\x10\x02\x01\x01\x50\x01"
START_UPDATE_COMMAND = b"\x11\x00\x00\x00\x50\x01"
STOP_UPDATE_COMMAND = b"\x12\x00\x00\x00\x50\x01"
ODL_HOME_COMMAND = b"\x43\x04\x01\x00\x50\x01"
ODL_IDENTIFY_COMMAND = b"\x23\x02\x00\x00\x50\x01"
ODL_MOVE_COMMAND = b"\x53\x04\x06\x00\xd0\x01\x00\x00"
ODL_RELATIVE_MOVE_COMMAND = b"\x48\x04\x06\x00\xd0\x01\x00\x00"


class OdlThorlabs(OpticalDelayLine):
    def __init__(
        self,
        serial_port: str | None = None,
        serial_number: str | None = None,
        config_file=None,
    ):
        super().__init__(serial_port, serial_number, config_file)
        self.conn.baudrate = 115200
        self.conn.bytesize = 8
        self.conn.stopbits = 1
        self.conn.parity = "N"
        self.conn.rtscts = 1
        self.resolution = 2000
        self.home_timeout = 25
        self.move_timeout = 4
        self.auto_update = False
        self.maxmove = 100
        self.minmove = 0
        self.name = "Thorlabs"
        self.model = "KBD101 driver DDS100/M Stage"
        self.logger = logging.getLogger(f"{self}")

    def __ensure_port_open(self) -> None:
        if not self.conn.is_open:
            self.logger.error("disconnected")
            raise DeviceDisconnectedError(f"{self} is disconnected")

    def __ensure_device_in_range(self, steps: int) -> None:
        if (
            steps > self.maxmove * self.resolution
            or steps < self.minmove * self.resolution
        ):
            raise OdlMoveOutofRangeError(
                f"Move request for device{self} is out of range min({self.minmove}) - max({self.maxmove})"
            )

    def connect(self) -> None:
        if self.conn.is_open:
            self.logger.warn("ODL ({self}) serial connection is already open")
        self.conn.open()

        if not self.conn.is_open:
            raise DeviceDisconnectedError(f"ODL device is disconneced")
        self.logger.info(f"({self}): Connecting to Thorlabs ODL mdoule")
        # Enable Channel ID (0)
        self.conn.write(ENABLE_CHANNEL_COMMAND)

    def identify(self):
        self.__ensure_port_open()
        self.conn.write(ODL_IDENTIFY_COMMAND)

    def __waitForReply(self, sequence, timeout):
        retries = timeout
        result = b""
        while retries > 0:
            noReadBytes = self.conn.in_waiting

            result = self.conn.read(noReadBytes)

            self.logger.debug(
                f"ODL wait for reply: {sequence}, results: {result}, retry count: {retries}"
            )
            if noReadBytes > 0 and result.find(sequence) != -1:
                self.logger.info(f"The response found: {result} ")
                return result
            time.sleep(1)
            retries -= 1

    def move(self, move_mm: int):

        self.__ensure_port_open()
        self.__ensure_device_in_range(move_mm * self.resolution)

        msg = ODL_MOVE_COMMAND + (move_mm * self.resolution).to_bytes(
            4, byteorder="little"
        )
        self.conn.write(msg)

        move_complete = self.__waitForReply(b"\x64\04", self.move_timeout)
        if not move_complete:
            self.logger.error(f"move command is not completed")
            raise OdlMoveNotComepleted(
                f"ODL({self}): No moved_completed response has been received"
            )

    def step_forward(self, steps):
        self.__ensure_port_open()
        self.__ensure_device_in_range(steps)

        msg = ODL_RELATIVE_MOVE_COMMAND + (int(steps)).to_bytes(
            4, byteorder="little", signed=True
        )
        self.conn.write(msg)

        forward_complete = self.__waitForReply(b"\x64\x04", self.move_timeout)

        if not forward_complete:
            self.logger.error(f"step forward command is not completed")
            raise OdlMoveNotComepleted(
                f"ODL({self}: No response is received for step_forward command)"
            )

    def step_backward(self, steps):
        self.__ensure_port_open()
        self.__ensure_device_in_range(steps)

        # negate steps
        steps = -steps

        # relative move
        msg = ODL_RELATIVE_MOVE_COMMAND + (int(steps)).to_bytes(
            4, byteorder="little", signed=True
        )
        self.conn.write(msg)

        backward_complete = self.__waitForReply(b"\x64\x04", self.move_timeout)
        if not backward_complete:
            self.logger.error(f"step backward command is not completed")
            raise OdlMoveNotComepleted(
                f"ODL{self}: No response id received for step_backward command"
            )

    def getpos(self) -> int | None:
        self.logger.info("call getpos cmd")
        self.__ensure_port_open()

        # MGMSG_HW_START_UPDATEMSGS 0x0011
        self.conn.write(START_UPDATE_COMMAND)

        self.__waitForReply
        result = self.__waitForReply(b"\x81\x04", self.move_timeout)
        self.logger.debug(f"getpos all byte sequence results: {result}")

        if not self.auto_update:
            # MSMSG_HW_STOP_UPDATEMSGS 0x0012
            msg = STOP_UPDATE_COMMAND
            self.conn.write(msg)

        if result is None:
            self.logger.error("getpos command is not completed")
            raise OdlGetPosNotCompleted(
                f"ODL{self}: No update response has been received for determining the position"
            )

        else:
            pos_seq = result[8:12]
            self.logger.debug(f"getpos byte result: {pos_seq}")

            steps = int.from_bytes(pos_seq, byteorder="little")
            position = steps / self.resolution
            self.logger.info(f"getpos extracted result: pos:{position} steps:{steps}")
            return steps

    def home(self) -> bytes | None:
        self.__ensure_port_open()

        self.conn.write(ODL_HOME_COMMAND)

        homed = self.__waitForReply(b"\x44\x04", self.home_timeout)
        self.logger.debug(f"home result: {homed}")
        if homed is None:
            self.logger.error("home command is not completed in ODL")
            raise OdlHomeNotCompleted(f"Odl{self}: Homed response can not be received")
        return homed


if __name__ == "__main__":
    dev = OdlThorlabs("/dev/ttyTest")
    print("Module Under Test")
