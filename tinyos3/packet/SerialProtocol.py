#
# Copyright (c) 2005-2006
#      The President and Fellows of Harvard College.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name of the University nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE UNIVERSITY AND CONTRIBUTORS ``AS IS'' AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE UNIVERSITY OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGE.
#
# Author: Geoffrey Mainland <mainland@eecs.harvard.edu>
#
# Author: Doug Carlson <carlson@cs.jhu.edu>
#  - Assign constants from Serial.py
#  - Add sequence number
#  - Handle acknowledgements correctly

import logging
from threading import Lock, Condition, Thread
from .IO import IODone
from .Serial import Serial

SYNC_BYTE = Serial.HDLC_FLAG_BYTE
B_SYNC_BYTE = (SYNC_BYTE).to_bytes(1, byteorder="big")
ESCAPE_BYTE = Serial.HDLC_CTLESC_BYTE
B_ESCAPE_BYTE = (ESCAPE_BYTE).to_bytes(1, byteorder="big")
MTU = 256

P_ACK = Serial.SERIAL_PROTO_ACK
P_PACKET_ACK = Serial.SERIAL_PROTO_PACKET_ACK
P_PACKET_NO_ACK = Serial.SERIAL_PROTO_PACKET_NOACK
P_UNKNOWN = Serial.SERIAL_PROTO_PACKET_UNKNOWN

logger = logging.getLogger(__name__)
TX_ATTEMPT_LIMIT = 1


class NoAckException(Exception):
    pass


def hex(x: int):
    return f"0x{x:02X}"


class RXThread(Thread):
    def __init__(self, prot):
        Thread.__init__(self)
        self.prot = prot

    def run(self):
        while True:
            try:
                frame = self.prot.readFramedPacket()
                frameType = ord(frame[0])
                pdataOffset = 1
                if frameType == P_PACKET_ACK:
                    # send an ACK
                    self.prot.writeFramedPacket(P_ACK, frame[1], b"", 0)
                    pdataOffset = 2
                packet = frame[pdataOffset:]

                if frameType == P_ACK:
                    with self.prot.ackCV:
                        if self.prot.lastAck:
                            logger.debug("Warning: last ack not cleared")
                        self.prot.lastAck = packet
                        self.prot.ackCV.notify()
                else:
                    with self.prot.dataCV:
                        self.prot.lastData = packet
                        self.prot.dataCV.notify()
            # OK, kind of ugly. finishing the SerialSource (ThreadTask)
            # leads (ultimately) to an IODone exception coming up
            # through here. At this point, the thread should complete.
            except IODone:
                with self.prot.ackCV:
                    self.prot.lastAck = None
                    self.prot.ackCV.notify()
                with self.prot.dataCV:
                    self.prot.lastData = None
                    self.prot.dataCV.notify()
                break


class SerialProtocol:
    def __init__(self, ins, outs):
        self.ins = ins
        self.outs = outs

        self.inSync = False
        self.seqNo = 0

        self.receiveBuffer = bytes(MTU)

        self.received = [None] * 256
        self.received[P_ACK] = []
        self.received[P_PACKET_NO_ACK] = []
        rxLock = Lock()
        self.dataCV = Condition(rxLock)
        self.ackCV = Condition(rxLock)
        self.lastData = None
        self.lastAck = None

    # also a little ugly: can't start this thread until the
    # serial.Serial object has been opened. This should all be
    # encapsulated in a single constructor.
    def open(self):
        self.rxThread = RXThread(self)
        self.rxThread.start()

    def readPacket(self):
        with self.dataCV:
            self.dataCV.wait()
            return self.lastData

    def readFramedPacket(self) -> bytes:
        count = 0
        escaped = False
        receiveBuffer = ""

        while True:
            if not self.inSync:
                logger.debug("resynchronizing...",)

                while self.ins.read(1) != B_SYNC_BYTE:
                    self.outs.write(B_SYNC_BYTE)
                    self.outs.write(B_SYNC_BYTE)
                logger.debug("synchronized")

                self.inSync = True
                count = 0
                escaped = False

                continue

            if count >= MTU:
                logger.debug("packet too long")
                self.inSync = False
                continue

            b = self.ins.read(1)[0]

            if escaped:
                if b == SYNC_BYTE:
                    # sync byte following escape is an error, resync
                    logger.debug("unexpected sync byte")
                    self.inSync = False
                    continue

                b ^= 0x20
                escaped = False
            elif b == ESCAPE_BYTE:
                escaped = True
                continue
            elif b == SYNC_BYTE:
                if count < 4:
                    # too-small frames are ignored
                    count = 0
                    continue

                packet = receiveBuffer[0 : count - 2]
                readCrc = receiveBuffer[count - 2] | (receiveBuffer[count - 1] << 8)
                computedCrc = crc(packet)

                logger.debug(" len: %d", len(receiveBuffer))
                logger.debug(" rcrc: %x ccrc: %x", readCrc, computedCrc)

                if readCrc == computedCrc:
                    return packet
                else:
                    logger.debug("bad packet")
                    logger.debug(receiveBuffer)
                    # We don't lose sync here. If we did, garbage on the line at
                    # startup will cause loss of the first packet.
                    count = 0
                    receiveBuffer = ""
                    continue

            receiveBuffer += (b).to_bytes(1, byteorder="big")
            count += 1

    def writePacket(self, data: bytes) -> None:
        logger.debug("Writing packet:")
        logger.debug(" ".join(map(hex, data)))
        attemptsLeft = TX_ATTEMPT_LIMIT
        self.seqNo = (self.seqNo + 1) % 256
        while attemptsLeft:
            attemptsLeft -= 1
            try:
                self.writeFramedPacket(P_PACKET_ACK, self.seqNo, data)
                break
            except NoAckException:
                logger.debug("NO ACK: %s", self.seqNo)

    def writeFramedPacket(self, frameType: int, sn: int, data: bytes) -> None:
        crc = 0
        frame = b""

        frame += B_SYNC_BYTE

        crc = crcByte(crc, frameType)
        frame += self.escape(frameType)

        crc = crcByte(crc, sn)
        frame += self.escape(sn)

        for c in data:
            crc = crcByte(crc, c)
            frame += self.escape(c)

        frame += self.escape(crc & 0xFF)
        frame += self.escape(crc >> 8)

        frame += B_SYNC_BYTE
        logger.debug("Framed Write: (%x) %s", sn, " ".join(map(hex, frame)))
        self.outs.write(frame)
        with self.ackCV:
            self.ackCV.wait(0.25)
            if not self.lastAck or self.lastAck[0] != sn:
                raise NoAckException("No serial ACK received")
            self.lastAck = None

    def escape(self, b: int) -> bytes:
        if b == SYNC_BYTE or b == ESCAPE_BYTE:
            return B_ESCAPE_BYTE + (b ^ 0x20).to_bytes(1, byteorder="big")
        else:
            return (b).to_bytes(1, byteorder="big")


def crc(data: bytes) -> int:
    crc = 0

    for b in data:
        crc = crcByte(crc, b)

    return crc


def crcByte(crc: int, b: int) -> int:
    crc = crc ^ b << 8

    for i in range(0, 8):
        if (crc & 0x8000) == 0x8000:
            crc = crc << 1 ^ 0x1021
        else:
            crc = crc << 1

    return crc & 0xFFFF
