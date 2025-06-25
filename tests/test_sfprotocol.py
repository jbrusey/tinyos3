from tinyos3.packet.SFProtocol import SFProtocol

class DummyIO:
    def __init__(self):
        self.written = []
    def write(self, data):
        self.written.append(data)
    def flush(self):
        pass


def test_write_packet_sends_length_as_byte():
    io = DummyIO()
    prot = SFProtocol(io, io)
    pkt = b"\x01\x02\x03"

    prot.writePacket(pkt)

    assert io.written[0] == bytes([len(pkt)])
    assert io.written[1] == pkt
