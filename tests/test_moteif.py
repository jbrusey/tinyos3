from unittest.mock import patch

from tinyos3.message.MoteIF import MoteIF
from tinyos3.message.Message import Message
from tinyos3.message.SerialPacket import SerialPacket
from tinyos3.packet.Serial import Serial


class DummyDest:
    def __init__(self):
        self.packet = None

    def writePacket(self, packet):
        self.packet = packet


def test_send_msg_constructs_correct_packet():
    payload = b"\x01\x02\x03"
    msg = Message(payload)
    dest = DummyDest()

    with patch("tinyos3.utils.Watcher.Watcher.getInstance", return_value=object()):
        mote = MoteIF()

    mote.sendMsg(dest, addr=1, amType=2, group=3, msg=msg)

    serial_pkt = SerialPacket(None)
    serial_pkt.set_header_dest(1)
    serial_pkt.set_header_group(3)
    serial_pkt.set_header_type(2)
    serial_pkt.set_header_length(len(payload))
    header = serial_pkt.dataGet()[: serial_pkt.offset_data(0)]
    expected = bytes([Serial.TOS_SERIAL_ACTIVE_MESSAGE_ID]) + header + payload

    assert dest.packet == expected
