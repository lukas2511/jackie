#!/usr/bin/env python3

import time
import os
import subprocess

if not os.path.exists("/dev/shm/jack-0-0"):
    subprocess.check_output(["systemctl", "start", "jackd"])
    time.sleep(10)

import modules

USE_BCF2000 = False
RATE = 48000
#96000
#192000

connmanager = modules.ConnectionManager()

def connect_with_mixer(out1, in1):
    mixer = modules.Mixer("%s to %s" % (out1.name, in1.name))
    connmanager.connect(out1, mixer)
    connmanager.connect(mixer, in1)
    return mixer

# Hardware Devices
scarlett2i4_in = modules.AlsaInput("Scarlett2i4 Input", "hw:scarlett2i4", rate=RATE)
scarlett2i4_out = modules.AlsaOutput("Scarlett2i4 Output", "hw:scarlett2i4", nchannels=4, rate=RATE)

# Virtual Devices
mic_1 = modules.SystemInput([scarlett2i4_in.out_ports[0]], name="Mic 1")
mic_2 = modules.SystemInput([scarlett2i4_in.out_ports[1]], name="Mic 2")

main_mix = modules.SystemOutput(scarlett2i4_out.in_ports[0:2], name="Main Mix")
#line_out_2 = modules.SystemOutput(scarlett2i4_out.in_ports[2:4], name="Line-Out 2")

line_in_1 = modules.AlsaInput("Line-In 1", "hw:uca222_1", rate=48000)
line_in_2 = modules.AlsaInput("Line-In 2", "hw:uca222_2", rate=48000)
line_in_3 = modules.AlsaInput("Line-In 3", "hw:uca222_3", rate=48000)

line_out_1 = modules.AlsaOutput("Line-Out 1", "hw:uca222_1", rate=48000)
line_out_2 = modules.AlsaOutput("Line-Out 2", "hw:uca222_2", rate=48000)
line_out_3 = modules.AlsaOutput("Line-Out 3", "hw:uca222_3", rate=48000)

# Used Devices
main_mix.name = "Main Mix"
line_out_2.name = "PC-Out"
line_out_3.name = "Notebook-Out"
outputs = [main_mix, line_out_2, line_out_3]

line_in_1.name = "Switch-In"
line_in_2.name = "PC-In"
line_in_3.name = "Notebook-In"
#pulse_in.name = "Pulseaudio"
inputs = [mic_1, mic_2, line_in_1, line_in_2, line_in_3]

mixer_matrix = []

# Mix
for o in outputs:
    mixer_matrix.append([])
    for i in inputs:
        mixer_matrix[-1].append(connect_with_mixer(i, o))

if USE_BCF2000:
    bcf2000 = modules.BCF2000()
    volmanager = modules.VolumeManager(mixer_matrix, iface=bcf2000)
else:
    volmanager = modules.VolumeManager(mixer_matrix)

volmanager.add_touchosc("10.25.11.35")

try:
    while True:
        time.sleep(1)
except:
    pass

modules.stop()
