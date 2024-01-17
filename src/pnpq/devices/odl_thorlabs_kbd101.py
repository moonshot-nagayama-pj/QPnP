#
# Thorlanbs ODL module driver
#       Brushless Motor Driver: KBD101
#       Stage:                  DDS100/M
#
import serial
import time
from serial import Serial


class OdlThorlabs:

    def __init__(self, serial_port = None, serial_number: str = None, config_file = None):
        self.conn = Serial()
        self.conn.baudrate = 115200
        self.conn.bytesize = 8
        self.conn.stopbits = 1
        self.conn.parity = 'N'
        self.conn.rtscts = 1

        self.device_sn = serial_number
        self.port = serial_port
        self.conn.port = self.port
        self.resolution = 2000

        find_Port = False
        if self.device_sn is not None:
            available_Ports = serial.tools.list_ports.comports()
            for ports in available_Ports:
                if (ports.serial_number ==  self.device_sn):
                    self.conn.port = ports.device
                    find_Port = True
                    break
            if find_Port == False:
                raise Exception("Can not find ODL by serial_number (FTDI_SN)")


    def connect(self):
        if self.conn.is_open:
            raise Exception("The connection is already open!")
        else:
            self.conn.open()
            #Enable Channel ID (0)
            self.conn.write(b'\x10\x02\x01\x01\x50\x01')


    def identify(self):
        if self.conn.is_open:
            self.conn.write(b'\x23\x02\x00\x00\x50\x01')
        else:
            raise Exception("Identification failed: can not connect to odl device")

    def move_absolute(self, move_mm: int):
        if self.conn.is_open:
            if (move_mm > 100 or move_mm < 0):
                raise Exception("Invalid move value!")
            else:
                msg = b'\x53\x04\x06\x00\xd0\x01\x00\x00'
                msg = msg + (move_mm*2000).to_bytes(4, byteorder = 'little')
                self.conn.write(msg)
                moving_time = move_mm/20
                time.sleep(moving_time)

        else:
            raise Exception("ODL move failed: can not connect to odl device")

    def home(self):
        if self.conn.is_open:
            self.conn.write(b'\x43\x04\x01\x00\x50\x01')

        else:
            raise Exception("ODL homing failed: can not connect to odl device")
