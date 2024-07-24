#
# OzOptics ODL module driver
#
import serial
from serial import Serial
from pnpq.devices.optical_delay_line import OpticalDelayLine
import time, logging
from pnpq.errors import (
    DeviceDisconnectedError,
    OdlMoveNotCompleted,
    OdlHomeNotCompleted,
    OdlGetPosNotCompleted,
    OdlMoveOutofRangeError,
)



class OdlOzOptics(OpticalDelayLine):
    max_move: int
    """maximum length for moving odl from 0-position, the total path length will be 2x(max_move)"""

    min_move: int
    """minimum specified length for moving: usually zero"""

    resolution: int
    """represents minimum specified length for moving on the stage: usually zero"""

    home_timeout: int
    """required time for completing home in seconds"""

    move_timeout: int
    """required time for completing home in seconds"""

    def __init__(
        self,
        serial_port: str | None = None,
        serial_number: str | None = None,
        config_file=None,
    ):
        super().__init__(serial_port, serial_number, config_file)
        self.name = "OzOptics ODL"

        self.conn.baudrate = 9600
        """Basic Communication BaudRate"""
        self.resolution = 32768 / 5.08
        """32768 steps per motor revolution(5.08 mm = 2xDistance Travel or mirror travel per pitch 0.1 inch)"""
        self.logger = logging.getLogger(f"{self}")
        self.command_terminate = "\r\n"
        self.max_move = 50
        self.min_move = 0
        self.logger = logging.getLogger(f"{self}")

        try:
            self.conn.open()

        except:
            raise RuntimeError("Can not open OZ optic ODL device")

    def __ensure_port_open(self) -> None:
        if not self.conn.is_open:
            self.logger.error("disconnected")
            raise DeviceDisconnectedError(f"{self} is disconnected")

    def reconnect(self):
        if self.conn.is_open:
            self.logger.warning(f"Serial connectio to ODL({self}) is already open!")
        else:
            self.logger.info(f"Openning connection to ODL({self}) device!")
            try:
                self.conn.open()
            except:
                raise DeviceDisconnectedError(f"{self} is disconnected")

    def move(self, dist: float):
        self.logger.debug(f"ODL({self}): move command is received")
        self.__ensure_port_open()

        if dist > self.max_move or dist < self.min_move:
            raise OdlMoveOutofRangeError(f"ODL({self}): Invalid Move Parameter:{dist}")
        else:
            response = self.set_step(int(dist * self.resolution))
            self.logger.debug(f"ODL({self}): move command complete: {response} verifying:")
            step_position = self.get_step()
            self.logger.debug(f"ODL({self}): final position after move:{step_position/self.resolution}")

    def set_step(self, value):
        self.logger.debug(f"ODL({self}): set_step command is received")
        self.__ensure_port_open()
        cmd = "S" + str(value)
        response = self.serial_command(cmd)
        return response

    def get_step(self):
        self.logger.debug(f"ODL({self}): get_step command is received")
        self.__ensure_port_open()
        cmd = "S?"
        response = self.serial_command(cmd)
        if (response.find("UNKNOWN")):
            raise OdlGetPosNotCompleted(
                f"Unknown position for {self}: run find_home()
                first and then change or get the position"
            )
        step = response.split("Done")[0].split(":")[1]
        self.logger.debug(f"ODL({self}): get_step:{step}:return{int(step)}")
        return int(step)

    def current_status(self):
        self.logger.debug(f"ODL({self}): current_status query is received!")
        self.__ensure_port_open()
        cmd = "Q?"
        response = self.serial_command(cmd)
        self.logger.debug(f"ODL({self}) current_status:{response}")
        return response

    def find_home(self):
        self.logger.debug(f"ODL({self}): find_home command is received!")
        self.__ensure_port_open()
        cmd = "FH"
        response = self.serial_command(cmd, retries=1000)
        return response

    def get_serial(self):
        self.logger.debug(f"ODL({self}): get_serial command is received!")
        self.__ensure_port_open()
        cmd = "V2"
        response = self.serial_command(cmd)
        return response.split("Done")[0].split("\r\n")[1]

    def get_device_info(self):
        self.logger.debug(f"ODL({self}): device_info command is received!")
        self.__ensure_port_open()
        cmd = "V1"
        response = self.serial_command(cmd)
        response = response.split("\r\n")[1]
        device_name = response.split("V")[0]
        hwd_version = response.split("V")[1].split("_")[0]
        return device_name, hwd_version

    def get_mfg_date(self):
        self.logger.debug(f"ODL({self}): get manufacturing date command (get_mfg_dates) is received!")
        self.__ensure_port_open()
        cmd = "d?"
        response = self.serial_command(cmd)
        date = response.split("\r\n")[1]
        return date

    def echo(self, on_off):
        self.logger.debug(f"ODL({self}): echo({on_off}) command is received!")

        self.__ensure_port_open()
        cmd = "e" + str(on_off)
        response = self.serial_command(cmd)
        return response

    def reset(self):
        self.logger.debug(f"ODL({self}): reset command is received!")
        self.__ensure_port_open()
        cmd = "RESET"
        response = self.serial_command(cmd)
        return response

    def oz_mode(self, on_off):  # on_off -> 0: OZ mode OFF | 1: OZ mode ON
        self.__ensure_port_open()
        cmd = "OZ-SHS" + str(on_off)
        # cmd = '?'
        response = self.serial_command(cmd)
        return response

    def home(self):
        self.logger.debug(f"ODL({self}): home command is received!")
        self.__ensure_port_open()
        cmd = "GR"
        response = self.serial_command(cmd, retries=15)
        return response

    def end(self):
        self.logger.debug(f"ODL({self}): end command is received!")

        self.__ensure_port_open()
        cmd = "GF"
        response = self.serial_command(cmd, retries=15)
        return response

    def stop(self):
        self.logger.debug(f"ODL({self}): stop motor driver command is received!")

        self.__ensure_port_open()
        cmd = "G0"
        response = self.serial_command(cmd)
        return response

    def write_to_flash(self):
        self.__ensure_port_open()
        cmd = "OW"
        response = self.serial_command(cmd)
        return response

    def start_burn_in(self, parameter):
        self.__ensure_port_open()
        cmd = "OZBI" + str(parameter)
        response = self.serial_command(cmd)
        return response

    def write_name(self, parameter):
        self.__ensure_port_open()
        cmd = "ODN" + str(parameter)
        response = self.serial_command(cmd)
        return response

    def write_serial(self, parameter):
        self.__ensure_port_open()
        cmd = "ODS" + str(parameter)
        response = self.serial_command(cmd)
        return response

    def write_mfg_date(self, parameter):
        self.__ensure_port_open()
        cmd = "ODM" + str(parameter)
        response = self.serial_command(cmd)
        return response

    def write_hw_version(self, parameter):
        self.__ensure_port_open()
        cmd = "OHW" + str(parameter)
        response = self.serial_command(cmd)
        return response

    def serial_close(self):
        self.__ensure_port_open()
        self.conn.close()

    def serial_send(self, serial_cmd):
        # Encode and send the command to the serial device.
        self.conn.flushInput()  # flush input buffer, discarding all its contents
        self.conn.flushOutput()  # flush output buffer, aborting current output and discard all that is in buffer
        self.conn.write(serial_cmd.encode())

    def serial_read(self, retries=10):
        # The Python serial "in_waiting" property is the count of bytes available
        # for reading at the serial port.  If the value is greater than zero
        # then we know we have content available.
        device_output = ""
        got_OK = False
        while self.conn.in_waiting > 0 or (got_OK is False and retries > 0):
            device_output += (self.conn.read(self.conn.in_waiting)).decode("iso-8859-1")
            # command output is complete.
            if device_output.find("Done") >= 0:
                got_OK = True
            time.sleep(0.05)
            retries -= 1
        return device_output

    def serial_command(self, serial_cmd, retries=5):
        self.__ensure_port_open()
        self.serial_send(serial_cmd + self.command_terminate)
        device_output = self.serial_read(retries)
        return device_output

    def readKey(self, key, retries=10):
        self.__ensure_port_open()
        device_output = ""
        got_OK = False
        while self.conn.in_waiting > 0 or (got_OK is False and retries > 0):
            device_output += (self.conn.read(self.conn.in_waiting)).decode("iso-8859-1")
            # command output is complete.
            if device_output.find(key) >= 0:
                got_OK = True
            time.sleep(0.05)
            retries -= 1
        return device_output

    def readall(self, sectimeout=5):
        self.__ensure_port_open()
        ok = False
        bytes = self.conn.read(1)
        while self.conn.in_waiting > 0:
            bytes += self.conn.read(1)
        msg = bytes.decode("UTF-8")
        ok = True
        return ok, msg


if __name__ == "__main__":
    dev = OdlOzOptics("/dev/ttyUSB0")
    print("Module Under Test/")
