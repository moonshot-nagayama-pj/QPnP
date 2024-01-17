#
#
#

from serial import Serial

class Switch:
    def __init__(
        self, serial_port: str = None, serial_number: str = None, config_file=None
    ):
        self.conn = Serial()
        self.port = serial_port
        self.conn.port = self.port
        self.resolution = 2000

    def __connect__(self):
            self.conn.open()

    #def current_state(self):
    #    if self.conn.is_open:
    #        self.conn.write(b'S ?\x0A')

    def bar_state(self):
        if self.conn.is_open:
            self.conn.write(b'S 1\x0A')
        else:
            raise Exception("Switch is not connected!")

    def cross(self):
        if self.conn.is_open:
             self.conn.write(b'S 2\x0A')
        else:
            raise Exception("Switch is not connected!")

    #def othermethod(self):
    #     if self.conn.is_open:
    #        self.conn.write()
    #    else:
    #        raise Exception("Switch is not connected!")

