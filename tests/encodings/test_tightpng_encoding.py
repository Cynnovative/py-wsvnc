"""Unit tests for RawEncoding class."""

import asyncio
from io import BytesIO
from os import urandom
from unittest import TestCase, mock

import numpy as np
from PIL import Image, ImageChops

from wsvnc.encodings.tightpng_encoding import TightPNGEncoding
from wsvnc.pixel_format import PixelFormat
from wsvnc.utils.safe_transport import SafeTransport


class TestTightPNGEncoding(TestCase):
    def setUp(self):
        self.transport_mock = mock.Mock(spec=SafeTransport)

    async def async_test_fetch_additional_data_need_transport(self):
        enc = TightPNGEncoding()
        
        # determine the byte data for 100 pixels
        byte_1 = 16
        byte_2 = 16
        byte_3 = 16
        data_length = byte_1
        data_length &= -129
        data_length += (byte_2 << 7)
        data_length &= -16385
        data_length += (byte_3 << 14)  
        
        random_bytes = urandom(data_length)
        #msg = b"\x10\x10\x10\x10" + random_bytes
        
        self.transport_mock.recvd = mock.AsyncMock(side_effect=[b'\x10\x10\x10\x10', random_bytes])
        ret_bytes = await enc.fetch_additional_data(0, 0, self.transport_mock, b"", PixelFormat())
        assert ret_bytes == bytearray(random_bytes)

    def test_tightpng_encoding_read(self):
        """Unit test for raw_encoding with true color flag set to true."""
        width=20
        height=20
        random_bytes=urandom(width * height * 3) # make fake RGB bytes
        
        # encode the bytes into an iamge
        image_array = np.frombuffer(random_bytes, dtype=np.uint8).reshape((height, width, 3))
        image = Image.fromarray(image_array)
        
        # encode into PNG
        png_buffer = BytesIO()
        image.save(png_buffer, format='PNG')
        png_bytes = png_buffer.getvalue()
        
        pf = PixelFormat()
        
        enc = TightPNGEncoding()
        enc.sub_encoding = enc.sub_enc_png
        enc.data_length = len(png_bytes)
        bytes_read = enc.read(width, height, png_bytes, pf)
        assert bytes_read == len(png_bytes)
        # this makes sure there is no difference between the images.
        assert not ImageChops.difference(image.convert('RGBA'), enc.img).getbbox()
        
    def test_tightpng_encoding_read_fill(self):
        enc = TightPNGEncoding()
        enc.sub_encoding = enc.sub_enc_fill
        assert 3 == enc.read(1, 1, b"\x01\x02\x03", PixelFormat())
        assert enc.img.getpixel((0, 0)) == (1,2,3,255)

    def test_tightpng_encoding_type(self):
        enc = TightPNGEncoding()
        assert enc.type() == -260

    def test(self):
        asyncio.run(self.async_test_fetch_additional_data_need_transport())

