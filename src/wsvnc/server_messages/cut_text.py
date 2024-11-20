"""Server cut text message."""

from struct import unpack

from wsvnc.server_messages.server_message_interface import ServerMessage
from wsvnc.utils.safe_transport import SafeTransport


class CutTextMessage(ServerMessage):
    cut_text: str

    def __init__(self) -> None:
        self.cut_text = ""

    def type(self) -> int:
        return 3

    async def read(self, transport: SafeTransport, msg: bytes) -> None:
        """Handle cut text server message.

        Specified in RFC 6143 7.6.4
        """
        # read off padding
        msg = msg[3:]

        # read text length
        text_len = unpack(">I", msg[0:4])[0]
        text = msg[4:]

        # wait for more text if message is incomplete.
        text = await transport.recvd(text, text_len)

        # read text
        self.cut_text = unpack("{l}s".format(l=text_len), text)[0]
