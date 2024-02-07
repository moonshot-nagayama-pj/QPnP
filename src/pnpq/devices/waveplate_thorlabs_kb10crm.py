import time, logging
from serial import Serial

from pnpq.errors import (
    DevicePortNotFoundError,
    DeviceDisconnectedError,
    WaveplateInvalidStepsError,
)
from pnpq.utils import get_available_port

HOME_REQ_COMMAND = (
    b"\x40\x04\x0e\x00\xb2\x01\x00\x00\x00\x00\x00\x00\xa4\xaa\xbc\x08\x00\x00\x00\x00"
)
HOME_SET_COMMAND = b"\x06\x00\x00\x00\x50\x01"
HOME_MOVE_COMMAND = b"\x43\x04\x01\x00\x50\x01"


class Waveplate:
    conn: Serial
    serial_number: str
    port: str | None
    resolution: int
    max_steps: int
    relative_home: float

    def __init__(
        self,
        serial_port: str | None = None,
        serial_number: str | None = None,
    ):
        self.conn = Serial()
        self.conn.baudrate = 115200
        self.conn.bytesize = 8
        self.conn.stopbits = 1
        self.conn.parity = "N"
        self.conn.rtscts = True

        self.device_sn = serial_number
        if serial_port is not None:
            self.port = serial_port
            self.conn.port = self.port
        self.resolution = 136533
        self.max_steps = 136533
        self.rotate_timeout = 10
        self.home_timeout = 20

        if self.device_sn is not None:
            self.conn.port = get_available_port(self.device_sn)
            if self.conn.port is None:
                raise DevicePortNotFoundError(
                    "Can not find Rotator WavePlate by serial_number (FTDI_SN)"
                )

        self.logger = logging.getLogger(f"{self}")

    def __ensure_port_open(self) -> None:
        if not self.conn.is_open:
            self.logger.warn("disconnected")
            raise DeviceDisconnectedError(f"{self} is disconnected")

    def __ensure_less_than_max_steps(self, steps: int) -> None:
        if steps > self.max_steps:
            raise WaveplateInvalidStepsError(
                f"the given steps: {steps} exceeds the device max steps: {self.max_steps}"
            )

    def __ensure_valid_degree(self, degree: float | int) -> None:
        if 0 <= degree <= 360:
            return
        raise WaveplateInvalidStepsError(
            f"Invalid degree specified: {degree}. must be in a range [0,360]"
        )

    def __wait_for_reply(self, sequence: bytes, num_retries: int) -> bytes | None:
        retries = num_retries
        result: bytes = b""
        while retries > 0:
            num_read_bytes = self.conn.in_waiting

            result += self.conn.read(num_read_bytes)
            self.logger.debug(
                f"try to find sequence: {sequence}, results: {result}, retry count: {retries}"
            )

            # the sequence is found
            if num_read_bytes > 0 and result.find(sequence) != -1:
                self.logger.debug(f"The sequence found")
                return result

            time.sleep(1)
            retries -= 1

    def connect(self) -> None:
        self.logger.info("connecting...")
        self.conn.open()
        self.logger.info("connected")

    def identify(self) -> None:
        self.logger.info("call identify cmd")
        self.__ensure_port_open()
        self.conn.write(b"\x23\x02\x00\x00\x50\x01")

    def home(self) -> bytes | None:
        self.logger.info("call home cmd")
        self.__ensure_port_open()

        self.conn.write(HOME_REQ_COMMAND)
        time.sleep(0.5)

        self.conn.write(HOME_SET_COMMAND)
        time.sleep(0.5)

        self.conn.write(HOME_MOVE_COMMAND)
        time.sleep(0.5)

        result = self.__wait_for_reply(b"\x44\x04", 20)
        self.logger.debug(f"home result: {result}")
        if result is None:
            self.logger.warn("home command is not completed")
        return result

    def getpos(self) -> bytes | None:
        self.logger.info("call getpos cmd")
        self.__ensure_port_open()

        # MGMSG_MOT_REQ_STATUSUPDATE
        msg = b"\x80\x04\x00\x32\x01"
        # msg = b'\x12\x00\x00\x32\x01'
        self.conn.write(msg)

        result = self.__wait_for_reply(b"\x81\x04", self.rotate_timeout)
        self.logger.debug(f"getpos result: {result}")
        if result is None:
            self.logger.warn("getpos command is not completed")
        return result

    def rotate(self, degree: int | float) -> bytes | None:
        self.logger.info(f"call rotate cmd: degree={degree}")
        # Absolute Rotation
        self.__ensure_port_open()
        self.__ensure_valid_degree(degree)

        msg = b"\x53\x04\x06\x00\xb2\x01\x00\x00"
        msg = msg + (int(degree * self.resolution)).to_bytes(4, byteorder="little")
        self.conn.write(msg)

        result = self.__wait_for_reply(b"\x64\x04", self.rotate_timeout)
        if result is None:
            self.logger.warn("rotate command is not completed")
        return result

    def step_backward(self, steps: int) -> bytes | None:
        self.logger.info("call step_backward cmd")
        self.__ensure_port_open()
        # negate steps
        steps = -steps
        self.__ensure_less_than_max_steps(steps)

        # relative move
        msg = b"\x48\x04\x06\x00\xb2\x01\x00\x00"
        msg = msg + (int(steps)).to_bytes(4, byteorder="little", signed=True)
        self.conn.write(msg)

        result = self.__wait_for_reply(b"\x64\x04", self.rotate_timeout)
        if result is None:
            self.logger.warn("step_backward command is not completed")
        return result

    def step_forward(self, steps: int) -> bytes | None:
        self.logger.info("call step_forward cmd")
        self.__ensure_port_open()
        self.__ensure_less_than_max_steps(steps)

        # relative
        msg = b"\x48\x04\x06\x00\xb2\x01\x00\x00"
        msg = msg + (int(steps)).to_bytes(4, byteorder="little")
        self.conn.write(msg)

        result = self.__wait_for_reply(b"\x64\x04", self.rotate_timeout)
        if result is None:
            self.logger.warn("step_forward command is not completed")
        return result

    def rotate_relative(self, degree) -> bytes | None:
        self.logger.info(f"call rotate_relative cmd: degree={degree}")
        self.__ensure_port_open()
        self.__ensure_valid_degree(degree)

        msg = b"\x48\x04\x06\x00\xb2\x01\x00\x00"
        msg = msg + (int(degree * self.resolution)).to_bytes(4, byteorder="little")
        self.conn.write(msg)

        result = self.__wait_for_reply(b"\x64\x04", 10)
        if result is None:
            self.logger.warn("rotate command is not completed")
        return result

    def rotate_absolute(self, degree):
        self.logger.info(f"call rotate_absolute cmd: degree={degree}")
        self.__ensure_port_open()
        self.__ensure_valid_degree(degree)

        msg = b"\x53\x04\x06\x00\xb2\x01\x00\x00"
        msg = msg + (int(degree * self.resolution)).to_bytes(4, byteorder="little")
        self.conn.write(msg)
        time.sleep(degree / 10)

    def custom_home(self, degree):
        self.logger.info(f"call custom_home cmd: degree={degree}")
        self.__ensure_port_open()
        self.__ensure_valid_degree(degree)

        self.home()
        self.relative_home = degree
        self.rotate(degree)

    def custom_rotate(self, degree):
        """Rotattion with customized home!"""

        if not self.relative_home:
            raise Exception("No relative homing is defined for rotation!")

        self.rotate(degree + self.relative_home)

    def __repr__(self) -> str:
        return f"Waveplate(Tholabs KB10CRM {self.conn.port})"
