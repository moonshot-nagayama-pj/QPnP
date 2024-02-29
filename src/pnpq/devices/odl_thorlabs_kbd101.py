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
    OdlMoveNotCompleted,
    OdlHomeNotCompleted,
    OdlGetPosNotCompleted,
    OdlMoveOutofRangeError,
)

ODL_HOME_COMMAND = b"\x43\x04\x01\x00\x50\x01"
ODL_MOVE_COMMAND = b"\x53\x04\x06\x00\xd0\x01\x00\x00"
STOP_UPDATE_COMMAND = b"\x12\x00\x00\x00\x50\x01"
START_UPDATE_COMMAND = b"\x11\x00\x00\x00\x50\x01"
ODL_IDENTIFY_COMMAND = b"\x23\x02\x00\x00\x50\x01"
ENABLE_CHANNEL_SET_COMMAND = b"\x10\x02\x01\x01\x50\x01"
ENABLE_CHANNEL_GET_COMMAND = b"\x11\x02\x01\x00\x50\x01"
ODL_RELATIVE_MOVE_COMMAND = b"\x48\x04\x06\x00\xd0\x01\x00\x00"

# KBD101 STATUS UPDATE (MSMSD_MOT_REQ|GET_USTATUSUPDATE):
# https://www.thorlabs.com/Software/Motion%20Control/APT_Communications_Protocol.pdf
MGMSG_MOT_REQ_USTATUSUPDATE = b"\x90\x04\x01\x00\x50\x01"
MGMSG_MOT_GET_USTATUSUPDATE = b"\x91\x04"

