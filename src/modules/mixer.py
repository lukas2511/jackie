import threading
import subprocess
import socket
import time
from . import base
import math

class Mixer(base.Object):
    def __init__(self, name, control=None):
        self.name = name
        self.control = control if control is not None else ("/" + self.name)
        self.gain = 0.00

        self.in_ports = []
        self.in_ports.append("%s:in_left" % self.name)
        self.in_ports.append("%s:in_right" % self.name)
        self.out_ports = []
        self.out_ports.append("%s:out_left" % self.name)
        self.out_ports.append("%s:out_right" % self.name)

        base.Object.__init__(self)

    def run(self):
        def target():
            while self.running:
                try:
                    self.process = subprocess.Popen(["jacknanomix", "-n", self.name], stdin=subprocess.PIPE)
                    self.process.stdin.write(b"%.2f\n" % self.gain)
                    self.process.stdin.flush()
                    self.process.wait()
                    self.status = self.process.returncode
                except:
                    tracback.print_exc()
                    self.error = "exception"
                    self.status = -1
                if self.running:
                    time.sleep(5)
        self.thread = threading.Thread(target=target)
        self.thread.start()

    def set_gain(self, gain):
        self.gain = gain
        self.process.stdin.write(b"%.2f\n" % self.gain)
        self.process.stdin.flush()

    def stop(self):
        self.running = False
        if self.thread.is_alive():
            self.process.terminate()
            self.process.kill()
            self.thread.join()
        return self.status

