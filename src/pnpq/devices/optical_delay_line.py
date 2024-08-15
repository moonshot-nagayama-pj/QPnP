from serial import Serial
import serial.tools.list_ports


class OpticalDelayLine:
    """represents optical delay line devices. all ODL classes must inherit this class."""

    name: str
    conn: Serial
    """represents a Serial connection"""

    device_sn: str | None
    """device's serial number"""

    port: str | None
    """initialize ODL class"""

    def __init__(
        self,
        port: str | None = None,
        serial_number: str | None = None,
        config_file=None,
    ):
        if serial_number is None and port is None:
            raise RuntimeError("Not port name nor serial_number are specified!")

        self.name = "Optical Delay Line"
        self.default_interface = "Serial Interface"
        self.device_sn = serial_number
        self.port = port
        self.conn = Serial()

        available_ports = serial.tools.list_ports.comports()
        for ports in available_ports:
            if ports.serial_number == self.device_sn or ports.device == self.port:
                self.conn.port = ports.device
                break

        if self.conn.port is None:
            raise RuntimeError("Can not find ODL by serial_number (FTDI_SN) or port!")


if __name__ == "__main__":
    dev = OpticalDelayLine("/dev/urandom")
    print("Module Under Test")
