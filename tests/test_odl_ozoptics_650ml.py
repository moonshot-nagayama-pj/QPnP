from pnpq.devices.odl_ozoptics_650ml import OdlOzOptics

import pytest


def test_disconnected_initialization():
    with pytest.raises(RuntimeError):
        OdlOzOptics("ABC", "DEF")
