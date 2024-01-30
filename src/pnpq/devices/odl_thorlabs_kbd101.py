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
        self.home_timeout = 25
        self.move_timeout = 2
        self.maxmove = 100
        self.minmove = 0
        self.name = "Thorlabs"
        self.model = "KBD101 driver DDS100/M Stage"

    def connect(self):
        if self.conn.is_open:
            raise Exception("The connection is already open!")

        self.conn.open()
        print("Connecting to Thorlabs ODL mdoule")
        # Enable Channel ID (0)
        self.conn.write(b'\x10\x02\x01\x01\x50\x01')
        time.sleep(0.5)


    def identify(self):
        if not self.conn.is_open:
            raise RuntimeError("Identification failed: can not connect to odl device")

        self.conn.write(b"\x23\x02\x00\x00\x50\x01")

    def waitForReply(self, sequence, timeout):
        retries = timeout
        result = b''
        readPhase = True
        while readPhase and retries > 0:
            noReadBytes = self.conn.in_waiting

            result += self.conn.read(noReadBytes)
            if (noReadBytes > 0):
                if result.find(sequence) == -1:  #find non matching sequence!
                    print("Unknown Sequence have been found: " + str(result))

                else:
                    readPhase = False
                    return result
            time.sleep(1)
            retries -= 1

    def move(self, move_mm: int):
        if not self.conn.is_open:
            raise Exception("Moving Failed: Can not connect to the device")

        if move_mm > self.maxmove or move_mm < self.minmove:
            raise Exception("Invalid/ Out of range value for ODL moving!")

        msg = b'\x53\x04\x06\x00\xd0\x01\x00\x00'
        msg = msg + (move_mm * self.resolution).to_bytes(4, byteorder="little")
        self.conn.write(msg)

        move_complete = self.waitForReply(b'\x64\04', self.move_timeout)
        #if not move_complete:
        #   raise Warning("Can not receive MOVE Complete Response")
        #else:
        #    print("Move Completed!")

    def step_forward(self, steps):
        if not self.conn.is_open:
            raise Exception("Move forward failed: can not connect to Thorlabs ODL device")

        if steps > self.maxmove*self.resolution:
            raise Exception("required steps are more that the device resolution: " + str(self.resolution))
        #relative

        msg = b'\x48\x04\x06\x00\xd0\x01\x00\x00'
        msg = msg + (int(steps)).to_bytes(4, byteorder="little", signed = True)
        self.conn.write(msg)

        forward_complete = self.waitForReply(b'\x64\x04', self.move_timeout)
        #if not forward_complete:
        #    raise Warning("Can not received STEP_FW Complete!")
        #else:
        #    print("Step Forward complete:" + str(forward_complete))

    def step_backward(self, steps):
        if not self.conn.is_open:
            raise Exception("Move forward failed: can not connect to Thorlabs ODL device")

        if steps > self.maxmove*self.resolution:
            raise Exception("required steps are more that the device resolution: " + str(self.resolution))

        #negate steps
        steps = -steps
        #relative move
        msg = b'\x48\x04\x06\x00\xd0\x01\x00\x00'
        msg = msg + (int(steps)).to_bytes(4, byteorder="little", signed = True)
        self.conn.write(msg)

        forward_complete = self.waitForReply(b'\x64\x04', self.move_timeout)
        #if not forward_complete:
        #    raise Warning("Can not received STEP_FW Complete!")
        #else:
        #    print("Step Forward complete:" + str(forward_complete))


    def get_status(self):
        if not self.conn.is_open:
            raise Exception("ODL get_status failed: can not connect to ODL device")

        print("trying to get_status using START_UPDATE")
        # MGMSG_MOT_REQ_STATUSUPDATE 0x480 but is it correct for KBD101?
        msg = b'\x11\x00\x00\x00\x50\x01'
        self.conn.write(msg)
        # Waiting for MGMSG_MOT_GET_STATUSUPDATE response 0x481
        readStatus = self.waitForReply(b'\x81\04')

        if readStatus:
            print("GET/UPDATE STATUS Failed!")
        else:
            print(readStatus)


    def home(self):
        if not self.conn.is_open:
            raise Exception("ODL homing failed: can not connect to odl device")

        self.conn.write(b'\x43\x04\x01\x00\x50\x01')

        homed = self.waitForReply(b'\x44\x04', self.home_timeout)
        #if not homed:
        #    raise Warning("Can not received HOME Complete!")
        #else:
        #    print("HOME complete:" + str(homed))


if __name__ == "__main__":
    dev = OdlThorlabs("/dev/ttyTest")
    print("Module Under Test")
