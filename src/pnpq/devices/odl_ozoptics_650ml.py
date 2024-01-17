#
# OzOptics ODL module driver
#
from serial import Serial

class OdlOzOptics:

    def __init__(self, serial_port = None, serial_number: str = None, config_file = None):
        self.conn = Serial()
        self.port = serial_port
        self.conn.port = self.port


    def connect(self):
        if self.conn.is_open == 0:
            self.conn.open()

    def move():
        pass

    def home():
        pass

    def current_step():
        pass