ODL_HOMD_POSITION: int = 0


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
        self.curr_pos_steps: int | None

    def __ensure_port_open(self) -> None:
        if not self.conn.is_open:
            self.logger.error("disconnected")
            raise DeviceDisconnectedError(f"{self} is disconnected")

    def __ensure_steps_in_range(self, steps: int) -> None:
        max_threshold = self.maxmove * self.resolution
        min_threshold = self.minmove * self.resolution

        if min_threshold <= steps <= max_threshold:
            return
        raise OdlMoveOutofRangeError(
            f"Move request for device{self} is out of range min({self.minmove}) - max({self.maxmove})"
        )

    def connect(self) -> None:
        if self.conn.is_open:
            self.logger.warning("ODL ({self}) serial connection is already open")
        self.conn.open()

        if not self.conn.is_open:
            raise DeviceDisconnectedError(f"ODL device is disconneced")
        self.logger.info(f"({self}): Connecting to Thorlabs ODL module")
        # Enable Channel ID (0)
        self.conn.write(ENABLE_CHANNEL_SET_COMMAND)
        time.sleep(0.1)
        self.conn.write(ENABLE_CHANNEL_GET_COMMAND)
        enable_channel_result = self.__wait_for_reply(b"\x12\x02", 5)
        if enable_channel_result is None:
            self.logger.error(f"can not enable odl channel")

    def identify(self):
        self.__ensure_port_open()
        self.conn.write(ODL_IDENTIFY_COMMAND)

    def __wait_for_reply(self, sequence, timeout):
        retries = timeout
        result = b""
        while retries > 0:
            num_read_bytes = self.conn.in_waiting

            result = self.conn.read(num_read_bytes)

            self.logger.debug(
                f"ODL wait for reply: {sequence}, results: {result}, retry count: {retries}"
            )
            if num_read_bytes > 0 and result.find(sequence) != -1:
                self.logger.info(f"The response found: {result} ")
                return result
            time.sleep(1)
            retries -= 1

    def move(self, move_mm: int):
        move_steps = move_mm * self.resolution
        self.logger.debug(
            f"move command recieved: move_mm:({move_mm})->move_steps:({move_steps})"
        )
        self.__ensure_port_open()
        self.__ensure_steps_in_range(move_steps)

        msg = ODL_MOVE_COMMAND + (move_steps).to_bytes(4, byteorder="little")
        self.conn.write(msg)

        move_result = self.__wait_for_reply(b"\x64\04", self.move_timeout)
        if not move_result:
            self.logger.error(f"move command is not completed")
            raise OdlMoveNotCompleted(
                f"ODL({self}): No moved_completed response has been received"
            )
        self.curr_pos_steps = move_steps

        self.logger.debug(f"Move completed position_steps({self.curr_pos_steps})!")

    def step_forward(self, steps):
        self.__ensure_port_open()
        self.__ensure_steps_in_range(steps)
        self.__ensure_final_in_range(self.curr_pos_steps, steps)

        msg = ODL_RELATIVE_MOVE_COMMAND + (int(steps)).to_bytes(
            4, byteorder="little", signed=True
        )
        self.conn.write(msg)
        forward_result = self.__wait_for_reply(b"\x64\x04", self.move_timeout)

        if not forward_result:
            self.logger.error(f"step forward command is not completed")
            raise OdlMoveNotCompleted(
                f"ODL({self}: No response is received for step_forward command)"
            )
        self.curr_pos_steps += steps

    def __ensure_final_in_range(self, current_position: int, steps: int):

        max_threshold = self.maxmove * self.resolution
        min_threshold = self.maxmove * self.resolution

        next_position = current_position + steps
        if next_position > max_threshold or next_position < min_threshold:
            raise OdlMoveOutofRangeError(
                f"The relative change position request for device{self} is out of range min({self.minmove}) - max({self.maxmove})"
            )

    def step_backward(self, steps):
        self.__ensure_port_open()
        self.__ensure_steps_in_range(steps)

        # negate steps
        steps = -steps
        self.__ensure_final_in_range(self.curr_pos_steps, steps)

        # relative move
        msg = ODL_RELATIVE_MOVE_COMMAND + (int(steps)).to_bytes(
            4, byteorder="little", signed=True
        )
        self.conn.write(msg)

        backward_result = self.__wait_for_reply(b"\x64\x04", self.move_timeout)
        if not backward_result:
            self.logger.error(f"step backward command is not completed")
            raise OdlMoveNotCompleted(
                f"ODL{self}: No response is received for step_backward command"
            )
        self.curr_pos_steps += steps

    def auto_update_start(self) -> bytes | None:
        self.logger.info("cal auto update start cmd")
        self.__ensure_port_open()
        msg = START_UPDATE_COMMAND
        self.conn.write(msg)
        result = self.__wait_for_reply(b"\x91\x04", self.move_timeout)

        self.logger.debug(f"auto_update_start result: {result}")
        if result is None:
            self.logger.warning("auto update start command is not completed")
        else:
            self.auto_update = True
        return result

    def auto_update_stop(self) -> bytes | None:
        self.logger.info("cal auto update stop cmd")
        self.__ensure_port_open()
        msg = STOP_UPDATE_COMMAND
        self.conn.write(msg)
        result = self.__wait_for_reply(b"\x91\x04", 2)

        self.logger.debug(f"auto_update_stop result: {result}")
        if result is not None:
            self.logger.warning("auto update stop command is not completed")
        else:
            self.auto_update = False
        return result

    def getpos(self) -> int | None:
        self.logger.info("call getpos cmd")
        self.__ensure_port_open()
        self.conn.write(MGMSG_MOT_REQ_USTATUSUPDATE)
        result = self.__wait_for_reply(b"\x91\x04", self.move_timeout)
        self.logger.debug(f"getpos all byte sequence results: {result}")

        if result is None:
            self.logger.error("getpos command is not completed")
            raise OdlGetPosNotCompleted(
                f"ODL{self}: No update response has been received for determining the position"
            )

        pos_seq = result[8:12]
        self.logger.debug(f"getpos byte result: {pos_seq}")

        steps = int.from_bytes(pos_seq, byteorder="little")
        position = steps / self.resolution
        self.logger.info(f"getpos extracted result: pos:{position} steps:{steps}")
        self.curr_pos_steps = steps
        return steps

    def home(self) -> bytes | None:
        self.__ensure_port_open()

        self.conn.write(ODL_HOME_COMMAND)
        time.sleep(0.5)

        homed = self.__wait_for_reply(b"\x44\x04", self.home_timeout)
        self.logger.debug(f"home result: {homed}")
        if homed is None:
            self.logger.error("home command is not completed in ODL")
            raise OdlHomeNotCompleted(f"Odl{self}: Homed response can not be received")
        self.curr_pos_steps = ODL_HOMD_POSITION
        return homed


if __name__ == "__main__":
    dev = OdlThorlabs("/dev/ttyTest")
    print("Module Under Test")
