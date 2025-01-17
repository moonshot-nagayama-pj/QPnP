from typing import Callable
from unittest.mock import Mock, create_autospec

from pnpq.apt.connection import AptConnection
from pnpq.apt.protocol import (
    Address,
    AptMessage,
    AptMessage_MGMSG_MOT_MOVE_ABSOLUTE,
    AptMessage_MGMSG_MOT_MOVE_COMPLETED_20_BYTES,
    ChanIdent,
    UStatus,
)
from pnpq.devices.refactored_waveplate_thorlabs_k10cr1 import WaveplateThorlabsK10CR1
from pnpq.units import pnpq_ureg


def test_move_absolute() -> None:

    connection = create_autospec(AptConnection)

    def mock_send_message_expect_reply(
        sent_message: AptMessage,
        match_reply_callback: Callable[
            [
                AptMessage,
            ],
            bool,
        ],
    ) -> None:
        if isinstance(sent_message, AptMessage_MGMSG_MOT_MOVE_ABSOLUTE):

            assert sent_message.absolute_distance == 10
            assert sent_message.chan_ident == ChanIdent(1)

            # A hypothetical reply message from the device
            reply_message = AptMessage_MGMSG_MOT_MOVE_COMPLETED_20_BYTES(
                chan_ident=sent_message.chan_ident,
                position=sent_message.absolute_distance,
                velocity=0,
                destination=Address.HOST_CONTROLLER,
                source=Address.GENERIC_USB,
                motor_current=0 * pnpq_ureg.milliamp,
                status=UStatus(INMOTIONCCW=True, INMOTIONCW=True, ENABLED=True),
            )

            assert match_reply_callback(reply_message)

    connection.send_message_expect_reply.side_effect = mock_send_message_expect_reply
    connection.tx_ordered_sender_awaiting_reply = Mock()
    connection.tx_ordered_sender_awaiting_reply.is_set = Mock(return_value=True)

    controller = WaveplateThorlabsK10CR1(connection=connection)

    controller.move_absolute(10 * pnpq_ureg.k10cr1_step)

    # One call for moving the motor. Enabling and disabling the channel doesn't use an expect reply in K10CR1
    assert connection.send_message_expect_reply.call_count == 1
