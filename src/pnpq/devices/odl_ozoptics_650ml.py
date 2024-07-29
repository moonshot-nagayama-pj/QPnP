#
# OzOptics ODL module driver
#
import serial
from serial import Serial
from pnpq.devices.optical_delay_line import OpticalDelayLine
from pnpq.errors import OdlGetPosNotCompleted
import time


class OdlOzOptics(OpticalDelayLine):
    def __init__(
        self,
        serial_port: str | None = None,
        serial_number: str | None = None,
        config_file=None,
    ):
        super().__init__(serial_port, serial_number, config_file)
        self.conn.baudrate = 9600
        """Basic Communication BaudRate"""
        self.resolution = 32768 / 5.08
        """32768 steps per motor revolution(5.08 mm = 2xDistance Travel or mirror travel per pitch 0.1 inch)"""

        self.command_terminate = "\r\n"

        try:
            self.conn.open()
        except:
            raise RuntimeError("Can not open OZ optic ODL device")

    def connect(self):
        if self.conn.is_open == 0:
            try:
                self.conn.open()
            except Exception as err:
                raise RuntimeError("Connection failed: " + str(err))

    def move(self, dist: float):
        if not self.conn.is_open:
            raise RuntimeError("Moving ODL failed: can not connect to ODL device")
        if dist > 200 or dist < 0:
            raise Exception("Invalid Move Parameter")
        else:
            self.set_step(int(dist * self.resolution))

    def set_step(self, value):
        cmd = "S" + str(value)
        response = self.serial_command(cmd)
        return response

    def get_step(self) -> int:
        response = self.serial_command("S?")
        if "UNKNOWN" in response:
            raise OdlGetPosNotCompleted(
                f"Unknown position for ODL({self}): run find_home() first and then change or get the position"
            )
        step = response.split("Done")[0].split(":")[1]
        return int(step)

    def home(self):
        cmd = "FH"
        response = self.serial_command(cmd, retries=1000)
        return response

    def get_serial(self):
        cmd = "V2"
        response = self.serial_command(cmd)
        return response.split("Done")[0].split("\r\n")[1]

    def get_device_info(self):
        cmd = "V1"
        response = self.serial_command(cmd)
        response = response.split("\r\n")[1]
        device_name = response.split("V")[0]
        hwd_version = response.split("V")[1].split("_")[0]
        return device_name, hwd_version

    def get_mfg_date(self):
        cmd = "d?"
        response = self.serial_command(cmd)
        date = response.split("\r\n")[1]
        return date

    def echo(self, on_off):
        cmd = "e" + str(on_off)
        response = self.serial_command(cmd)
        return response

    def reset(self):
        cmd = "RESET"
        response = self.serial_command(cmd)
        return response

    def oz_mode(self, on_off):  # on_off -> 0: OZ mode OFF | 1: OZ mode ON
        cmd = "OZ-SHS" + str(on_off)
        # cmd = '?'
        response = self.serial_command(cmd)
        return response

    def forward(self):
        cmd = "GF"
        response = self.serial_command(cmd, retries=15)
        return response

    def reverse(self):
        cmd = "GR"
        response = self.serial_command(cmd, retries=15)
        return response

    def stop(self):
        cmd = "G0"
        response = self.serial_command(cmd)
        return response

    def set_step(self, value):
        cmd = "S" + str(value)
        response = self.serial_command(cmd)
        return response

    def write_to_flash(self):
        cmd = "OW"
        response = self.serial_command(cmd)
        return response

    def start_burn_in(self, parameter):
        cmd = "OZBI" + str(parameter)
        response = self.serial_command(cmd)
        return response

    def write_name(self, parameter):
        cmd = "ODN" + str(parameter)
        response = self.serial_command(cmd)
        return response

    def write_serial(self, parameter):
        cmd = "ODS" + str(parameter)
        response = self.serial_command(cmd)
        return response

    def write_mfg_date(self, parameter):
        cmd = "ODM" + str(parameter)
        response = self.serial_command(cmd)
        return response

    def write_hw_version(self, parameter):
        cmd = "OHW" + str(parameter)
        response = self.serial_command(cmd)
        return response

    def serial_close(self):
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
        self.serial_send(serial_cmd + self.command_terminate)
        device_output = self.serial_read(retries)
        return device_output

    def readKey(self, key, retries=5):
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
        ok = False
        bytes = self.conn.read(1)
        while self.conn.inWaiting() > 0:
            bytes += self.conn.read(1)
        msg = bytes.decode("UTF-8")
        ok = True
        return ok, msg


if __name__ == "__main__":
    dev = OdlOzOptics("/dev/ttyUSB0")
    print("Module Under Test/")
