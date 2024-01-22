#
# OzOptics ODL module driver
#
import serial
from serial import Serial
from serial.tools import list_ports

class OdlOzOptics:

    def __init__(self, serial_port = None, serial_number: str = None, config_file = None):
        self.conn = Serial()
        self.conn.baudrate = 9600
        self.port = serial_port
        self.conn.port = self.port
        self.device_sn = serial_number

        find_Port = False
        if self.device_sn is not None:
            available_Ports =  serial.tools.list_ports.comports()
            for ports in available_Ports:
                if (ports.serial_number ==  self.device_sn):
                    self.conn.port = ports.device
                    find_Port = True
                    break
            if find_Port == False:
                raise Exception("Can not find ODL by serial_number (FTDI_SN)")


    def connect(self):
        if self.conn.is_open == 0:
            try:
                self.conn.open()
            except Exception as err:
                raise Exception("Connection failed: " + str(err))

    def move():
        pass

    def home():
        pass

    def current_step():
        pass
