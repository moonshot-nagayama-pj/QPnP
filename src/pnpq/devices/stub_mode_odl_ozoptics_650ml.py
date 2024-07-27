#
# OzOptics ODL module driver
# Stub mode:    True
#
from pnpq.devices.optical_delay_line import OpticalDelayLine
import time, logging


class OdlOzOptics(OpticalDelayLine):
    def __init__(self):
        # Stub Serial Number
        # TODO: Custom serial number from initializer
        self.device_sn = "stubodl_ozoptics"
        """Basic Communication BaudRate"""
        self.resolution = 32768 / 5.08
        """32768 steps per motor revolution(5.08 mm = 2xDistance Travel or mirror travel per pitch 0.1 inch)"""
        self.logger = logging.getLogger(f"{self}")

        # Stub device parameters
        self.current_position = 0

        # Is connected to the device
        self.connected = False

    def connect(self):
        self.connected = True
        self.logger.info("Stub Odl_Ozoptics Connected")

    def move(self, dist: float):
        if dist > 200 or dist < 0:
            raise Exception("Invalid Move Parameter")
        else:
            self.set_step(int(dist * self.resolution))

    def current_step(self):
        return self.current_position

    def home(self):
        cmd = "FH"
        return self.logger.info(f"Set to Home Parameter Value: {cmd}")

    def get_serial(self):
        cmd = "V2"
        self.logger.info("Get Serial Parameter Value: "+cmd)
        return self.logger.info("Serial Number: Stub Odl_Ozoptics")

    def get_device_info(self):
        cmd = "V1"
        self.logger.info("Get Device Info Parameter Value: "+cmd)
        return self.logger.info(self.device_sn)

    def get_mfg_date(self):
        cmd = "d?"
        return self.logger.info("Get MFG Date: "+cmd)

    def echo(self, on_off):
        cmd = "e" + str(on_off)
        return self.logger.info("echo: "+cmd)

    def reset(self):
        cmd = "RESET"
        return self.logger.info("reset: "+cmd)

    def oz_mode(self, on_off):  # on_off -> 0: OZ mode OFF | 1: OZ mode ON
        cmd = "OZ-SHS" + str(on_off)
        # cmd = '?'
        return self.logger.info("oz-mode: "+cmd)

    def forward(self):
        cmd = "GF"
        return self.logger.info("Forward: "+cmd)

    def reverse(self):
        cmd = "GR"
        return self.logger.info("Reverse: "+cmd)

    def stop(self):
        cmd = "G0"
        return self.logger.info("Stop: "+cmd)

    def set_step(self, value):
        cmd = "S" + str(value)
        return self.logger.info("Set Step: "+cmd)

    def get_step(self):
        cmd = "S?"
        step = self.current_position
        return int(step)

    def write_to_flash(self):
        cmd = "OW"
        return self.logger.info("Write to Flash: "+cmd)

    def start_burn_in(self, parameter):
        cmd = "OZBI" + str(parameter)
        return self.logger.info("Start Burn In: "+cmd)

    def write_name(self, parameter):
        cmd = "ODN" + str(parameter)
        return self.logger.info("Write Name: "+cmd)

    def write_serial(self, parameter):
        cmd = "ODS" + str(parameter)
        return self.logger.info("Write Serial: "+cmd)

    def write_mfg_date(self, parameter):
        cmd = "ODM" + str(parameter)
        return self.logger.info("Write MFG Date: "+cmd)

    def write_hw_version(self, parameter):
        cmd = "OHW" + str(parameter)
        return self.logger.info("Write HW Version: "+cmd)

    def serial_close(self):
        self.logger.info("Stub Serial Close")
        self.connected = False

    def serial_send(self, serial_cmd):
        # Encode and send the command to the serial device.
        self.logger.info("Serial Send: "+serial_cmd)

    def serial_read(self, retries=10):
        return "Serial Read: Done"

    def serial_command(self, serial_cmd, retries=5):
        return "Serial Command: Done"

    def readKey(self, key, retries=5):
        return "Read Key: Done"

    def readall(self, sectimeout=5):
        return "Read All: Done"


if __name__ == "__main__":
    dev = OdlOzOptics()
    print("Stub Mode Under Test")
