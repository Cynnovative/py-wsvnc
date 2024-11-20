"""TightPNG encoding standard."""

from io import BytesIO

from PIL import Image

from wsvnc.encodings.encoding_interface import EncodingInterface
from wsvnc.pixel_format import PixelFormat
from wsvnc.utils.logger import get_logger
from wsvnc.utils.safe_transport import SafeTransport

logger = get_logger(__name__)


class TightPNGEncoding(EncodingInterface):
    img: Image.Image

    def __init__(self) -> None:
        self.sub_enc_jpeg = 144
        self.sub_enc_fill = 128
        self.sub_enc_png = 160
        self.sub_enc_diff_jpeg = 176
        self.sub_enc_mask = 240

    def type(self) -> int:
        return -260

    async def fetch_additional_data(
        self,
        width: int,
        height: int,
        transport: SafeTransport,
        msg: bytes,
        pf: PixelFormat,
    ) -> bytes:
        """Fetch more pixel data if we don't have enough yet.

            This design is specific to TightVNC Encoding.
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
        # if necessary wait for the TightPNG header (subencoding + length)
        pixel_data = await transport.recvd(msg, 4)

        # the subencoding is the first byte
        self.sub_encoding = pixel_data[0]
        logger.debug(f"Subencoding: {self.sub_encoding}")

        # unmask subencoding
        self.sub_encoding &= self.sub_enc_mask
        logger.debug(f"Subencoding Unmasked: {self.sub_encoding}")

        # if the sub_encoding is the color map we don't want to read off
        # any data aside from the subencoding
        if self.sub_encoding == self.sub_enc_fill:
            return pixel_data[1:]

        # get the length of the data encoded (lots of shifting here)
        # but this is correct (exact same logic in wmks.js from VMWare)
        data_length = pixel_data[1]
        data_length &= -129
        data_length += pixel_data[2] << 7
        data_length &= -16385
        data_length += pixel_data[3] << 14
        logger.debug(f"Tight Encoding length: {data_length}")

        self.data_length = data_length

        # chop off the header with subencoding & length
        pixel_data = pixel_data[4:]

        # now we know how many bytes we expect to receive, and so if we don't have them
        # we must wait
        pixel_data = await transport.recvd(pixel_data, data_length)

        return pixel_data

    def read(self, width: int, height: int, msg: bytes, pf: PixelFormat) -> int:
        # if sub_encoding is fill then our img is just a pixel
        # from three bytes in the buffer
        if self.sub_encoding == self.sub_enc_fill:
            self.img = Image.new("RGBA", (width, height), (msg[0], msg[1], msg[2], 255))
            return 3

        data = msg[: self.data_length]

        if (
            self.sub_encoding == self.sub_enc_jpeg
            or self.sub_encoding == self.sub_enc_png
        ):
            """Implements JPEG & PNG logic."""
            self.img = Image.open(BytesIO(data))

            if self.img.mode != "RGBA":
                self.img = self.img.convert("RGBA")

        if self.sub_encoding == self.sub_enc_diff_jpeg:
            """Implements JPEGDiff logic."""
            raise NotImplementedError

        return self.data_length
