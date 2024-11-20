import asyncio
from unittest import TestCase, mock

from wsvnc.encodings.pseudo_desktop_size_encoding import PseudoDesktopSizeEncoding
from wsvnc.pixel_format import PixelFormat
from wsvnc.utils.safe_transport import SafeTransport


class TestPseduoDesktopEncoding(TestCase):
    def setUp(self):
        self.transport_mock = mock.Mock(spec=SafeTransport)
        
    async def async_test_fetch_additional_data(self):
        enc = PseudoDesktopSizeEncoding()
        assert b"" == await enc.fetch_additional_data(0,0, self.transport_mock, b"", PixelFormat())     
    
    def test_type(self):
        enc = PseudoDesktopSizeEncoding()
        assert enc.type() == -223
        
    def test_read(self):
        enc = PseudoDesktopSizeEncoding()
        assert enc.read(0, 0, b"", PixelFormat()) == 0
    
    def test(self):
        asyncio.run(self.async_test_fetch_additional_data())
        