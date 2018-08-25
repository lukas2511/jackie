from . import base

class SystemInput(base.Object):
    def __init__(self, out_ports, name=None):
        if name is not None:
            self.name = name
        else:
            self.name = " ".join(out_ports)
        self.out_ports = out_ports

class SystemOutput(base.Object):
    def __init__(self, in_ports, name=None):
        if name is not None:
            self.name = name
        else:
            self.name = " ".join(in_ports)
        self.in_ports = in_ports
