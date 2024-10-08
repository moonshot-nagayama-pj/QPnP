#
# Thorlanbs ODL module driver
#       Brushless Motor Driver: KBD101
#       Stage:                  DDS100/M
#
import logging
import time

from pnpq.devices.optical_delay_line import OpticalDelayLine
from pnpq.errors import (
    DeviceDisconnectedError,
    OdlGetPosNotCompleted,
    OdlHomeNotCompleted,
    OdlMoveNotCompleted,
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
ODL_HOMED_POSITION = 0


class OdlThorlabs(OpticalDelayLine):
    max_move: int
    """represents maximum specified length for moving on the stage"""

    min_move: int
    """represents minimum specified length for moving on the stage: usually zero"""

    resolution: int
    """represents minimum specified length for moving on the stage: usually zero"""

    home_timeout: int
    """required time for completing home in seconds"""

    move_timeout: int
    """required time for completing home in seconds"""

    auto_update: bool
    """a flag for checking automatic update is active or inactive"""

    current_steps: int
    """current position of optical delay line in steps"""

    def __init__(
        self,
        serial_port: str | None = None,
        serial_number: str | None = None,
    ):
        super().__init__(serial_port, serial_number)
        self.name = "Thorlabs"
        self.model = "KBD101 driver DDS100/M Stage"
        self.conn.baudrate = 115200
        self.conn.bytesize = 8
        self.conn.stopbits = 1
        self.conn.parity = "N"
        self.conn.rtscts = True

        self.home_timeout = 25
        self.move_timeout = 4
        self.resolution = 2000
        self.auto_update = False
        self.max_move = 100
        self.min_move = 0
        self.logger = logging.getLogger(f"{self}")

    def __ensure_port_open(self) -> None:
        if not self.conn.is_open:
            self.logger.error("disconnected")
            raise DeviceDisconnectedError(f"{self} is disconnected")

    def __ensure_steps_in_range(self, steps: int) -> None:
        max_threshold = self.max_move * self.resolution
        min_threshold = self.min_move * self.resolution

        if min_threshold <= steps <= max_threshold:
            return

        self.logger.error("ODL(%s) required steps:(%s) is out of range", self, steps)
        raise OdlMoveOutofRangeError(
            f"Move request for device{self} is out of range min({self.min_move}) - max({self.max_move})"
        )

    def connect(self) -> None:
        if self.conn.is_open:
            self.logger.warning("ODL ({self}) serial connection is already open")
        self.conn.open()

        if not self.conn.is_open:
            raise DeviceDisconnectedError("ODL device is disconneced")
        self.logger.info("(%s): Connecting to Thorlabs ODL module", self)
        # Enable Channel ID (0)
        self.conn.write(ENABLE_CHANNEL_SET_COMMAND)
        time.sleep(0.1)
        self.conn.write(ENABLE_CHANNEL_GET_COMMAND)
        enable_channel_result = self.__wait_for_reply(b"\x12\x02", 5)
        if enable_channel_result is None:
            self.logger.error("cannot enable odl channel")

    def identify(self) -> None:
        self.__ensure_port_open()
        self.conn.write(ODL_IDENTIFY_COMMAND)

    def __wait_for_reply(self, sequence: bytes, timeout: int) -> bytes | None:
        retries = timeout
        result = b""
        while retries > 0:
            num_read_bytes = self.conn.in_waiting

            result = self.conn.read(num_read_bytes)

            self.logger.debug(
                "ODL wait for reply: %s, results: %s, retry count: %s",
                sequence,
                result,
                retries,
            )
            if num_read_bytes > 0 and result.find(sequence) != -1:
                self.logger.info("The response found: %s", result)
                return result
            time.sleep(1)
            retries -= 1
        return None

    def move(self, move_mm: int) -> None:
        move_steps = move_mm * self.resolution
        self.logger.debug(
            "move command recieved: move_mm:(%s)->move_steps:(%s)", move_mm, move_steps
        )
        self.__ensure_port_open()
        self.__ensure_steps_in_range(move_steps)

        msg = ODL_MOVE_COMMAND + (move_steps).to_bytes(4, byteorder="little")
        self.conn.write(msg)

        move_result = self.__wait_for_reply(b"\x64\04", self.move_timeout)
        if not move_result:
            self.logger.error("move command is not completed")
            # raise OdlMoveNotCompleted(
            #    f"ODL({self}): No moved_completed response has been received"
            # )
        self.current_steps = move_steps
        self.logger.debug("Move completed position_steps(%s)", self.current_steps)

    def step_forward(self, steps: int) -> None:
        self.__ensure_port_open()
        self.__ensure_steps_in_range(steps)
        self.__ensure_final_in_range(self.current_steps, steps)

        msg = ODL_RELATIVE_MOVE_COMMAND + (int(steps)).to_bytes(
            4, byteorder="little", signed=True
        )
        self.conn.write(msg)
        forward_result = self.__wait_for_reply(b"\x64\x04", self.move_timeout)

        if not forward_result:
            self.logger.error("step forward command is not completed")
            raise OdlMoveNotCompleted(
                f"ODL({self}: No response is received for step_forward command)"
            )
        self.current_steps += steps

    def __ensure_final_in_range(self, current_position: int, steps: int) -> None:

        max_threshold = self.max_move * self.resolution
        min_threshold = self.min_move * self.resolution

        next_position = current_position + steps
        if min_threshold <= next_position <= max_threshold:
            return
        raise OdlMoveOutofRangeError(
            f"The relative change position request for device{self} is out of range min({self.min_move}) - max({self.max_move})"
        )

    def step_backward(self, steps: int) -> None:
        self.__ensure_port_open()
        self.__ensure_steps_in_range(steps)

        # negate steps
        steps = -steps
        self.__ensure_final_in_range(self.current_steps, steps)

        # relative move
        msg = ODL_RELATIVE_MOVE_COMMAND + (int(steps)).to_bytes(
            4, byteorder="little", signed=True
        )
        self.conn.write(msg)

        backward_result = self.__wait_for_reply(b"\x64\x04", self.move_timeout)
        if not backward_result:
            self.logger.error("step backward command is not completed")
            raise OdlMoveNotCompleted(
                f"ODL{self}: No response is received for step_backward command"
            )
        self.current_steps += steps

    def auto_update_start(self) -> bytes | None:
        self.logger.info("call auto update start cmd")
        self.__ensure_port_open()
        self.conn.write(START_UPDATE_COMMAND)
        result = self.__wait_for_reply(b"\x91\x04", self.move_timeout)

        self.logger.debug("auto_update_start result: %s", result)
        if result is None:
            self.logger.warning("auto update start command is not completed")
        else:
            self.auto_update = True
        return result

    def auto_update_stop(self) -> bytes | None:
        self.logger.info("cal auto update stop cmd")
        self.__ensure_port_open()

        self.conn.write(STOP_UPDATE_COMMAND)
        result = self.__wait_for_reply(b"\x91\x04", 2)

        self.logger.debug("auto_update_stop result: %s", result)
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
        self.logger.debug("getpos all byte sequence results: %s", result)

        if result is None:
            self.logger.error("getpos command is not completed")
            raise OdlGetPosNotCompleted(
                f"ODL{self}: No update response has been received for determining the position"
            )

        pos_seq = result[8:12]
        self.logger.debug("getpos byte result: %s", pos_seq)

        steps = int.from_bytes(pos_seq, byteorder="little")
        position = steps / self.resolution
        self.logger.info("getpos extracted result: pos:%s steps:%s", position, steps)
        self.current_steps = steps
        return steps

    def home(self) -> bytes | None:
        self.__ensure_port_open()

        self.conn.write(ODL_HOME_COMMAND)
        time.sleep(0.5)

        homed = self.__wait_for_reply(b"\x44\x04", self.home_timeout)
        self.logger.debug("home result: %s", homed)
        if homed is None:
            self.logger.error("home command is not completed in ODL")
            raise OdlHomeNotCompleted(f"Odl{self}: Homed response can not be received")
        self.current_steps = ODL_HOMED_POSITION
        return homed


if __name__ == "__main__":
    dev = OdlThorlabs("/dev/ttyTest")
    print("Module Under Test")
