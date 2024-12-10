from pnpq.apt.protocol import (
AptMessage_MGMSG_MOT_GET_STATUSUPDATE,
AptMessage_MGMSG_MOT_REQ_STATUSUPDATE,
AptMessage_MGMSG_MOT_REQ_USTATUSUPDATE,
AptMessage_MGMSG_MOT_GET_USTATUSUPDATE,
)
from pnpq.apt.protocol import ChanIdent, Address, UStatus, Status

msg = AptMessage_MGMSG_MOT_REQ_STATUSUPDATE(
    chan_ident=ChanIdent.CHANNEL_1,
    destination=Address.GENERIC_USB,
    source=Address.HOST_CONTROLLER
)
msgBytes = msg.to_bytes()
print(msgBytes)
print( msgBytes == b"\x80\x04\x01\x00\x50\x01")

newMsg = AptMessage_MGMSG_MOT_REQ_STATUSUPDATE.from_bytes(msgBytes)
print(newMsg == msg)

msg = AptMessage_MGMSG_MOT_GET_STATUSUPDATE(
    destination=Address.HOST_CONTROLLER,
    source=Address.BAY_1,
    chan_ident=ChanIdent.CHANNEL_1,
    position=1,
    enc_count=0,
    status=Status(CWHARDLIMIT=True, CCWHARDLIMIT=True, CWSOFTLIMIT=True)
)
msgBytes = msg.to_bytes()
print(msgBytes)
checkBytes = bytes.fromhex(
    "8104 0e00 81 22 01000100 000000000000 07000000"
)
print(checkBytes)
print( msgBytes == checkBytes )
