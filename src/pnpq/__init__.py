"Python interface for Controlling Optical Devices in Quantum Networks"
__version__ = "0.0.1"
from .devices import OpticalDelayLine, Switch, Waveplate

__all__ = ["Waveplate", "Switch", "OpticalDelayLine"]


class pnpq:
    def __init__(self):
        pass
