import threading
from pythonosc import dispatcher
from pythonosc import osc_server
from pythonosc import udp_client
from pythonosc import osc_message_builder
from . import base
import time
import sqlalchemy
import sqlalchemy.ext.declarative
import sqlalchemy.orm
import threading
import traceback
import http.server
import xmltodict
import base64

MAXGAIN = 1.0
DEFAULTGAIN = 0.8
DEFAULTMUTE = True

DBBase = sqlalchemy.ext.declarative.declarative_base()
DBEngine = sqlalchemy.create_engine("sqlite:////root/jackie/volumes.db", connect_args={'check_same_thread':False})

class Volume(DBBase):
    __tablename__ = 'volumes'
    control = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    value = sqlalchemy.Column(sqlalchemy.Float, nullable=False)
    muted = sqlalchemy.Column(sqlalchemy.Boolean, default=False)

DBBase.metadata.bind = DBEngine
DBBase.metadata.create_all()
DBSessionMaker = sqlalchemy.orm.sessionmaker(bind=DBEngine)
DBLock = threading.Lock()

class BCF2000(base.Object):
    BUTTONS = [
        # knob buttons
        32, 33, 34, 35, 36, 37, 38, 39,
        # first row
        16, 17, 18, 19, 20, 21, 22, 23,
        # second row
        24, 25, 26, 27, 28, 29, 30, 31,
        # store/learn/etc.
        42, 43, 44, 45,
        # preset
        46, 47,
        # bottom right
        91, 92, 93, 94,
        # faders
        104, 105, 106, 107, 108, 109, 110, 111
    ]

    def __init__(self, callback=None, mididev="/dev/bcf2000"):
        self.name = "BCF2000"
        self.r = open(mididev, "rb")
        self.w = open(mididev, "wb")
        self.callback = callback
        self.running = True
        base.Object.__init__(self)

    def write(self, data):
        self.w.write(bytes(data))
        self.w.flush()

    def parse(self, data):
        output = {'type': 'raw', 'data': data}
        if data[0] & 0xf0 == 0xe0:
            output['type'] = 'fader'
            output['fader'] = data[0] & 0x0f
            output['value'] = (data[1] + (data[2] * 127)) / 16256 * MAXGAIN
        elif data[0] & 0xf0 == 0x90:
            output['type'] = 'button'
            output['button'] = self.BUTTONS.index(data[1])
            output['value'] = 1 if data[2] == 0x7f else 0

        return output

    def run(self):
        def readloop():
            while self.running:
                try:
                    data = self.r.read(1)
                    while not data[0] & 0x80:
                        data = self.r.read(1)
                    data += self.r.read(2)

                    if self.callback:
                        self.callback(self.parse(data))
                except:
                    traceback.print_exc()
        self.thread = threading.Thread(target=readloop)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.running = False

    def set_fader(self, fader, value):
        if value > MAXGAIN:
            value = MAXGAIN
        elif value < 0.0:
            value = 0.0
        value = int(value / MAXGAIN * 16255)
        data = [0xe0 + fader, value & 127, value // 127]
        self.write(data)

    def set_led(self, led, value):
        data = [0x90, self.BUTTONS[led], 127 if value else 0]
        self.write(data)

class TouchOSCHTTPHandler(http.server.BaseHTTPRequestHandler):
    def b64(self, a):
        return base64.b64encode(a.encode()).decode()

    def generate_xml(self):
        layout = {}
        layout['@version'] = 16
        layout['@mode'] = 3
        layout['@w'] = 414
        layout['@h'] = 736
        layout['@orientation'] = 'vertical'
        layout['tabpage'] = []

        for o, inputs in enumerate(self.mixermatrix):
            outname = inputs[0].name.split(" to ")[1]
            tabpage = {}
            tabpage['@name'] = self.b64(outname)
            tabpage['@scalef'] = 0.0
            tabpage['@scalet'] = 1.0
            tabpage['@osc_cs'] = self.b64("/refresh")
            tabpage['@li_t'] = self.b64(outname)
            tabpage['@li_c'] = 'gray'
            tabpage['@li_s'] = 14
            tabpage['@li_o'] = 'false'
            tabpage['@li_b'] = 'false'
            tabpage['@la_t'] = self.b64(outname)
            tabpage['@la_c'] = 'gray'
            tabpage['@la_s'] = 14
            tabpage['@la_o'] = 'false'
            tabpage['@la_b'] = 'false'
            tabpage['control'] = []
            for i, mixer in enumerate(inputs):
                inname = mixer.name.split(" to ")[0]
                control = {}
                control['name'] = self.b64(inname)
                control['@x'] = 6 + 6 + 36
                control['@w'] = layout['@w'] - 46 - 6 - 6 - 36
                control['@h'] = int((layout['@h'] - 6) / len(inputs) - 6)
                control['@y'] = int(6 + (control['@h'] + 6) * i)
                control['@color'] = 'red'
                control['@scalef'] = 0.0
                control['@scalet'] = 1.0
                control['@osc_cs'] = self.b64("/%s" % mixer.name)
                control['@type'] = 'faderh'
                control['@response'] = 'absolute'
                control['@inverted'] = 'false'
                control['@centered'] = 'false'
                tabpage['control'].append(control)

                control = {}
                control['name'] = self.b64(inname)
                control['@x'] = 6
                control['@w'] = 36
                control['@h'] = int((layout['@h'] - 6) / len(inputs) - 6)
                control['@y'] = int(6 + (control['@h'] + 6) * i)
                control['@color'] = 'red'
                control['@scalef'] = 0.0
                control['@scalet'] = 1.0
                control['@osc_cs'] = self.b64("/mute/%s" % mixer.name)
                control['@type'] = 'push'
                control['@local_off'] = 'true'
                control['@sp'] = 'true'
                control['@sr'] = 'false'
                tabpage['control'].append(control)

                control = {}
                control['name'] = self.b64(inname)
                control['@x'] = 6
                control['@w'] = 36
                control['@h'] = int((layout['@h'] - 6) / len(inputs) - 6)
                control['@y'] = int(6 + (control['@h'] + 6) * i)
                control['@color'] = 'gray'
                control['@type'] = 'labelv'
                control['@text'] = self.b64(inname)
                control['@size'] = 14
                control['@background'] = 'false'
                control['@outline'] = 'false'
                tabpage['control'].append(control)

            layout['tabpage'].append(tabpage)

        return xmltodict.unparse({'layout': layout})


    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/touchosc')
        self.send_header('Content-Disposition', 'attachment; filename="jackie.touchosc"')
        self.end_headers()
        self.wfile.write(self.generate_xml().encode())

class VolumeManager(base.Object):
    def __init__(self, mixermatrix, iface=None, port=10000):
        self.name = "Volume Manager"
        self.mixermatrix = mixermatrix
        self.db = None

        self.bcf2000 = iface
        if self.bcf2000:
            self.bcf2000.callback = self.callback

        self.port = port
        self.touchosc = []

        self.page = 0
        self.controls = {}
        self.values = {}
        self.muted = {}

        self.changed = threading.Event()

        self.dispatcher = dispatcher.Dispatcher()
        self.dispatcher.map("/ping", self.ping)
        self.dispatcher.map("/*", self.responder)
        self.server = osc_server.ThreadingOSCUDPServer(('', self.port), self.dispatcher)

        self.lastping = 0.0
        base.Object.__init__(self)

        for output in self.mixermatrix:
            for control in output:
                self.add_control(control)

        if self.bcf2000:
            self.update_faders()

    def callback(self, data):
        try:
            if data['type'] == 'fader':
                if data['fader'] < len(self.mixermatrix[self.page]):
                    control = self.mixermatrix[self.page][data['fader']].control
                    self.set_volume(control, data['value'], self.muted[control])
            elif data['type'] == 'button':
                if data['value'] != 1:
                    return

                newpage = self.page
                if data['button'] in range(8, 16 +1) and data['button'] - 8 < len(self.mixermatrix):
                    newpage = data['button'] - 8
                elif data['button'] == 28 and newpage > 0:
                    newpage -= 1
                elif data['button'] == 29 and newpage < len(self.mixermatrix) - 1:
                    newpage += 1
                if newpage != self.page:
                    self.page = newpage
                    if self.bcf2000:
                        self.update_faders()

                if data['button'] in range(16, 24 +1):
                    control = self.mixermatrix[self.page][data['button'] - 16].control
                    if self.muted[control]:
                        self.set_volume(control, self.values[control], False)
                    else:
                        self.set_volume(control, self.values[control], True)
        except:
            traceback.print_exc()

    def update_faders(self):
        for i in range(8):
            self.bcf2000.set_led(8 + i, 1 if i == self.page else 0)
        for i, mixer in enumerate(self.mixermatrix[self.page]):
            self.bcf2000.set_fader(i, self.values[mixer.control])
            self.bcf2000.set_led(16 + i, self.muted[mixer.control])
        for i in range(len(self.mixermatrix[self.page]), 8):
            self.bcf2000.set_fader(i, 0)

    def update_touchosc(self):
        for control, value in self.values.items():
            msg = osc_message_builder.OscMessageBuilder(address=control)
            msg.add_arg(value)
            msg = msg.build()
            for touchosc in self.touchosc:
                touchosc.send(msg)
        for control, value in self.muted.items():
            msg = osc_message_builder.OscMessageBuilder(address="/mute" + control)
            msg.add_arg(1 if value else 0)
            msg = msg.build()
            for touchosc in self.touchosc:
                touchosc.send(msg)

    def responder(self, path, *values):
        if path[:5] == "/mute" and path[5:] in self.controls:
            self.set_volume(path[5:], self.values[path[5:]], not self.muted[path[5:]])
        elif path in self.controls:
            self.set_volume(path, values[0], self.muted[path])
        elif path == "/refresh":
            self.update_touchosc()

    def ping(self, *args):
        self.lastping = time.time()

    def set_volume(self, control, value, muted):
        self.controls[control].set_gain(value if not muted else 0.0)
        if self.controls[control] in self.mixermatrix[self.page]:
            fader = self.mixermatrix[self.page].index(self.controls[control])
            if self.bcf2000:
                self.bcf2000.set_fader(fader, value)
                self.bcf2000.set_led(16 + fader, muted)

        self.values[control] = value
        self.muted[control] = muted
        self.changed.set()

        msg = osc_message_builder.OscMessageBuilder(address=control)
        msg.add_arg(value)
        msg = msg.build()
        for touchosc in self.touchosc:
            touchosc.send(msg)

        msg = osc_message_builder.OscMessageBuilder(address="/mute" + control)
        msg.add_arg(1 if muted else 0)
        msg = msg.build()
        for touchosc in self.touchosc:
            touchosc.send(msg)

    def set_stored_volume(self, control, value, muted):
        with DBLock:
            s = DBSessionMaker()
            q = s.query(Volume).filter(Volume.control == control).all()
            if q:
                v = q[0]
                if v.value == value and v.muted == muted:
                    return
            else:
                v = Volume()
                v.control = control
                v.value = 1.0
                v.muted = muted
                s.add(v)

            v.value = value
            v.muted = muted
            s.commit()
            s.close()

    def get_stored_volume(self, control):
        with DBLock:
            s = DBSessionMaker()
            q = s.query(Volume).filter(Volume.control == control).all()
            if q:
                return q[0]
            else:
                return None
            s.close()

    def run(self):
        def storeloop():
            while self.running:
                try:
                    self.changed.wait()
                    for control in list(self.controls):
                        self.set_stored_volume(control, self.values[control], self.muted[control])
                    self.changed.clear()
                except:
                    traceback.print_exc()
        self.thread = threading.Thread(target=storeloop)
        self.thread.start()
        self.thread2 = threading.Thread(target=self.server.serve_forever)
        self.thread2.start()

        TouchOSCHTTPHandler.mixermatrix = self.mixermatrix
        self.webserver = http.server.HTTPServer(('', 9658), TouchOSCHTTPHandler)
        self.thread3 = threading.Thread(target=self.webserver.serve_forever)
        self.thread3.daemon = True
        self.thread3.start()

    def stop(self):
        self.running = False
        self.changed.set()
        self.server.shutdown()
        self.thread2.join()
        self.webserver.shutdown()
        self.thread3.join()

    def add_control(self, mixer):
        #print("VolManager: Adding '%s' to controls" % mixer.name)
        self.controls[mixer.control] = mixer
        stored = self.get_stored_volume(mixer.control)
        if stored is not None:
            self.set_volume(mixer.control, stored.value, stored.muted)
        else:
            self.set_volume(mixer.control, DEFAULTGAIN, DEFAULTMUTE)

    def add_touchosc(self, touchosc):
        self.touchosc.append(udp_client.SimpleUDPClient(touchosc, self.port))
