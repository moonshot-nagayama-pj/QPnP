import serial
import threading

from apt.protocol import ChanIdent, EnableState, AptMessage_MGMSG_MOD_SET_CHANENABLESTATE
from dataclasses import dataclass, ClassVar
from serial import Serial
from serial.tools import list_ports

@dataclass(frozen=True, kw_only=True)
class PolarizationControllerThorlabsMPC320:
    # Serial connection parameters
    baudrate: int = 115200
    bytesize: int = serial.EIGHTBITS
    exclusive: bool = True
    parity: str = serial.PARITY_NONE
    rtscts: bool = True
    stopbits: int = serial.STOPBITS_ONE
    timeout: None|int = None

    connection: InitVar[Serial] = field(init=False)
    rx_dispatcher: InitVar[Thread] = field(init=False)
    serial_number: str

    command_lock: threading.Lock = field(default_factory=threading.Lock)

    def __post_init__() -> None:
        for port in serial.tools.list_ports.comports():
            if port.serial_number == self.serial_number:
                self.connection = Serial(
                    baudrate=this.baudrate,
                    bytesize=this.bytesize,
                    exclusive=this.exclusive,
                    parity=this.parity,
                    port=port.device,
                    rtscts=this.rtscts,
                    stopbits=this.stopbits,
                    timeout=this.timeout,
                )
                self.rx_dispatcher = Thread(target=self.rx_dispatch, daemon=True)
                self.send_message(AptMessage_MGMSG_MOD_SET_CHANENABLESTATE(chan_ident=ChanIdent.CHANNEL_1, enable_state=EnableState.CHANNEL_DISABLED))
                return
        raise ValueError(f"Serial number {self.serial_number} could not be found, failing intialization.")

    # TODO from a multi-threading point of view, it might be much
    # easier to assume that, for the life of a program, a connection
    # is held by a single object that cannot be closed.

    # def __enter__(self) -> None:
    #     self.open()

    # def __exit__(self, exc_type, exc_value, exc_tb) -> None:
    #     self.close()

    # def open(self) -> None:
    #     self.connection.open()

    # def close(self) -> None:
    #     self.connection.flush()
    #     self.connection.close()

    def send_message(self, message: AptMessage) -> None | AptMessage:
        """Send a message and block until a reply is received (assuming that a reply is expected)"""

        # Not necessarily the case that we need to syncrhonize writes
        # to the port to avoid interleaved text from other threads
        # (the underlying os.write() may handle this for us, I'm not
        # totally sure) but eventually we will need to prevent more
        # than one command running at the same time, e.g. we will need
        # to wait until a reply to the command is received.
        with command_lock:
            connection.write(message.to_bytes())

    def rx_dispatch(self) -> None:
        # TODO acquire a lock and keep it, only one of these threads should run at once
        while True:
            message_bytes = self.connection.read(6)
            message_header = AptMessageForStreamParsing.from_bytes(message_bytes)
            if message_header.data_length == 0:
                pass
            else:
                message_bytes = message_bytes + self.connection.read(message_header.data_length)
            print()
