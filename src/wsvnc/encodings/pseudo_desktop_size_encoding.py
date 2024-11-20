"""Header encoding to enable CopyRect on ESXi, and to redefine our screen size."""

from PIL import Image

from wsvnc.encodings.encoding_interface import EncodingInterface
from wsvnc.pixel_format import PixelFormat
from wsvnc.utils.safe_transport import SafeTransport


class PseudoDesktopSizeEncoding(EncodingInterface):
    img: Image.Image

    async def fetch_additional_data(
        self,
        width: int,
        height: int,
        transport: SafeTransport,
        msg: bytes,
        pf: PixelFormat,
    ) -> bytes:
        return msg

    def type(self) -> int:
        return -223

    def read(self, width: int, height: int, msg: bytes, pf: PixelFormat) -> int:
        """Header encoding."""
        return 0
