"""Handle color map entries message."""

from struct import unpack

from wsvnc.color import Color
from wsvnc.server_messages.server_message_interface import ServerMessage
from wsvnc.utils.safe_transport import SafeTransport


class ColorMapEntriesMessage(ServerMessage):
    _first_color: int
    _number_of_colors: int
    color_map: dict[int, Color]

    def __init__(self) -> None:
        self._first_color = 0
        self._number_of_colors = 0
        self.color_map = {}

    def type(self) -> int:
        return 1

    async def read(self, transport: SafeTransport, msg: bytes) -> None:
        """Handle Color Map Entries server message.

        Specified in RFC 6143 7.6.2
        """
        # read off passing.
        msg = msg[1:]

        # read off first color & num colors
        self._first_color = unpack(">H", msg[0:2])[0]
        self._number_of_colors = unpack(">H", msg[2:4])[0]

        # wait for the color map if message is incomplete.
        colors = msg[4:]
        expected_bytes = self._number_of_colors * 6
        colors = await transport.recvd(colors, expected_bytes)

        # read off each RGB color pixel value
        for i in range(self._number_of_colors):
            r, g, b = unpack(">HHH", colors[0:6])
            c = Color(r=r, g=g, b=b)
            self.color_map[i + self._first_color] = c
            colors = colors[6:]
