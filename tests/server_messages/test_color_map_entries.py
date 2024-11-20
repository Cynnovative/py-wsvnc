"""Unit tests for ColorMapMessage class."""

import asyncio
from unittest import TestCase, mock

from wsvnc.color import Color
from wsvnc.server_messages.color_map_entries import ColorMapEntriesMessage
from wsvnc.utils.safe_transport import SafeTransport


class TestColorMapMessage(TestCase):
    def setUp(self):
        self.transport_mock = mock.Mock(spec=SafeTransport)
        self.test_color = Color(r=1,g=2,b=3)


    async def async_test_message_no_transport(self):
        """Test color map server message with no waiting extra data from connection."""
        cmem = ColorMapEntriesMessage()
        # message here is padding=[0] fist_color=[1:3]=0, num_colors=[3:5]=1, color=RGB=1,2,3
        msg = b'\x00\x00\x00\x00\x01\x00\x01\x00\x02\x00\x03'
        self.transport_mock.recvd = mock.AsyncMock(return_value=msg[5:])
        await cmem.read(self.transport_mock, msg)
        
        self.assertEqual(cmem.color_map[0].r, self.test_color.r)
        self.assertEqual(cmem.color_map[0].g, self.test_color.g)
        self.assertEqual(cmem.color_map[0].b, self.test_color.b)
    
    async def async_test_message_need_transport(self):
        """Test color map server message but wait for extra data from connection."""
        cmem = ColorMapEntriesMessage()
        # message here is padding=[0] fist_color=[1:3]=0, num_colors=[3:5]=1, color=RGB=1,2,3
        msg = b'\x00\x00\x00\x00\x01\x00\x01\x00\x02'
        self.transport_mock.recvd = mock.AsyncMock(return_value=msg[5:] + b'\x00\x03')
        await cmem.read(self.transport_mock, msg)
        
        
        self.assertEqual(cmem.color_map[0].r, self.test_color.r)
        self.assertEqual(cmem.color_map[0].g, self.test_color.g)
        self.assertEqual(cmem.color_map[0].b, self.test_color.b)
    
    def test_type(self):
        """Verify type."""
        cmem=ColorMapEntriesMessage()
        assert cmem.type() == 1
        
    def test(self):
        asyncio.run(self.async_test_message_no_transport())
        asyncio.run(self.async_test_message_need_transport())
