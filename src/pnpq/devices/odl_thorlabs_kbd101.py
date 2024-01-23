#
# Thorlanbs ODL module driver
#       Brushless Motor Driver: KBD101
#       Stage:                  DDS100/M
#
import serial
import time
from serial import Serial
from pnpq.devices.optical_delay_line import OpticalDelayLine


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

    def connect(self):
        if self.conn.is_open:
            raise Exception("The connection is already open!")

        self.conn.open()
        # Enable Channel ID (0)
        self.conn.write(b"\x10\x02\x01\x01\x50\x01")

    def identify(self):
        if not self.conn.is_open:
            raise RuntimeError("Identification failed: can not connect to odl device")

        self.conn.write(b"\x23\x02\x00\x00\x50\x01")

    def move(self, move_mm: int):
        if self.conn.is_open:
            if move_mm > 100 or move_mm < 0:
                raise Exception("Invalid move value!")
            else:
                msg = b"\x53\x04\x06\x00\xd0\x01\x00\x00"
                msg = msg + (move_mm * 2000).to_bytes(4, byteorder="little")
                self.conn.write(msg)
                moving_time = move_mm / 20
                time.sleep(moving_time)

        else:
            raise Exception("ODL move failed: can not connect to odl device")

    def home(self):
        if self.conn.is_open:
            self.conn.write(b"\x43\x04\x01\x00\x50\x01")

        else:
            raise Exception("ODL homing failed: can not connect to odl device")


if __name__ == "__main__":
    dev = OdlThorlabs("/dev/ttyTest")
    print("Module Under Test")
