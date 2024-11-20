"""Pixel format class representation."""

from struct import pack, unpack
from typing import Optional

from wsvnc.color import Color


class PixelFormat(object):
    bpp: int
    depth: int
    big_endian: int
    true_color: int
    red_max: int
    green_max: int
    blue_max: int
    red_shift: int
    green_shift: int
    blue_shift: int
    color_map: Optional[dict[int, Color]]

    def write_pixel_format(self) -> bytes:
        """Encode pixel format into bytes.

        Returns
        -------
            bytes: pixel format encoded into bytes
        """
        return pack(
            "!BBBBHHHBBBxxx",
            self.bpp,
            self.depth,
            self.big_endian,
            self.true_color,
            self.red_max,
            self.green_max,
            self.blue_max,
            self.red_shift,
            self.green_shift,
            self.blue_shift,
        )


def read_format(b: bytes) -> PixelFormat:
    """Read the pixel format.

    Args:
        b (bytes): 16 bytes that include the pixel format

    Returns
    -------
        PixelFormat: PixelFormat object
    """
    pf = PixelFormat()
    pf.bpp = b[0]
    pf.depth = b[1]
    pf.big_endian = b[2]
    pf.true_color = b[3]
    pf.red_max = unpack(">H", b[4:6])[0]
    pf.green_max = unpack(">H", b[6:8])[0]
    pf.blue_max = unpack(">H", b[8:10])[0]
    pf.red_shift = b[10]
    pf.green_shift = b[11]
    pf.blue_shift = b[12]
    return pf
