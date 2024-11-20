"""Unit tests for FrameBufferUpdate class."""

import asyncio
from unittest import TestCase, mock

from wsvnc.pixel_format import PixelFormat
from wsvnc.server_messages.framebuffer_update import FrameBufferUpdate
from wsvnc.utils.safe_transport import SafeTransport


class TestFrameBufferUpdateMessage(TestCase):
    def setUp(self):
        self.transport_mock = mock.Mock(spec=SafeTransport)
        self.pf = PixelFormat()
        self.pf.bpp=32
        self.pf.big_endian=1
        self.pf.true_color=1
        self.pf.red_shift=0
        self.pf.red_max=256
        self.pf.green_shift=8
        self.pf.green_max=256
        self.pf.blue_shift=16
        self.pf.blue_max=256


    async def async_test_message_no_transport(self):
        """Test fbu server message with no waiting extra data from connection."""
        fbu = FrameBufferUpdate(self.pf)
        # message here is padding=[0] num_rects=[1:3]=1
        # rect=[3:15]=(0,0,1,1,0) pixel=[15:19]
        msg = b'\x00\x00\x01'
        rect = b'\x00\x00\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00'
        pixel=b'\x00\x01\x00\x02'
        self.transport_mock.recvd = mock.AsyncMock(side_effect=[rect+pixel, pixel])
        await fbu.read(self.transport_mock, msg+rect+pixel)
        
        assert len(fbu.rectangles) == 1
        assert fbu.rectangles[0].enc.img.getpixel((0, 0)) == (0,255,0,255)
        assert fbu.rectangles[0].height == fbu.rectangles[0].width == 1
        
    async def async_test_message_need_transport(self):
        """Test fbu server message but must wait for extra data from connection."""
        fbu = FrameBufferUpdate(self.pf)
        # message here is padding=[0] num_rects=[1:3]=1
        # rect=[3:15]=(0,0,1,1,0) pixel=[15:19]
        msg = b'\x00\x00\x01'
        rect = b'\x00\x00\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00'
        #pixel=b'\x00\x01\x00\x02'
        # this will cuase the fbu to wait for the transport to return pixel data.
        self.transport_mock.recvd = mock.AsyncMock(side_effect=[rect, b'\x00\x01\x00\x02'])
        await fbu.read(self.transport_mock, msg+rect)
        
        assert len(fbu.rectangles) == 1
        assert fbu.rectangles[0].enc.img.getpixel((0, 0)) == (0,255,0,255)
        assert fbu.rectangles[0].height == fbu.rectangles[0].width == 1
    
    def test_type(self):
        """Verify type."""
        fbu = FrameBufferUpdate(self.pf)
        assert fbu.type() == 0
        
    def test(self):
        asyncio.run(self.async_test_message_no_transport())
        asyncio.run(self.async_test_message_need_transport())
