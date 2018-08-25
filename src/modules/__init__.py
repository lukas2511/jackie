from .mixer import Mixer
from .alsa import AlsaInput, AlsaOutput
from .network import NetworkInput, NetworkOutput
from .connmanager import ConnectionManager
from .system import SystemInput, SystemOutput
from .volmanager import VolumeManager, BCF2000

threads = []
Mixer.threads = threads
AlsaInput.threads = threads
AlsaOutput.threads = threads
NetworkInput.threads = threads
NetworkOutput.threads = threads
ConnectionManager.threads = threads
VolumeManager.threads = threads
BCF2000.threads = threads

def stop():
    for thread in threads:
        thread.running = False
    for thread in threads:
        #print("Stopping %s" % thread.name)
        thread.stop()
