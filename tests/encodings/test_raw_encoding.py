"""Unit tests for RawEncoding class."""

import asyncio
from os import urandom
from struct import unpack
from unittest import TestCase, mock

from wsvnc.color import Color
from wsvnc.encodings.raw_encoding import RawEncoding
from wsvnc.pixel_format import PixelFormat
from wsvnc.utils.safe_transport import SafeTransport


class TestRawEncoding(TestCase):
    def setUp(self):
        self.transport_mock = mock.Mock(spec=SafeTransport)

    async def async_test_fetch_additonal_data_need_transport(self):
        enc = RawEncoding()
        
        pf = PixelFormat()
        pf.bpp = 32
        
        self.transport_mock.recvd = mock.AsyncMock(side_effect=[b'\x01\x02\x03\x04'])
        assert b'\x01\x02\x03\x04' == await enc.fetch_additional_data(1, 1, self.transport_mock, b"", pf)

    def test_true_color_raw_encoding(self):
        """Unit test for raw_encoding with true color flag set to true."""
        width=1
        height=10
        msg=urandom(40)
        
        pf = PixelFormat()
        pf.bpp=32
        pf.big_endian=1
        pf.true_color=1
        pf.red_shift=0
        pf.red_max=255
        pf.green_shift=8
        pf.green_max=255
        pf.blue_shift=16
        pf.blue_max=255
        
        enc = RawEncoding()
        bytes_read = enc.read(width, height, msg, pf)
        assert bytes_read == 40
        assert enc.img is not None
        
        for i in range(10):
            raw_pixel = unpack('>I', msg[i*4:4*(i+1)])[0]
            pixel = enc.img.getpixel((0, i))
            print(pixel)
            r = ((raw_pixel>>pf.red_shift & pf.red_max)&0xffff)
            g = ((raw_pixel>>pf.green_shift & pf.green_max)&0xffff)
            b = ((raw_pixel>>pf.blue_shift & pf.blue_max)&0xffff)
            assert pixel[0] == r
            assert pixel[1] == g
            assert pixel[2] == b

    def test_no_true_color_raw_encoding(self):
        """Unit test for raw_encoding with true_color flag set to false."""
        width=1
        height=1
        msg=b'\x00\x00\x00\x00'
        
        pf = PixelFormat()
        pf.bpp=32
        pf.big_endian=1
        pf.true_color=0
        pf.red_shift=0
        pf.red_max=256
        pf.green_shift=8
        pf.green_max=256
        pf.blue_shift=16
        pf.blue_max=256
        c = Color(r=15,b=10,g=20)
        pf.color_map={0: c}
        
        enc = RawEncoding()
        bytes_read = enc.read(width, height, msg, pf)
        assert bytes_read == 4
        assert enc.img.getpixel((0,0)) == (15,20,10,255)
        
    def test_type(self):
        """Verify type."""
        enc = RawEncoding()
        
        assert enc.type() == 0
    
    def test(self):
        asyncio.run(self.async_test_fetch_additonal_data_need_transport())