import asyncio
from unittest import TestCase, mock

from wsvnc.encodings.tightdiff_comp_encoding import TightPNGDiffCompEncoding
from wsvnc.pixel_format import PixelFormat
from wsvnc.utils.safe_transport import SafeTransport


class TestTightPNGDiffCompEncoding(TestCase):
    def setUp(self):
        self.transport_mock = mock.Mock(spec=SafeTransport)
        
    async def async_test_fetch_additional_data(self):
        enc = TightPNGDiffCompEncoding()
        assert b"" == await enc.fetch_additional_data(0,0, self.transport_mock, b"", PixelFormat())    

    def test_type(self):
        assert 1464686102 == TightPNGDiffCompEncoding().type()
        
    def test_read(self):
        enc = TightPNGDiffCompEncoding()
        assert enc.read(0, 0, b"", PixelFormat()) == 0
    
    def test(self):
        asyncio.run(self.async_test_fetch_additional_data())