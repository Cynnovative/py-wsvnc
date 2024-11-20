"""Server framebuffer update message."""

from struct import unpack
from typing import List, Optional, Type

from wsvnc.encodings.encoding_interface import EncodingInterface
from wsvnc.encodings.raw_encoding import RawEncoding
from wsvnc.exceptions.encoding_exception import PixelEncodingError
from wsvnc.pixel_format import PixelFormat
from wsvnc.rectangle import Rectangle
from wsvnc.server_messages.server_message_interface import ServerMessage
from wsvnc.utils.logger import get_logger
from wsvnc.utils.safe_transport import SafeTransport

logger = get_logger(__name__)


class FrameBufferUpdate(ServerMessage):
    rectangles: List[Rectangle]
    encs: List[Type[EncodingInterface]]

    def __init__(
        self, pf: PixelFormat, encs: Optional[List[Type[EncodingInterface]]] = None
    ) -> None:
        self.pf = pf
        self.rectangles = []
        if encs:
            self.encs = encs
        else:
            self.encs = [RawEncoding]

    def type(self) -> int:
        return 0

    async def read(self, transport: SafeTransport, msg: bytes) -> None:
        """Handle a frame buffer update server message.

        Go through each rectangle and save the pixel data into an encoding object that
        will be later drawn on a PIL.Image object.
        Specified in RFC 6143 7.6.1

        Raise:
            PixelEncodingError: Couldn't decode rectangle.
        """
        # read off padding
        msg = msg[1:]

        # number of rectangles
        rect_num = unpack(">H", msg[0:2])[0]

        # read every rectangle
        msg = msg[2:]  # read off the rect number
        logger.debug(f"Num rectangles: {rect_num}")
        for _ in range(rect_num):
            rect = Rectangle()

            # wait for rectangle header if message is incomplete.
            msg = await transport.recvd(msg, 12)

            (rect.x, rect.y, rect.width, rect.height, enc_type) = unpack(
                "!HHHHi", msg[:12]
            )
            logger.debug(f"rectangle: {(rect.x, rect.y, rect.width, rect.height)}")
            msg = msg[12:]  # drop the rectangles header

            # here we read off the pixel data into the encodings colors field.
            success = False
            for enc in self.encs:
                encoding = enc()
                # use the first encoding that matches the enc_type 4 byte integer
                if encoding.type() == enc_type:
                    # update the msg first if necessary
                    msg = await encoding.fetch_additional_data(
                        rect.width, rect.height, transport, msg, self.pf
                    )
                    # remember to increase offset by data read
                    chg = encoding.read(rect.width, rect.height, msg, self.pf)
                    msg = msg[chg:]
                    rect.enc = encoding
                    success = True
            if not success:
                logger.error(
                    f"Rect: {rect.x, rect.y, rect.width, rect.height}, Encoding Type: {enc_type}"
                )
                raise PixelEncodingError(
                    "Server encoding does not match acceptable client encodings."
                )

            # next rectangle
            self.rectangles.append(rect)
