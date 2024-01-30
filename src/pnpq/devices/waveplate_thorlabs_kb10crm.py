import serial
import time
from serial import Serial


class Waveplate:
    conn: Serial
    serial_number: str
    port: str
    resolution: int
    relative_home: float

    def __init__(
        self, serial_port: str = None, serial_number: str = None, config_file=None
    ):
        self.conn = Serial()
        self.conn.baudrate = 115200
        self.conn.bytesize = 8
        self.conn.stopbits = 1
        self.conn.parity = "N"
        self.conn.rtscts = 1

        self.device_sn = serial_number
        self.port = serial_port
        self.conn.port = self.port
        self.resolution = 136533

        find_Port = False
        if self.device_sn is not None:
            available_Ports = serial.tools.list_ports.comports()
            for ports in available_Ports:
                if ports.serial_number == self.device_sn:
                    self.conn.port = ports.device
                    find_Port = True
                    break
            if find_Port == False:
                raise Exception(
                    "Can not find Rotator WavePlate by serial_number (FTDI_SN)"
                )

    def connect(self):
        self.conn.open()

    def identify(self):
        if self.conn.is_open:
            self.conn.write(b"\x23\x02\x00\x00\x50\x01")
        else:
            raise Exception("WP device is not connected!")

    def resolution(self):
        print("Device Resolution: 136533 steps/degree")


    def waitForReply(self, sequence, timeout):
        retries = timeout
        result = b''
        readPhase = True
        while readPhase and retries > 0:
            #while True:
            noReadBytes = self.conn.in_waiting

            #result += self.conn.read(noReadBytes).encode('backslashreplace')
            result += self.conn.read(noReadBytes)
            #print(str(result))
            #print("try to find sequence: " + str(sequence))
            if (noReadBytes > 0):
                if result.find(sequence) == -1:  #find non matching sequence!
                    print("Unknown Sequence have been found: " + str(result))

                else:
                #if result.find(sequence) == 0: #find the sequence at the begining of the response
                    readPhase = False
                    #print("FInd sequence:" + str(result))
                    return result
            time.sleep(1)
            retries -= 1


    def home(self):
        if not self.conn.is_open:
            raise Exception("Homing Failed: Can not connect to the device!")

        # Home REQ command!
        self.conn.write(
            b'\x40\x04\x0e\x00\xb2\x01\x00\x00\x00\x00\x00\x00\xa4\xaa\xbc\x08\x00\x00\x00\x00'
        )
        time.sleep(0.5)

        # HOME SET command!
        self.conn.write(b'\x06\x00\x00\x00\x50\x01')
        time.sleep(0.5)

        # HOME Move command!
        self.conn.write(b'\x43\x04\x01\x00\x50\x01')
        time.sleep(0.5)

        homed = self.waitForReply(b'\x44\x04', 20)

        if not homed:
            raise Warning("Can not received HOME Complete!")
        #else:
        #    print("HOME complete:" + str(homed))


    def rotate(self, degree):
        # Absolute Rotation
        if not self.conn.is_open:
            raise Exception("Moving Failed: Can not connect to the device")

        else:
            if degree > 360 or degree < 0:
                raise Exception("Invalid Rotation Parameter")

            msg = b'\x53\x04\x06\x00\xb2\x01\x00\x00'
            msg = msg + (int(degree * self.resolution)).to_bytes(4, byteorder="little")
            self.conn.write(msg)

            rotate_complete = self.waitForReply(b'\x64\x04', 10)
            if not rotate_complete:
                raise Warning("Can not receive ROTATE Complete Response!")

    def step_forward(self, steps):
        if not self.conn.is_open:
            raise Exception("Move one step forward")

        MAX_STEPS = self.resolution
        if steps > MAX_STEPS:
            raise Exception("required steps are more that the device resolution: " + str(self.resolution))
        #relative

        msg = b'\x48\x04\x06\x00\xb2\x01\x00\x00'
        msg = msg + (int(steps)).to_bytes(4, byteorder="little")
        self.conn.write(msg)

        forward_complete = self.waitForReply(b'\x64\x04', 10)
        if not forward_complete:
            raise Warning("Can not received STEP_FW Complete!")


    def rotate_relative(self, degree):
        if self.conn.is_open:
            if degree > 360 or degree < 0:
                raise Exception("Invalid Rotation Parameter")

            msg = b'\x48\x04\x06\x00\xb2\x01\x00\x00'
            msg = msg + (int(degree * self.resolution)).to_bytes(4, byteorder="little")
            self.conn.write(msg)

            rotate_complete = self.waitForReply(b'\x64\x04', 10)
            if not rotate_complete:
                raise Warning("Can not received ROTATE Complete!")

            #time.sleep(degree / 10)
        else:
            raise Exception("Moving Failed: Can not connect to the device")

    def rotate_absolute(self, degree):
        if self.conn.is_open:
            if degree > 360 or degree < 0:
                raise Exception("Invalid Rotation Parameter")

            msg = b'\x53\x04\x06\x00\xb2\x01\x00\x00'
            msg = msg + (int(degree * self.resolution)).to_bytes(4, byteorder="little")
            self.conn.write(msg)
            time.sleep(degree / 10)
        else:
            raise Exception("Moving Failed: Can not connect to the device")


    def custom_home(self, degree):
        if not self.conn.is_open:
            raise Exception("Relative Homing Failed: Can not connect to the device!")

        if degree > 360 or degree < 0:
            raise Exception("Invalid degree parameter in Customized Home")

        self.home()
        self.relative_home = degree
        self.rotate(degree)

    # Rotattion with customized home!
    def custom_rotate(self, degree):
        if not self.relative_home:
            raise Exception("No relative homing is defined for rotation!")

        self.rotate(degree + self.relative_home)

    def __repr__(self) -> str:
        return "Waveplate<Tholabs KB10CRM>"
