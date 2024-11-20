"""Server Bell message handler."""

from wsvnc.server_messages.server_message_interface import ServerMessage
from wsvnc.utils.safe_transport import SafeTransport


class BellMessage(ServerMessage):
    sig: int

    def type(self) -> int:
        return 2

    async def read(self, transport: SafeTransport, msg: bytes) -> None:
        self.sig = 0
