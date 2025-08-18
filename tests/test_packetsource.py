from unittest.mock import patch

from tinyos3.packet.PacketSource import PacketSource
from tinyos3.packet.IO import IODone


class DummyDispatcher:
    def dispatchPacket(self, source, packet):
        pass


class FlakySource(PacketSource):
    def __init__(self, fail_times=1):
        PacketSource.__init__(self, DummyDispatcher())
        self.fail_times = fail_times
        self.attempts = 0

    def open(self):
        self.attempts += 1
        if self.attempts <= self.fail_times:
            raise ConnectionRefusedError()

    def readPacket(self):
        raise IODone()


def test_retries_until_open_succeeds():
    src = FlakySource(fail_times=2)
    with patch("tinyos3.packet.PacketSource.time.sleep", return_value=None) as sleep:
        src.__call__()

    assert src.attempts == 3
    assert sleep.call_count == 2

