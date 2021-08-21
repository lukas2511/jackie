#!/usr/bin/env python3

import modules
import time
import logging
import json
import sqlalchemy
import sqlalchemy.ext.declarative
import sqlalchemy.orm
import threading
from flask import Flask, render_template, request, redirect, url_for

DBBase = sqlalchemy.ext.declarative.declarative_base()
DBEngine = sqlalchemy.create_engine("sqlite:////opt/jackie/jackie.db", connect_args={'check_same_thread':False})

class DB:
    class Connection(DBBase):
        __tablename__ = 'connections'
        id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
        source = sqlalchemy.Column(sqlalchemy.String)
        sink = sqlalchemy.Column(sqlalchemy.String)

    class Mixer(DBBase):
        __tablename__ = 'mixers'
        id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
        name = sqlalchemy.Column(sqlalchemy.String)
        gain = sqlalchemy.Column(sqlalchemy.Float)
        mute = sqlalchemy.Column(sqlalchemy.Boolean)

DBBase.metadata.bind = DBEngine
DBBase.metadata.create_all()
DBSessionMaker = sqlalchemy.orm.sessionmaker(bind=DBEngine)
DBLock = threading.Lock()

connmanager = modules.ConnectionManager()

# ignore some apps connections
connmanager.ignores.append(lambda t, dev: dev.startswith('PortAudio')) # ignore PortAudio (e.g. Audacity)
connmanager.ignores.append(lambda t, dev: dev.startswith('alsoft')) # ignore alsoft (e.g. FlightGear)

# outputs
scarlett2i4_out = modules.AlsaOutput("Scarlett 2i4 Output", "hw:scarlett2i4", nchannels=4)
bluetooth_out = modules.AlsaOutput("Bluetooth Output", "hw:bluetooth", nchannels=2)
#headset_out = modules.AlsaOutput("VR Headset Output", "hw:unknowndev_3d3b", nchannels=2, rate=48000, period=2048)

# inputs
scarlett2i4_in = modules.AlsaInput("Scarlett 2i4 Input", "hw:scarlett2i4", nchannels=2)
#headset_in = modules.AlsaInput("VR Headset Input", "hw:unknowndev_3d3b", nchannels=2, period=2048)

# yolo
mixers = {}
with DBLock:
    s = DBSessionMaker()
    for m in s.query(DB.Mixer).all():
        mixers[m.id] = modules.Mixer("mixer_%d" % m.id, 0.0 if m.mute else m.gain)

    for c in s.query(DB.Connection).all():
        connmanager.connect(c.source, c.sink)

app = Flask(__name__)

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.route('/')
def web_index():
    context = {}
    context['sinks'] = sorted(connmanager.get_sinks())
    context['sources'] = sorted(connmanager.get_sources())
    context['connections'] = connmanager.ensure
    with DBLock:
        s = DBSessionMaker()
        context['mixers'] = s.query(DB.Mixer).all()
    return render_template("index.html", **context)

@app.route('/addmixer', methods=['POST'])
def web_addmixer():
    with DBLock:
        m = DB.Mixer()
        m.name = request.form["name"]
        m.gain = float(request.form["gain"])
        m.mute = False
        s = DBSessionMaker()
        s.add(m)
        s.commit()
        mixers[m.id] = modules.Mixer("mixer_%d" % m.id, m.gain)
        time.sleep(0.5)

    return redirect("/")

@app.route('/delmixer', methods=['POST'])
def web_delmixer():
    mid = int(request.form["mixer"])
    if mid not in mixers:
        return redirect("/")

    mixers[mid].stop()
    del mixers[mid]
    with DBLock:
        s = DBSessionMaker()
        s.query(DB.Mixer).filter(DB.Mixer.id==mid).delete()
        s.commit()

    return redirect("/")

@app.route('/setmixername', methods=['POST'])
def web_setmixername():
    mid = int(request.form["mixer"])
    if mid not in mixers:
        return redirect("/")
    with DBLock:
        s = DBSessionMaker()
        m = s.query(DB.Mixer).filter(DB.Mixer.id==mid).first()
        m.name = request.form["name"]
        s.commit()
    return redirect("/")

@app.route('/mixerinfo')
def web_mixerinfo():
    mid = int(request.args.get("mixer"))
    if mid not in mixers:
        return "{}"
    with DBLock:
        s = DBSessionMaker()
        m = s.query(DB.Mixer).filter(DB.Mixer.id==mid).first()
        return json.dumps({'id': m.id, 'gain': m.gain, 'mute': m.mute, 'name': m.name})

@app.route('/setgain', methods=['POST'])
def web_setgain():
    mid = int(request.form["mixer"])
    gain = float(request.form["gain"])
    if mid not in mixers:
        return redirect("/")

    with DBLock:
        s = DBSessionMaker()
        m = s.query(DB.Mixer).filter(DB.Mixer.id==mid).first()
        m.gain = gain
        s.commit()

    mixers[mid].set_gain(0.0 if m.mute else m.gain)
    return redirect("/")

@app.route('/setmute', methods=['POST'])
def web_setmute():
    mid = int(request.form["mixer"])

    if mid not in mixers:
        return redirect("/")

    with DBLock:
        s = DBSessionMaker()
        m = s.query(DB.Mixer).filter(DB.Mixer.id==mid).first()
        if request.form["action"] == "toggle":
            m.mute = not m.mute
        elif request.form["action"] == "mute":
            m.mute = True
        else:
            m.mute = False
        s.commit()

    mixers[mid].set_gain(0.0 if m.mute else m.gain)
    return redirect("/")

@app.route('/connect', methods=['POST'])
def web_connect():
    with DBLock:
        c = DB.Connection()
        c.source = request.form["source"]
        c.sink = request.form["sink"]
        if connmanager.connect(c.source, c.sink):
            s = DBSessionMaker()
            s.add(c)
            s.commit()

    return redirect("/")

@app.route('/disconnect', methods=['POST'])
def web_disconnect():
    with DBLock:
        s = DBSessionMaker()
        s.query(DB.Connection).filter(DB.Connection.source==request.form["source"], DB.Connection.sink==request.form["sink"]).delete()
        connmanager.disconnect(request.form['source'], request.form['sink'])
        s.commit()

    return redirect("/")

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=1928)
    modules.stop()
