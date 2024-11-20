import asyncio
from unittest import TestCase, mock

from wsvnc.encodings.copyrect_encoding import CopyRectEncoding
from wsvnc.pixel_format import PixelFormat
from wsvnc.utils.safe_transport import SafeTransport


class TestCopyRectEncoding(TestCase):
    def setUp(self):
        self.transport_mock = mock.Mock(spec=SafeTransport)
    
    async def async_test_fetch_additional_data_need_transport(self):
        enc = CopyRectEncoding()
        self.transport_mock.recvd = mock.AsyncMock(side_effect=[b"\x01\x00\x02\x00"])
        
        assert b"\x01\x00\x02\x00" == await enc.fetch_additional_data(1,1,self.transport_mock, b"", PixelFormat)

    def test_type(self):
        assert 1 == CopyRectEncoding().type()
        
    def test_read(self):
        enc = CopyRectEncoding()
        assert enc.read(0, 0, b"\x01\x00\x02\x00", PixelFormat()) == 4
        assert enc.srcx == 256
        assert enc.srcy == 512
    
    def test(self):
        asyncio.run(self.async_test_fetch_additional_data_need_transport())