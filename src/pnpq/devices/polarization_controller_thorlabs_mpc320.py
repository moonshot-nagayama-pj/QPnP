import pnpq.apt
import serial.tools.list_ports
import structlog
import threading
import time

from ..apt.protocol import (
    Address,
    AptMessage,
    AptMessageForStreamParsing,
    AptMessageId,
    AptMessage_MGMSG_HW_START_UPDATEMSGS,
    AptMessage_MGMSG_HW_STOP_UPDATEMSGS,
    AptMessage_MGMSG_MOD_SET_CHANENABLESTATE,
    AptMessage_MGMSG_MOT_ACK_USTATUSUPDATE,
    AptMessage_MGMSG_MOT_MOVE_ABSOLUTE,
    AptMessage_MGMSG_MOT_MOVE_HOME,
    AptMessage_MGMSG_MOT_REQ_USTATUSUPDATE,
    AptMessage_MGMSG_MOT_RESUME_ENDOFMOVEMSGS,
    ChanIdent,
    EnableState,
)
from dataclasses import dataclass, field
from pathlib import Path
from serial import Serial

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.WriteLoggerFactory(
        file=Path("target/app").with_suffix(".log").open("a")
    ),
)


@dataclass(frozen=True, kw_only=True)
class PolarizationControllerThorlabsMPC320:
    # Serial connection parameters
    baudrate: int = 115200
    bytesize: int = serial.EIGHTBITS
    exclusive: bool = True
    parity: str = serial.PARITY_NONE
    rtscts: bool = True
    stopbits: int = serial.STOPBITS_ONE
    timeout: None | int = (
        None  # None means wait forever, until the requested number of bytes are received
    )

    connection: Serial = field(init=False)
    ack_sender: threading.Thread = field(init=False)
    rx_dispatcher: threading.Thread = field(init=False)
    ack_lock: threading.Lock = field(default_factory=threading.Lock)
    command_lock: threading.Lock = field(default_factory=threading.Lock)
    dispatch_lock: threading.Lock = field(default_factory=threading.Lock)
    log = structlog.get_logger()

    serial_number: str

    def __post_init__(self) -> None:
        self.log.debug("Starting post-init...")

        port_found = False
        for port in serial.tools.list_ports.comports():
            if port.serial_number == self.serial_number:
                port_found = True
                break
        if not port_found:
            raise ValueError(
                f"Serial number {self.serial_number} could not be found, failing intialization."
            )

        object.__setattr__(
            self,
            "connection",
            Serial(
                baudrate=self.baudrate,
                bytesize=self.bytesize,
                exclusive=self.exclusive,
                parity=self.parity,
                port=port.device,
                rtscts=self.rtscts,
                stopbits=self.stopbits,
                timeout=self.timeout,
            ),
        )
        object.__setattr__(
            self,
            "ack_sender",
            threading.Thread(target=self.tx_ack, daemon=True),
        )
        self.ack_sender.start()

        object.__setattr__(
            self,
            "rx_dispatcher",
            threading.Thread(target=self.rx_dispatch, daemon=True),
        )
        self.rx_dispatcher.start()

        # Disable and then re-enable all three channels
        for enable_state in (EnableState.CHANNEL_DISABLED, EnableState.CHANNEL_ENABLED):
            self.send_message(
                AptMessage_MGMSG_MOD_SET_CHANENABLESTATE(
                    chan_ident=(
                        ChanIdent.CHANNEL_1 | ChanIdent.CHANNEL_2 | ChanIdent.CHANNEL_3
                    ),
                    enable_state=enable_state,
                    destination=Address.GENERIC_USB,
                    source=Address.HOST_CONTROLLER,
                )
            )
        self.send_message(
            AptMessage_MGMSG_MOT_RESUME_ENDOFMOVEMSGS(
                destination=Address.GENERIC_USB,
                source=Address.HOST_CONTROLLER,
            )
        )

        self.log.debug("Finishing post-init...")

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

        # It's not necessarily the case that we need to syncrhonize
        # writes to the port to avoid interleaved text from other
        # threads (the underlying os.write() may handle this for us,
        # I'm not totally sure) but eventually we will need to prevent
        # more than one command running at the same time, e.g. we will
        # need to wait until a reply to the command is received.
        with self.command_lock:
            self.log.debug("Sending message", sent_message=message)
            self.connection.write(message.to_bytes())
            self.connection.flush()
        return None

    def rx_dispatch(self) -> None:
        with self.dispatch_lock:
            while True:
                self.log.debug("Ready to receive message...")
                message_bytes = self.connection.read(6)
                self.connection.flush()
                message = AptMessageForStreamParsing.from_bytes(message_bytes)
                if message.message_id in AptMessageId:
                    message_id = AptMessageId(message.message_id)
                    if message.data_length != 0:
                        message_bytes = message_bytes + self.connection.read(
                            message.data_length
                        )
                    message = getattr(
                        pnpq.apt.protocol, f"AptMessage_{message_id.name}"
                    ).from_bytes(message_bytes)
                self.log.debug("Received message", received_message=message)

    def tx_ack(self) -> None:
        with self.ack_lock:
            while True:
                self.send_message(
                    AptMessage_MGMSG_MOT_REQ_USTATUSUPDATE(
                        chan_ident=ChanIdent.CHANNEL_1,
                        destination=Address.GENERIC_USB,
                        source=Address.HOST_CONTROLLER,
                    )
                )
                self.send_message(
                    AptMessage_MGMSG_MOT_REQ_USTATUSUPDATE(
                        chan_ident=ChanIdent.CHANNEL_2,
                        destination=Address.GENERIC_USB,
                        source=Address.HOST_CONTROLLER,
                    )
                )
                self.send_message(
                    AptMessage_MGMSG_MOT_REQ_USTATUSUPDATE(
                        chan_ident=ChanIdent.CHANNEL_3,
                        destination=Address.GENERIC_USB,
                        source=Address.HOST_CONTROLLER,
                    )
                )
                self.send_message(
                    AptMessage_MGMSG_MOT_ACK_USTATUSUPDATE(
                        destination=Address.GENERIC_USB,
                        source=Address.HOST_CONTROLLER,
                    )
                )
                time.sleep(0.1)

    def home(self, chan_ident: ChanIdent) -> None:
        self.send_message(
            AptMessage_MGMSG_MOT_MOVE_HOME(
                chan_ident=chan_ident,
                destination=Address.GENERIC_USB,
                source=Address.HOST_CONTROLLER,
            )
        )
        time.sleep(1)

    def move_absolute(self, chan_ident: ChanIdent, absolute_degree: float) -> None:
        if absolute_degree < 0 or absolute_degree > 170:
            raise ValueError(
                f"Absolute degree must be between 0 and 170. Value given was {absolute_degree}"
            )
        absolute_distance = round(absolute_degree * (1370 / 170))
        self.send_message(
            AptMessage_MGMSG_MOT_MOVE_ABSOLUTE(
                chan_ident=chan_ident,
                absolute_distance=absolute_distance,
                destination=Address.GENERIC_USB,
                source=Address.HOST_CONTROLLER,
            )
        )
        time.sleep(1)

    def start_status_updates(self) -> None:
        self.send_message(
            AptMessage_MGMSG_HW_START_UPDATEMSGS(
                destination=Address.GENERIC_USB,
                source=Address.HOST_CONTROLLER,
            )
        )

    def stop_status_updates(self) -> None:
        self.send_message(
            AptMessage_MGMSG_HW_STOP_UPDATEMSGS(
                destination=Address.GENERIC_USB,
                source=Address.HOST_CONTROLLER,
            )
        )
