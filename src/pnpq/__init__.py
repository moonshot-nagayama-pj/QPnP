#
#  Copyright (C) 2024 Moontshot Nagayama Project
#

"Python interface for Controlling Optical Devices in Quantum Networks"
__version__ = "0.0.1"
from .devices import *

__all__ = ["pnpq", "Waveplate", "Switch"]


class pnpq:
    def __init__(self):
        pass


# def list_devices():
#    return "Hello from pnpq!"
