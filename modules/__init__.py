from .mixer import Mixer
from .alsa import AlsaInput, AlsaOutput
from .network import NetworkInput
from .connmanager import ConnectionManager

threads = []
Mixer.threads = threads
AlsaInput.threads = threads
AlsaOutput.threads = threads
NetworkInput.threads = threads
ConnectionManager.threads = threads

def stop():
    for thread in threads:
        thread.running = False
    for thread in threads:
        print("Stopping %s" % thread.name)
        thread.stop()
