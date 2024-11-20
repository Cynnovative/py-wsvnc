"""Unit tests for RFBClient class."""

import asyncio
from unittest import TestCase, mock

import pytest
from PIL import Image
from websockets import WebSocketClientProtocol

from wsvnc.encodings.raw_encoding import RawEncoding
from wsvnc.pixel_format import PixelFormat
from wsvnc.rectangle import Rectangle
from wsvnc.rfb.rfb_client import RFBClient
from wsvnc.security.no_security import NoSecurity
from wsvnc.server_messages import framebuffer_update
from wsvnc.utils.safe_transport import SafeTransport


class TestRFBClient(TestCase):
    def setUp(self):
        self.conn_mock = mock.AsyncMock(spec=WebSocketClientProtocol)
        self.transport_mock = mock.AsyncMock(spec=SafeTransport)
        self.security_type = NoSecurity()
        self.pf = PixelFormat()
        self.pf.bpp=32
        self.pf.depth = 32
        self.pf.big_endian=1
        self.pf.true_color=1
        self.pf.red_shift=0
        self.pf.red_max=256
        self.pf.green_shift=8
        self.pf.green_max=256
        self.pf.blue_shift=16
        self.pf.blue_max=256
    
    async def async_test_handshake(self):
        """Test RFB handshake works as expected."""
        rfb = RFBClient(self.conn_mock, self.security_type)
        rfb.transport = self.transport_mock
        rfb._security_handshake = mock.AsyncMock()
        self.transport_mock.send = mock.AsyncMock()
        side_effect = [bytes for _ in range(4)]
        side_effect[0] = b'RFB 003.008\n'
        side_effect[1] = b'\x00\x00'
        side_effect[2] = b'\x00\x00\x00\x00'
        side_effect[3] = b'\x00\x01\x00\x01' + self.pf.write_pixel_format() + b'\x00\x00\x00\x03' + b'abc'
        
        self.transport_mock.recv.side_effect = side_effect
        
        await rfb.handshake()
        assert rfb.width == 1
        assert rfb.height == 1
        
    async def async_test_handshake_fail(self):
        rfb = RFBClient(self.conn_mock, self.security_type)
        rfb.transport = self.transport_mock
        side_effect = [bytes for _ in range(1)]
        side_effect[0] = b'RFB 003.008'
    
        self.transport_mock.recv.side_effect = side_effect
        
        with pytest.raises(ValueError):
            await rfb.handshake()
        
    
    async def async_test_listen(self):
        rfb = RFBClient(self.conn_mock, self.security_type)
        rfb.transport = self.transport_mock
        rfb.transport.conn = self.conn_mock
        rfb._handle_bell = mock.AsyncMock()
        rfb._handle_color_map = mock.AsyncMock()
        rfb._handle_framebuffer_update = mock.AsyncMock()
        rfb._handle_server_cut_text = mock.AsyncMock()
        messages = [
            b'\x00' + b'\x00'*15,  # FBU
            b'\x01' + b'\x00'*5,   # ColorMap
            b'\x02',               # Bell
            b'\x03' + b'\x00'*7    # Cut text
        ]
        
        self.transport_mock.recvd = mock.AsyncMock(side_effect=messages)
        
        # sets the asynchronous iter for: 
        # async for message in self.transport.conn:
        self.conn_mock.__aiter__.return_value = messages
        
        await rfb.listen()
        
        rfb._handle_bell.assert_awaited()
        rfb._handle_color_map.assert_awaited()
        rfb._handle_framebuffer_update.assert_awaited()
        rfb._handle_server_cut_text.assert_awaited()
        
    @mock.patch('wsvnc.rfb.rfb_client.FrameBufferUpdate', new_callable=mock.MagicMock, spec=framebuffer_update.FrameBufferUpdate)
    @mock.patch('PIL.Image.new')
    async def async_test_fbu(self, mock_image_new, mock_fbu_new):
        rfb = RFBClient(self.conn_mock, self.security_type)
        rfb.transport = self.transport_mock
        rfb.width = 800
        rfb.height = 600
        rfb.pixel_format = self.pf
        
        rect = Rectangle() # test rectangle
        rect.enc = RawEncoding()
        rect.enc.img = Image.new('RGBA', (1, 1), (1, 2, 3, 2555))
        rect.height, rect.width, rect.x, rect.y = (1, 1, 1, 1)
        
        # setup mocked variables (mocks the FBU object)
        mock_fbu = mock.AsyncMock(mock=framebuffer_update.FrameBufferUpdate)
        mock_fbu.rectangles = [rect]
        mock_fbu.read = mock.AsyncMock()
        mock_fbu_new.return_value = mock_fbu
        mock_image = mock.MagicMock() # mocks the Image.new() call
        mock_image_new.return_value = mock_image
        
        await rfb._handle_framebuffer_update(b'')
        
        # Check if an image was created when none was set
        assert rfb.img.getpixel((0, 0)) is not None
        mock_image_new.assert_called()
        mock_fbu_new.assert_called_once()
        mock_fbu.read.assert_awaited_once()
    
    @mock.patch('wsvnc.server_messages.color_map_entries.ColorMapEntriesMessage.read')
    async def async_test_color_map(self, cme_read):
        rfb = RFBClient(self.conn_mock, self.security_type)
        rfb.transport = self.transport_mock
        rfb.pixel_format = self.pf
        
        await rfb._handle_color_map(b'')
        
        cme_read.assert_awaited()
        
    @mock.patch('wsvnc.server_messages.cut_text.CutTextMessage.read')
    async def async_test_cut_text(self, cut_text_read):
        rfb = RFBClient(self.conn_mock, self.security_type)
        rfb.transport = self.transport_mock
        
        await rfb._handle_server_cut_text(b'\x00\x00\x00')
        
        cut_text_read.assert_awaited()
        
        
    def test_handshake(self):
        asyncio.run(self.async_test_handshake())
    def test_bad_handshake(self):
        asyncio.run(self.async_test_handshake_fail())
    def test_listen(self):
        asyncio.run(self.async_test_listen())
    def test_fbu(self):
        asyncio.run(self.async_test_fbu())
    def test_color_map(self):
        asyncio.run(self.async_test_color_map())
    def test_cut_text(self):
        asyncio.run(self.async_test_cut_text())