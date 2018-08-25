import threading
import time
import jack
from . import base
import traceback

class ConnectionManager(object):
    def __init__(self):
        self.ensure = {}

        self.name = "ConnectionManager"
        self.running = True
        self.client = jack.Client("connmanager")
        self.run()
        self.threads.append(self)

    def connect(self, sources, sinks):
        if isinstance(sources, base.Object):
            sources = sources.out_ports

        if isinstance(sinks, base.Object):
            sinks = sinks.in_ports

        if isinstance(sources, list) and isinstance(sinks, str):
            oldsink = sinks
            sinks = []
            for source in sources:
                sinks.append(oldsink)
        elif isinstance(sources, str) and isinstance(sinks, list):
            oldsource = sources
            sources = []
            for sink in sinks:
                sources.append(oldsource)
        elif isinstance(sources, str) and isinstance(sinks, str):
            sinks = [sinks]
            sources = [sources]

        if len(sinks) == 1 and len(sources) != 1:
            oldsink = sinks[0]
            sinks = []
            for source in sources:
                sinks.append(oldsink)
        elif len(sources) == 1 and len(sinks) != 1:
            oldsource = sources[0]
            sources = []
            for sink in sinks:
                sources.append(oldsource)

        for key, source in enumerate(sources):
            if source not in self.ensure:
                self.ensure[source] = []
            if sinks[key] not in self.ensure[source]:
                self.ensure[source].append(sinks[key])

    def ensure_connections(self):
        ports = {}
        connections = {}
        for port in self.client.get_ports(is_audio=True):
            ports[port.name] = port
            connections[port.name] = list(c.name for c in self.client.get_all_connections(port))

        for sink in self.client.get_ports(is_audio=True, is_input=True):
            if sink.name in connections:
                del connections[sink.name]

        for source, sinks in connections.items():
            for sink in sinks:
                if source not in self.ensure or sink not in self.ensure[source]:
                    if not sink.startswith("meter"):
                        print("Disconnecting '%s' and '%s'" % (source, sink))
                        self.client.disconnect(source, sink)

        for source, sinks in self.ensure.items():
            for sink in sinks:
                skip = False

                if sink not in ports:
                    print("Missing sink %s" % sink)
                    skip=True

                if source not in ports:
                    print("Missing source %s" % source)
                    skip=True

                if not skip and sink not in connections[source]:
                    print("Connecting '%s' and '%s'" % (source, sink))
                    self.client.connect(source, sink)

    def run(self):
        def target():
            time.sleep(2)
            while self.running:
                try:
                    self.ensure_connections()
                except:
                    print("Next exception is ignored")
                    traceback.print_exc()
                if self.running:
                    time.sleep(1)

        self.thread = threading.Thread(target=target)
        self.thread.start()

    def stop(self):
        self.running = False
        self.thread.join()
