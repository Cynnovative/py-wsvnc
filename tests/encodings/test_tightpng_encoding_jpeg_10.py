import asyncio
from unittest import TestCase, mock

from wsvnc.encodings.tightpng_encoding_jpeg_10 import TightPNGEncodingJpegQuality10
from wsvnc.pixel_format import PixelFormat
from wsvnc.utils.safe_transport import SafeTransport


class TestTightPNGJpeg10Encoding(TestCase):
    def setUp(self):
        self.transport_mock = mock.Mock(spec=SafeTransport)
    
    async def async_test_fetch_additional_data(self):
        enc = TightPNGEncodingJpegQuality10()
        assert b"" == await enc.fetch_additional_data(0,0, self.transport_mock, b"", PixelFormat()) 

    def test_type(self):
        assert TightPNGEncodingJpegQuality10().type() == -23
        
    def test_read(self):
        assert TightPNGEncodingJpegQuality10().read(0, 0, b"", PixelFormat()) == 0
    
    def test(self):
        asyncio.run(self.async_test_fetch_additional_data())