import threading
import subprocess
import socket
import time
from . import base

class NetworkInput(base.Object):
    def __init__(self, name, port, buf=100, bind="0.0.0.0"):
        self.name = name
        self.port = port
        self.buf = buf
        self.bind = bind

        self.out_ports = []
        self.out_ports.append("%s:out_%d" % (self.name, 1))
        self.out_ports.append("%s:out_%d" % (self.name, 2))

        base.Object.__init__(self)

    def run(self):
        def target():
            while self.running:
                try:
                    self.process = subprocess.Popen(["zita-n2j", "--jname", self.name, "--buf", str(self.buf), self.bind, str(self.port)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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

class NetworkOutput(base.Object):
    def __init__(self, name, dst, port, nchannels=2, sampletype="float", mtu=1000):
        self.name = name
        self.dst = dst
        self.port = port
        self.nchannels = nchannels
        self.sampletype = sampletype
        self.mtu = mtu

        self.in_ports = []
        for i in range(self.nchannels):
            self.in_ports.append("%s:in_%d" % (self.name, i+1))

        base.Object.__init__(self)

    def run(self):
        def target():
            while self.running:
                try:
                    self.process = subprocess.Popen(["zita-j2n", "--mtu", str(self.mtu), "--jname", self.name, "--%s" % self.sampletype, "--chan", str(self.nchannels), self.dst, str(self.port)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    self.output, self.error = self.process.communicate()
                    self.status = self.process.returncode
                except:
                    self.error = traceback.format_exc()
                    print(self.error)
                    self.status = -1
                for i in range(10):
                    if not self.running:
                        break
                    time.sleep(0.5)

        self.thread = threading.Thread(target=target)
        self.thread.start()

