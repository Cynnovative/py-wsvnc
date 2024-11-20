"""Header encoding to enable JpegDiff Composition subencodings for TightPNG."""

from PIL import Image

from wsvnc.encodings.encoding_interface import EncodingInterface
from wsvnc.pixel_format import PixelFormat
from wsvnc.utils.safe_transport import SafeTransport


class TightPNGDiffCompEncoding(EncodingInterface):
    img: Image.Image

    async def fetch_additional_data(
        self,
        width: int,
        height: int,
        transport: SafeTransport,
        msg: bytes,
        pf: PixelFormat,
    ) -> bytes:
        return b""

    def type(self) -> int:
        return 1464686102

    def read(self, width: int, height: int, msg: bytes, pf: PixelFormat) -> int:
        """Header encoding."""
        return 0
