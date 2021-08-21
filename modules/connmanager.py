import threading
import time
import jack
import traceback
from . import base

class ConnectionManager(object):
    def __init__(self):
        self.ensure = {}

        self.ignores = []
        self.name = "ConnectionManager"
        self.client = jack.Client("connmanager")
        self.running = True
        self.run()
        self.threads.append(self)

    def get_sources(self):
        return list([x.name for x in self.client.get_ports(is_audio=True, is_output=True)])

    def get_sinks(self):
        return list([x.name for x in self.client.get_ports(is_audio=True, is_input=True)])

    def connect(self, source, sink):
        if source not in self.ensure:
            self.ensure[source] = []
        if sink not in self.ensure[source]:
            self.ensure[source].append(sink)
            return True
        return False

    def disconnect(self, source, sink):
        if source not in self.ensure:
            return
        if sink in self.ensure[source]:
            self.ensure[source].remove(sink)

    def ensure_connections(self):
        ports = {}
        connections = {}
        for port in self.client.get_ports(is_audio=True):
            ports[port.name] = port
            connections[port.name] = list(c.name for c in self.client.get_all_connections(port))

        for sink in self.client.get_ports(is_audio=True, is_input=True):
            del connections[sink.name]

        for source, sinks in connections.items():
            for sink in sinks:
                if source not in self.ensure or sink not in self.ensure[source]:
                    if any([ign('source', source) or ign('sink', sink) for ign in self.ignores]):
                        continue
                    print("Disconnecting '%s' and '%s'" % (source, sink))
                    self.client.disconnect(source, sink)

        for source, sinks in self.ensure.items():
            for sink in sinks:
                skip = False

                if sink not in ports:
                    #print("Missing sink %s" % sink)
                    skip=True

                if source not in ports:
                    #print("Missing source %s" % source)
                    skip=True

                if not skip and sink not in connections[source]:
                    print("Connecting '%s' and '%s'" % (source, sink))
                    self.client.connect(source, sink)

    def run(self):
        def target():
            while self.running:
                try:
                    self.ensure_connections()
                except:
                    print("Something went wrong while connecting things, but I don't really care...")
                    traceback.print_exc()
                if self.running:
                    time.sleep(1)

        self.thread = threading.Thread(target=target)
        self.thread.start()

    def stop(self):
        self.running = False
        self.thread.join()
