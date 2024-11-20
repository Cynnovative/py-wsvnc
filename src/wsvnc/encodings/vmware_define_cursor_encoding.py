"""Necessary to enable CopyRect encoding on ESXi."""

from PIL import Image

from wsvnc.encodings.encoding_interface import EncodingInterface
from wsvnc.pixel_format import PixelFormat
from wsvnc.utils.safe_transport import SafeTransport


class VMWDefineCursorEncoding(EncodingInterface):
    img: Image.Image

    async def fetch_additional_data(
        self,
        width: int,
        height: int,
        transport: SafeTransport,
        msg: bytes,
        pf: PixelFormat,
    ) -> bytes:
        # we need at least two bytes to determine the cursor type (second byte is garbage)
        cursor_header = await transport.recvd(msg, 2)

        # cursor type defined in the first byte
        self.cursor_type = cursor_header[0]

        # pixel length is fixed to the rectangle width * height * 4
        self.pixel_length = width * height * 4

        # mask length is either 0 or the pixel length
        if self.cursor_type == 0:
            self.mask_length = self.pixel_length
        else:
            self.mask_length = 0

        # now we must wait for pixel_length + mask_length bytes
        data = cursor_header[2:]
        data = await transport.recvd(data, self.pixel_length + self.mask_length)

        return data

    def type(self) -> int:
        return 1464686180

    def read(self, width: int, height: int, msg: bytes, pf: PixelFormat) -> int:
        """Not properly implemented.

        I believe this encoding gives you a base64 value from what I understand of the
        javascript in wmks, however this encoding is not actually used by the WebSDK.
        Instead, it just goes into the canvas style value and sets it to: `cursor:
        none`, to disable the canvas's cursor. I am going to leave this as unimplemented
        since it's not useful and only specific to ESXi, and I am only adding this
        encoding to enable CopyRect for ESXi.

        Also, apparently when this is received the FBU sends additional TightPNG
        rectangles with subencoding set to fill. I suppose that's meant to draw the
        cursor.
        """
        return self.pixel_length + self.mask_length
