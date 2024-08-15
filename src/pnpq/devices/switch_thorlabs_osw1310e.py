#
# Thorlanbs Oprical Switch 1x2 and 2x2 1310E driver
#       OSW12-1310E & OSW22-1310E
#
import serial
from serial import Serial


class Switch:
    def __init__(
        self, serial_port: str = None, serial_number: str = None, config_file=None
    ):
        self.conn = Serial()
        self.conn.baudrate = 115200
        self.conn.bytesize = 8
        self.conn.parity = "N"
        self.conn.rtscts = 1

        self.port = serial_port
        self.conn.port = self.port
        self.device_sn = serial_number
        self.conf = config_file

        find_Port = False
        if self.device_sn is not None:
            available_Ports = serial.tools.list_ports.comports()
            for ports in available_Ports:
                if ports.serial_number == self.device_sn:
                    self.conn.port = ports.device
                    find_Port = True
                    break
            if not find_Port:
                raise Exception("Cannot find Switch by serial_number (FTDI_SN)")

        # if config_file != 0:
        #    if find_Port:
        #        raise Warning("Two different approaches are used for supplying serial port")
        #    else:

    def connect(self):
        try:
            self.conn.open()
        except Exception as err:
            raise Exception("Connection failed: " + str(err))

    # def current_state(self):
    #    if self.conn.is_open:
    #        self.conn.write(b'S ?\x0A')

    def bar_state(self):
        if self.conn.is_open:
            try:
                self.conn.write(b"S 1\x0A")
            except Exception as e:
                raise Exception("Failed to set bar state: " + str(e))
        else:
            raise Exception("Switch is not connected!")

    def cross(self):
        if self.conn.is_open:
            self.conn.write(b"S 2\x0A")
        else:
            raise Exception("Switch is not connected!")

    # def othermethod(self):
    #     if self.conn.is_open:
    #        self.conn.write()
    #    else:
    #        raise Exception("Switch is not connected!")
