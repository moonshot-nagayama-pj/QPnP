from waveplate_stub import WaveplateStub
from waveplate_stub import (
    DeviceDisconnectedError,
    WaveplateInvalidDegreeError,
)
import unittest

class TestStubWaveplate(unittest.TestCase):
    """Unit test case for WaveplateStub class"""
    def __init__(self, *args, **kwargs):
        super(TestStubWaveplate, self).__init__(*args, **kwargs)
        self.wp = WaveplateStub()

    def test_access_without_connection(self):
        # Test if there's a DeviceDisconnectedError
        self.assertRaises(DeviceDisconnectedError, self.wp.identify)

    def test_connect(self):
        self.wp.connect()
        # Test if there's no exception
        self.wp.identify()

    def test_rotate(self):
        self.wp.connect()
        self.wp.rotate(90)
        pos = self.wp.getpos()
        res = self.wp.resolution
        self.assertEqual(pos, 90*res)

    def test_rotate_invalid_degree(self):
        self.wp.connect()
        self.assertRaises(WaveplateInvalidDegreeError, self.wp.rotate, 361)

if __name__ == '__main__':
    unittest.main()
