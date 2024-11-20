"""Interface class for encodings."""

from abc import ABC, abstractmethod

from PIL.Image import Image

from wsvnc.pixel_format import PixelFormat
from wsvnc.utils.safe_transport import SafeTransport


class EncodingInterface(ABC):
    img: Image

    @abstractmethod
    def type(self) -> int:
        """Return the id of the encoding type.

        Returns
        -------
            int
        """
        pass

    @abstractmethod
    async def fetch_additional_data(
        self,
        width: int,
        height: int,
        transport: SafeTransport,
        msg: bytes,
        pf: PixelFormat,
    ) -> bytes:
        """Update rectangle data if necessary.

        Args:
            width (int): width of the rectangle
            height (int): height of the rectangle
            transport (SafeTransport): the socket
            msg (bytes): the data
            pf (PixelFormat): pixel format

        Returns
        -------
            bytes: The updated rectangle data.
        """
        pass

    @abstractmethod
    def read(self, width: int, height: int, msg: bytes, pf: PixelFormat) -> int:
        """Read the encoded pixels.

        Reads the pixels into self.img: Image, which is later assembled into
        the screen in the RFBClient.

        Args:
            width (int): width of the rectangle
            height (int): height of the rectangle
            msg (bytes): the encoded pixels in bytes
            pf (PixelFormat): the pre-set pixel format

        Returns
        -------
            int: number of encoded pixel bytes read
        """
        pass
