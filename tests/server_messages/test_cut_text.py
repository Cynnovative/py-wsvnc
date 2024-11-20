"""Unit tests for CutTextMessage class."""

import asyncio
from unittest import TestCase, mock

from wsvnc.server_messages.cut_text import CutTextMessage
from wsvnc.utils.safe_transport import SafeTransport


class TestCutTextMessage(TestCase):
    def setUp(self):
        self.transport_mock = mock.Mock(spec=SafeTransport)


    async def async_test_message_no_transport(self):
        """Test cut text server message with no waiting extra data from connection."""
        ctm = CutTextMessage()
        # message here is padding=[0:3] text_len=[3:7]=3 text='abc'
        msg = b'\x00\x00\x00\x00\x00\x00\x03abc'
        self.transport_mock.recvd = mock.AsyncMock(return_value=b'abc')
        await ctm.read(self.transport_mock, msg)
        
        assert ctm.cut_text == b'abc'
        
    async def async_test_message_need_transport(self):
        """Test cut text server message but wait for extra data from connection."""
        ctm = CutTextMessage()
        # message here is padding=[0:3] text_len=[3:7]=3 text='abc'
        msg = b'\x00\x00\x00\x00\x00\x00\x03'
        self.transport_mock.recvd = mock.AsyncMock(return_value=b'abc')
        await ctm.read(self.transport_mock, msg)
        
        assert ctm.cut_text == b'abc'
    
    def test_type(self):
        """Verify type."""
        ctm = CutTextMessage()
        assert ctm.type() == 3
        
    def test(self):
        asyncio.run(self.async_test_message_no_transport())
        asyncio.run(self.async_test_message_need_transport())
