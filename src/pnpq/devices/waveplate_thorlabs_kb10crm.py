import serial
import time
from serial import Serial

class Waveplate:
    conn: Serial
    serial_number: str
    port: str
    resolution: int

    def __init__(
        self, serial_port: str = None, serial_number: str = None, config_file=None
    ):
        self.conn = Serial()
        self.conn.baudrate = 115200
        self.conn.bytesize = 8
        self.conn.stopbits = 1
        self.conn.parity = 'N'
        self.conn.rtscts = 1

        self.device_sn = serial_number
        self.port = serial_port
        self.conn.port = self.port
        self.resolution = 136533

        find_Port = False
        if self.device_sn is not None:
            available_Ports = serial.tools.list_ports.comports()
            for ports in available_Ports:
                if (ports.serial_number ==  self.device_sn):
                    self.conn.port = ports.device
                    find_Port = True
                    break
            if find_Port == False:
                raise Exception("Can not find Rotator WavePlate by serial_number (FTDI_SN)")

    def connect(self):
        self.conn.open()

    def identify(self):
        if self.conn.is_open:
            self.conn.write(b"\x23\x02\x00\x00\x50\x01")
        else:
            raise Exception("WP device is not connected!")

    def resolution(self):
        print("Device Resolution: 136533 steps/degree")

    def home(self):
        if self.conn.is_open:
            # Home REQ command!
            self.conn.write(
                b"\x40\x04\x0e\x00\xb2\x01\x00\x00\x00\x00\x00\x00\xa4\xaa\xbc\x08\x00\x00\x00\x00"
            )
            time.sleep(0.5)

            # HOME SET command!
            self.conn.write(b"\x06\x00\x00\x00\x50\x01")
            time.sleep(0.5)

            # HOME Move command!
            self.conn.write(b"\x43\x04\x01\x00\x50\x01")
            time.sleep(0.5)
        else:
            raise Exception("Homing Failed: Can not connect to the device!")

    def rotate(self, degree):
        #Relatibve Rotation
        if self.conn.is_open:
            if degree > 360 or degree < 0:
                raise Exception("Invalid Rotation Parameter")

            msg = b"\x48\x04\x06\x00\xb2\x01\x00\x00"
            msg = msg + (degree * self.resolution).to_bytes(4, byteorder="little")
            self.conn.write(msg)
            time.sleep(degree / 10)
        else:
            raise Exception("Moving Failed: Can not connect to the device")

    def rotate_relative(self, degree):
        if self.conn.is_open:
            if degree > 360 or degree < 0:
                raise Exception("Invalid Rotation Parameter")

            msg = b"\x48\x04\x06\x00\xb2\x01\x00\x00"
            msg = msg + (degree * self.resolution).to_bytes(4, byteorder="little")
            self.conn.write(msg)
            time.sleep(degree / 10)
        else:
            raise Exception("Moving Failed: Can not connect to the device")

    def rotate_absolute(self, degree):
        if self.conn.is_open:
            if degree > 360 or degree < 0:
                raise Exception("Invalid Rotation Parameter")

            msg = b'\x53\x04\x06\x00\xb2\x01\x00\x00'
            msg = msg + (degree * self.resolution).to_bytes(4, byteorder="little")
            self.conn.write(msg)
            time.sleep(degree / 10)
        else:
            raise Exception("Moving Failed: Can not connect to the device")


    def __repr__(self) -> str:
        return "Waveplate<Tholabs KB10CRM>"
