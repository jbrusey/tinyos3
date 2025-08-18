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
import logging
import signal
import sys
import time
import traceback

from .IO import *
from .ThreadTask import *
from threading import Semaphore

logger = logging.getLogger(__name__)

runner = ThreadTaskRunner()


def finishAll():
    runner.cancelAll()
    runner.finish()


class PacketSourceException(Exception):
    def __init__(self, *args):
        self.args = args


class PacketSource(ThreadTask):
    def __init__(self, dispatcher):
        ThreadTask.__init__(self, runner)
        self.dispatcher = dispatcher
        self.semaphore = Semaphore(1)
        self.semaphore.acquire()

    def __call__(self):
        try:
            while True:
                try:
                    self.open()
                    break
                except OSError as e:
                    if self.isDone():
                        self.finish()
                        return
                    logger.debug("open failed: %s", e)
                    time.sleep(1)
        finally:
            self.semaphore.release()

        while not self.isDone():
            try:
                packet = self.readPacket()
            except IODone:
                logger.debug("IO finished")
                break

            if packet:
                logger.debug("About to run packet dispatcher!")
                logger.debug("packet=%s", packet)
                # for i in packet:
                #     print(i, " ", end=" ")
                # print()

                self.dispatcher.dispatchPacket(self, packet)

        self.close()

        self.finish()

    def start(self):
        runner.start(self)

    def open(self):
        pass

    def close(self):
        pass

    def readPacket(self):
        return None

    def writePacket(self, packet):
        pass
