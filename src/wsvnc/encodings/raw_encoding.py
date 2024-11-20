"""Basic raw pixel encoding class supported by ESXi."""

from struct import unpack

from PIL import Image

from wsvnc.encodings.encoding_interface import EncodingInterface
from wsvnc.pixel_format import PixelFormat
from wsvnc.utils.logger import get_logger
from wsvnc.utils.safe_transport import SafeTransport

logger = get_logger(__name__)


class RawEncoding(EncodingInterface):
    img: Image.Image

    def type(self) -> int:
        return 0

    async def fetch_additional_data(
        self,
        width: int,
        height: int,
        transport: SafeTransport,
        msg: bytes,
        pf: PixelFormat,
    ) -> bytes:
        """Fetch more pixel data if we don't have enough yet.

            This design is specific to raw encoding.
        Args:
            width: width of the rectangle
            height: height of the rectangle
            transport (SafeTransport): the socket
            msg (bytes): the existing (possibly incomplete) message.
            pf (PixelFormat): The pixel format

        Returns
        -------
            bytes: the updated message
        """
        return await transport.recvd(msg, (width * height * pf.bpp // 8))

    def read(self, width: int, height: int, msg: bytes, pf: PixelFormat) -> int:
        self.img = Image.new("RGBA", (width, height), (0, 0, 0, 0))

        bytes_per_pixel = pf.bpp // 8
        if pf.big_endian:
            byteorder = ">"
        else:
            byteorder = "<"

        offs = 0
        for i in range(height * width):
            x = i % width
            y = i // width

            pixel_bytes = msg[offs : offs + bytes_per_pixel]
            offs += bytes_per_pixel

            if len(pixel_bytes) < bytes_per_pixel:
                raise ValueError("Failed to read enough pixel bytes")

            if pf.bpp == 8:
                raw_pixel = pixel_bytes[0]
            elif pf.bpp == 16:
                raw_pixel = unpack(byteorder + "H", pixel_bytes)[0]
            elif pf.bpp == 32:
                raw_pixel = unpack(byteorder + "I", pixel_bytes)[0]

            # determines the color of this pixel
            # the final "&0xffff" ensures its a uint16 type
            if pf.true_color:
                r = (raw_pixel >> pf.red_shift & pf.red_max) & 0xFFFF
                g = (raw_pixel >> pf.green_shift & pf.green_max) & 0xFFFF
                b = (raw_pixel >> pf.blue_shift & pf.blue_max) & 0xFFFF
                self.img.putpixel((x, y), (r, g, b, 255))
            else:
                if pf.color_map is None:
                    logger.error("Color map is not ready. Cannot parse encoding.")
                    return offs
                color = pf.color_map[raw_pixel]
                self.img.putpixel((x, y), (color.r, color.g, color.b, 255))

        return offs
