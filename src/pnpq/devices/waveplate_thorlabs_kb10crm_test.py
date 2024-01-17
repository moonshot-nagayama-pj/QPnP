from .waveplate_thorlabs_kb10crm import Waveplate

def test_init_waveplate():
    wp = Waveplate()
    wp.identify()
