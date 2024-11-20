import asyncio
from unittest import TestCase, mock

from wsvnc.encodings.vmware_define_cursor_encoding import VMWDefineCursorEncoding
from wsvnc.pixel_format import PixelFormat
from wsvnc.utils.safe_transport import SafeTransport


class TestVMWDefineCursorEncoding(TestCase):
    def setUp(self):
        self.transport_mock = mock.Mock(spec=SafeTransport)
        
    async def async_test_fetch_additional_data_no_transport(self):
        enc = VMWDefineCursorEncoding()
        
        # cursor type is 1, the one pixel is the last 4 bytes
        msg = b"\x01\x00\x02\x03\x04\x05"
        self.transport_mock.recvd = mock.AsyncMock(side_effect=[msg, b"\x02\x03\x04\x05"])
        
        assert msg[2:] == await enc.fetch_additional_data(1,1, self.transport_mock, msg, PixelFormat())
    
    async def async_test_fetch_additional_data_need_transport(self):
        enc = VMWDefineCursorEncoding()
        # by setting the mask to 0 we'll need double the bytes
        self.transport_mock.recvd = mock.AsyncMock(side_effect=[b'\x00\x00', b"\x02\x03\x04\x05\x02\x03\x04\x05"])
        
        assert b"\x02\x03\x04\x05\x02\x03\x04\x05" == await enc.fetch_additional_data(1,1,self.transport_mock, b"", PixelFormat)

    def test_type(self):
        assert 1464686180 == VMWDefineCursorEncoding().type()
        
    def test_read(self):
        enc = VMWDefineCursorEncoding()
        enc.pixel_length = 10
        enc.mask_length = 10
        assert enc.read(0, 0, b"", PixelFormat()) == 20
    
    def test(self):
        asyncio.run(self.async_test_fetch_additional_data_no_transport())
        asyncio.run(self.async_test_fetch_additional_data_need_transport())