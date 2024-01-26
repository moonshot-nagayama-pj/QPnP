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
        self.maxmove = 100
        self.minmove = 0
        self.name = "Thorlabs"
        self.model = "KBD101 driver DDS100/M Stage"

    def connect(self):
        if self.conn.is_open:
            raise Exception("The connection is already open!")

        self.conn.open()
        # Enable Channel ID (0)
        self.conn.write(b"\x10\x02\x01\x01\x50\x01")

    def identify(self):
        if not self.conn.is_open:
            raise RuntimeError("Identification failed: can not connect to odl device")
        self.conn.write(b'\x23\x02\x00\x00\x50\x01')

    def move(self, move_mm: int):
        if not self.conn.is_open:
            raise Exception("ODL move failed: can not connect to odl device")
        else:
            if move_mm > self.maxmove or move_mm < self.minmove:
                raise Exception("Invalid move value!")
            else:
                step(move_mm*self.resolution)
                msg = b'\x53\x04\x06\x00\xd0\x01\x00\x00'
                msg = msg + (move_mm * 2000).to_bytes(4, byteorder="little")
                self.conn.write(msg)
                moving_time = move_mm / 20
                time.sleep(moving_time)

    def get_status(self):
        if not self.conn.is_open:
            raise Exception("ODL get_status failed: can not connect to ODL device")
        else:
            # MGMSG_MOT_REQ_STATUSUPDATE 0x480 but is it correct for KBD101?
            msg = b'\x80\x04\x00\x00\x50\x01'
            self.conn.write(msg)

            retries = 10
            result = ""
            while self.conn.in_waiting or retries > 0:
                result += self.conn.read(20)
                retries -= 1
            return result


        #if not self.conn.is_open:
        #    raise Exception("ODL get status failed: can not connect to odl device")
        #else:
            #msg = b""

    def position(self):
        if not self.conn.is_open:
            raise Exception("ODL get_status failed: can not connet to ODL device")

        response = get_status()
        if response is None:
            raise Exception("Can not get the position correctly")
        else:
            position  = response[8:12]
            print(position)


    def step(self, steps: int):
        if not self.conn.is_open:
            raise Exception("ODL step failed: can not connect to odl device:")
        else:
                # Get the current position let call it = 10
                if steps > self.maxmove or steps < self.minmove:
                    msg = b'\x53\x04\x06\x00\xd0\x01\x00\x00'
                    msg = msg + steps.to_bytes(4, byteorder="little")
                    self.conn.write(msg)
                    moving_time = steps / 20000
                    time.sleep(moving_time)



    def home(self):
        if not self.conn.is_open:
            raise Exception("ODL homing failed: can not connect to odl device")
        else:
            self.conn.write(b'\x43\x04\x01\x00\x50\x01')

            # Checking Ishomed()?
\


if __name__ == "__main__":
    dev = OdlThorlabs("/dev/ttyTest")
    print("Module Under Test")
