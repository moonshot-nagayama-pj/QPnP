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
