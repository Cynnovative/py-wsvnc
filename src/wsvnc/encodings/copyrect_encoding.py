"""CopyRect encoding."""

from struct import unpack

from PIL import Image

from wsvnc.encodings.encoding_interface import EncodingInterface
from wsvnc.pixel_format import PixelFormat
from wsvnc.utils.safe_transport import SafeTransport


class CopyRectEncoding(EncodingInterface):
    img: Image.Image

    async def fetch_additional_data(
        self,
        width: int,
        height: int,
        transport: SafeTransport,
        msg: bytes,
        pf: PixelFormat,
    ) -> bytes:
        # CopyRect only contains 4 bytes (2 for src-x, and 2 for src-y)
        return await transport.recvd(msg, 4)

    def type(self) -> int:
        return 1

    def read(self, width: int, height: int, msg: bytes, pf: PixelFormat) -> int:
        """Determine the x & y of the original screen to copy.

        CopyRect is different than most encodings in that it requires the existing image
        to construct the new one. We can't do this at this function so here we just save
        the src-x & src-y value of the rectangle we're going to copy. In RFBClient
        _handleFBU() you'll see that the img value is assigned to a cropped section of
        the existing image based on these values.
        """
        (self.srcx, self.srcy) = unpack("!HH", msg[:4])
        return 4
