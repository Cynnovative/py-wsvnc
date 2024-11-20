"""Class to represent framebuffer update rectangles sent back by VNC server."""

from wsvnc.encodings.encoding_interface import EncodingInterface


class Rectangle(object):
    x: int  # 2 bytes
    y: int
    width: int
    height: int
    enc: EncodingInterface
