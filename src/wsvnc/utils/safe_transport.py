"""Wrapper to ensure binary transmission."""

from websockets import WebSocketClientProtocol


class SafeTransport:
    def __init__(self, transport: WebSocketClientProtocol) -> None:
        self.conn = transport

    async def recv(self) -> bytes:
        """Guarantee we receive bytes from connection."""
        data = await self.conn.recv()
        if isinstance(data, bytes):
            return data
        raise ValueError("Received data is not bytes.")

    async def recvd(self, msg: bytes, length: int) -> bytes:
        """Wait for a specific number of bytes given an existing message."""
        data = bytearray(msg)
        while len(data) < length:
            data.extend(await self.recv())
        return data

    async def send(self, msg: bytes) -> None:
        """Guarantee we send bytes.

        Args:
            msg (bytes): msg to be sent.
        """
        await self.conn.send(msg)
