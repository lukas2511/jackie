import threading
import subprocess
import socket
import time
from . import base

class AlsaOutput(base.Object):
    def __init__(self, name, device, nchannels=2, quality=None, rate=48000, period=256):
        self.name = name
        self.device = device
        self.nchannels = nchannels
        self.quality = quality
        self.rate = rate
        self.period = period

        self.in_ports = []
        for i in range(self.nchannels):
            self.in_ports.append("%s:playback_%d" % (self.name, i+1))

        base.Object.__init__(self)

    def run(self):
        def target():
            while self.running:
                try:
                    self.process = subprocess.Popen(["zita-j2a", "-j", self.name, "-d", self.device, "-r", str(self.rate), "-p", str(self.period), "-c", str(self.nchannels)] + (["-Q", str(self.quality)] if self.quality else []), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    self.output, self.error = self.process.communicate()
                    self.status = self.process.returncode
                except:
                    self.error = traceback.format_exc()
                    self.status = -1
                for i in range(10):
                    if not self.running:
                        break
                    time.sleep(0.5)

        self.thread = threading.Thread(target=target)
        self.thread.start()

class AlsaInput(base.Object):
    def __init__(self, name, device, nchannels=2, quality=None, rate=48000, period=256):
        self.name = name
        self.device = device
        self.nchannels = nchannels
        self.quality = quality
        self.rate = rate
        self.period = period

        self.out_ports = []
        for i in range(self.nchannels):
            self.out_ports.append("%s:capture_%d" % (self.name, i+1))

        base.Object.__init__(self)

    def run(self):
        def target():
            while self.running:
                try:
                    self.process = subprocess.Popen(["zita-a2j", "-j", self.name, "-d", self.device, "-r", str(self.rate), "-p", str(self.period), "-c", str(self.nchannels)] + (["-Q", str(self.quality)] if self.quality else []), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    self.output, self.error = self.process.communicate()
                    self.status = self.process.returncode
                except:
                    self.error = traceback.format_exc()
                    self.status = -1
                for i in range(10):
                    if not self.running:
                        break
                    time.sleep(0.5)

        self.thread = threading.Thread(target=target)
        self.thread.start()
