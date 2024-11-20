"""Unit tests for VNCSecurity test."""

import asyncio
from os import urandom
from unittest import TestCase, mock

from Cryptodome.Cipher import DES

from wsvnc.security.vnc_security import VNCSecurity
from wsvnc.utils.safe_transport import SafeTransport


class TestHandshake(TestCase):
    def setUp(self):
        self.transport_mock = mock.Mock(spec=SafeTransport)
        self.challenge=urandom(16)
        self.password=urandom(8)
        self.transport_mock.recv = mock.AsyncMock(return_value=self.challenge)
        self.transport_mock.send = mock.AsyncMock()
        
        # determine what the encrypted response should be
        key = bytes(sum((128 >> i) if (k & (1 << i)) else 0 for i in range(8)) for k in self.password)
        des = DES.new(key=key, mode=DES.MODE_ECB)
        self.resp = des.encrypt(self.challenge)


    async def async_test_handshake(self):
        """Verify that handshake returns correct encrypted (via password) challenge."""
        vncs = VNCSecurity(self.password)
        await vncs.handshake(self.transport_mock)
        
        self.transport_mock.recv.assert_awaited_once()
        
        self.transport_mock.send.assert_awaited_once()
        sent_args = self.transport_mock.send.call_args[0]
        assert sent_args[0] == self.resp
        
    def test_type(self):
        vncs = VNCSecurity(self.password)
        assert vncs.type() == 2
    
    def test(self):
        asyncio.run(self.async_test_handshake())
