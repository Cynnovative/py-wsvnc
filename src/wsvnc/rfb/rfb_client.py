"""Client that implements RFB Protocol according to RFC 6143."""

import re
import traceback
from struct import pack, unpack
from typing import List, Optional, Type

from PIL import Image
from websockets import WebSocketClientProtocol

from wsvnc.constants import supported_versions
from wsvnc.encodings.copyrect_encoding import CopyRectEncoding
from wsvnc.encodings.encoding_interface import EncodingInterface
from wsvnc.encodings.pseudo_desktop_size_encoding import PseudoDesktopSizeEncoding
from wsvnc.encodings.raw_encoding import RawEncoding
from wsvnc.encodings.vmware_define_cursor_encoding import VMWDefineCursorEncoding
from wsvnc.pixel_format import PixelFormat, read_format
from wsvnc.security.no_security import NoSecurity
from wsvnc.security.security_type_interface import SecurityTypeInterface
from wsvnc.server_messages.bell import BellMessage
from wsvnc.server_messages.color_map_entries import ColorMapEntriesMessage
from wsvnc.server_messages.cut_text import CutTextMessage
from wsvnc.server_messages.framebuffer_update import FrameBufferUpdate
from wsvnc.utils.logger import get_logger
from wsvnc.utils.safe_transport import SafeTransport

logger = get_logger(__name__)


class RFBClient:
    encs: List[Type[EncodingInterface]]
    width: int
    height: int
    pixel_format: PixelFormat
    _server_name_length: int
    server_name: str
    img: Optional[Image.Image] = None
    resend_flag: bool = False
    bell: Optional[BellMessage] = None

    def __init__(
        self,
        conn: WebSocketClientProtocol,
        security_type: SecurityTypeInterface = NoSecurity(),
        shared_flag: int = 1,
    ) -> None:
        self.transport = SafeTransport(conn)
        self.security_type = security_type
        self.encs = [RawEncoding]
        self.clipboard = ""
        self.shared_flag = shared_flag

    """ Functions that are sent by the VNC Client -> ESXi """

    async def cut_text(self, text: str) -> None:
        """Tell the server that the client has new text in its cut buffer.

        RFC 6143 Section 7.5.6.

        Args:
            text (str): string to copy
        """
        self.clipboard = text
        await self.transport.send(pack("!BxxxI", 6, len(text)) + text.encode("utf-8"))

    async def framebuffer_update_request(
        self, x: int, y: int, width: int, height: int, incremental: bool = False
    ) -> None:
        """Request a framebuffer update from the server.

        There may be an indefinite time
        between the request and the actual framebuffer update being received.
        RFC 6143 Section 7.5.3.

        Args:
            x (int): x-pos start of frame
            y (int): y-pos start of frame
            width (int): width of frame
            height (int): height of frame
            incremental (bool): true = incremental,
        """
        logger.debug("sent frame buffer update request.")
        await self.transport.send(pack("!BBHHHH", 3, incremental, x, y, width, height))

    async def key_event(self, key: int, down: bool) -> None:
        """Press or release key on server.

        Many keys are there ASCII equivalent, but some are unique and in constants.
        RFC 6143 Section 7.5.4.

        Args:
            key (int): keyId #
            down (bool): true=down, false=up.
        """
        if down:
            send_down = 1
        else:
            send_down = 0
        await self.transport.send(pack("!BBxxI", 4, send_down, key))

    async def pointer_event(self, x: int, y: int, mask: int) -> None:
        """Send pointer event to server.

        RFC 6143 Section 7.5.5.

        Args:
            x (int): x-cord on screen
            y (int): y-cord on screen
            mask (int): button to press (0 to unpress) (1=leftclick) (4=rightclick)
        """
        await self.transport.send(pack("!BBHH", 5, mask, x, y))

    async def set_encodings(self, encs: List[Type[EncodingInterface]]) -> None:
        """Set encoding types that can be sent from the server.

        Args:
            encs (List[EncodingInterface]): List of implemented encodings
        """
        msg = pack("!BxH", 2, len(encs))
        for enc in encs:
            encoding = enc()
            msg += pack(">i", encoding.type())
        await self.transport.send(msg)
        self.encs = encs + [RawEncoding]

    async def set_pixel_format(self, format: PixelFormat) -> None:
        """Set pixel format for FramebufferUpdate messages from the server.

        RFC 6143 Section 7.5.1.

        Args:
            format (PixelFormat): _description_
        """
        self.pixel_format = format
        logger.debug("Setting Pixel Format.")
        await self.transport.send(pack("!Bxxx", 0) + format.write_pixel_format()[1:])

    async def close(self) -> None:
        """Close the websocket connection."""
        await self.transport.conn.close()

    """ Functions that handle messages received by the Client, Server -> Client """

    async def listen(self) -> None:
        """Async function that listens and handles server messages."""
        try:
            async for message in self.transport.conn:
                if not isinstance(message, bytes):
                    raise TypeError("Client should receive bytes.")
                if len(message) == 0:
                    logger.error("Received a message from the server with no bytes.")
                else:
                    logger.debug(f"Received: {len(message)} bytes")
                    if (
                        message[0] == 0
                    ):  # if first byte is 0 we received a framebuffer_update
                        logger.debug("received framebuffer update.")
                        message = await self.transport.recvd(
                            message, 16
                        )  # read the rest of the FBU.
                        await self._handle_framebuffer_update(message)
                        logger.debug("updated screen!")
                        if self.resend_flag:
                            await self.framebuffer_update_request(
                                0, 0, self.width, self.height, True
                            )
                    elif message[0] == 1:
                        logger.debug("received colorMap message.")
                        message = await self.transport.recvd(
                            message, 6
                        )  # read the rest of the FBU. # read rest of color map
                        await self._handle_color_map(message)
                    elif message[0] == 2:
                        logger.debug("received bell message.")
                        await self._handle_bell()
                    elif message[0] == 3:
                        logger.debug("received server cut text message.")
                        message = await self.transport.recvd(
                            message, 8
                        )  # read the rest of the FBU. # read rest of cut text
                        await self._handle_server_cut_text(message)
        except Exception as e:
            logger.error("RFBClient Encountered An exception! {s}".format(s=e))
            logger.error(f"RFBClient Exception Traceback: {traceback.format_exc()}")
            await self.close()

    async def _handle_framebuffer_update(self, msg: bytes) -> None:
        """Async function helper to handle framebuffer update messages from server."""
        if self.img is None:  # set the image to the screen size and all black.
            self.img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))

        fbu = FrameBufferUpdate(self.pixel_format, self.encs)
        await fbu.read(self.transport, msg[1:])
        logger.debug("Updating image with pixels.")
        for rect in fbu.rectangles:
            enc = rect.enc
            logger.debug(f"Processing: {rect.width * rect.height}, pixels")

            # VMWare define unimplemented
            if isinstance(enc, VMWDefineCursorEncoding):
                continue

            # DesktopSize is special since it defines the screen size
            # If we get this encoding we should redefine the img to be blank
            # and to whatever size it now should be, and then send an FBUR for
            # the entire screen to get an update ASAP
            if isinstance(enc, PseudoDesktopSizeEncoding):
                logger.info(
                    f"Redefining Desktop Size to: width: {rect.width}, height: {rect.height}"
                )
                self.img = Image.new("RGBA", (rect.width, rect.height), (0, 0, 0, 0))
                self.width = rect.width
                self.height = rect.height
                await self.framebuffer_update_request(
                    0, 0, rect.width, rect.height, False
                )
                return

            # CopyRect is special since we need the existing image to crop from
            # to assemble the new one
            if isinstance(enc, CopyRectEncoding):
                enc.img = self.img.crop(
                    (enc.srcx, enc.srcy, enc.srcx + rect.width, enc.srcy + rect.height)
                )

            self.img.paste(enc.img, (rect.x, rect.y))

    async def _handle_server_cut_text(self, msg: bytes) -> None:
        """Handle server cut text messages.

        RFC 6143 section 7.6.4. Replaces the rfb_client.cut_text field.
        """
        sct = CutTextMessage()
        await sct.read(self.transport, msg[1:])
        logger.debug(f"Client has cut text in buffer: {sct.cut_text}")
        self.clipboard = sct.cut_text

    async def _handle_color_map(self, msg: bytes) -> None:
        """Handle color map entries server message.

        RFC 6143 section 7.6.2. Sets the pixel_format.color_map field that will be used
        when decoding pixels.
        """
        cme = ColorMapEntriesMessage()
        await cme.read(self.transport, msg[1:])
        self.pixel_format.color_map = cme.color_map

    async def _handle_bell(self) -> None:
        """Handle server bell message.

        If you want the bell to do something I recommend overriding the read() in
        BellMessage.
        """
        self.bell = BellMessage()
        await self.bell.read(self.transport, b"")

    """ Helpers to establish the VNC connection over websocket."""

    async def handshake(self) -> None:
        """Do initial handshake with VNC server."""
        msg = await self.transport.recv()
        if re.search(rb"RFB (\d+\.\d+)\n", msg):
            logger.debug(f"Received initial handshake message: {msg!r}")
        else:
            logger.error("Received bad handshake message!")
            raise (ValueError("VNC handshake start failed!"))

        if self._validate_security(msg):
            # we'll support 003.008 (the latest security)
            await self.transport.send(b"RFB 003.008\n")

            # now we read the servers security types
            # first byte is the length, the rest are the types supported
            # for ESXi, only None is supported (1).
            security_types_recv = await self.transport.recv()
            security_types = security_types_recv[1:]
            # now we do the security handshake
            await self._security_handshake(security_types)

            # security handshake result (4 bytes should be 0, else is error)
            security_result_recv = await self.transport.recv()
            security_result = unpack(">I", security_result_recv)[0]
            if security_result != 0:
                raise (ValueError("Security handshake failed!"))

            # send share flag
            await self.transport.send(pack("!B", self.shared_flag))

            # ServerInit
            server_init_recv = await self.transport.recv()
            # the first 4 bytes of the initialization are the width and height of the screen respectively
            self.width = unpack(">H", server_init_recv[0:2])[0]
            self.height = unpack(">H", server_init_recv[2:4])[0]
            # the next 16 bytes are the pixel format
            self.pixel_format = read_format(server_init_recv[4:20])
            # the next 4 bytes is the LENGTH of the NAME of the server
            self._server_name_length = unpack(">I", server_init_recv[20:24])[0]
            # finally read in the server name.
            self.server_name = str(
                unpack(
                    "{l}s".format(l=self._server_name_length),
                    server_init_recv[-self._server_name_length :],
                )[0]
            )

            logger.info("Handshake done!")
            logger.info("Client Ready!")
        else:
            logger.error("Received unsupported security version.")

    async def _security_handshake(self, sec_types: bytes) -> None:
        """Commence security handshake.

        First determines if the server handles the
        security type we want to use. Then, commences the security handshake.

        Args:
            sec_types (bytes): list of security types the server can handle (ESXi handles only 1 (noSecurity)).
        """
        for sec_type in sec_types:
            if self.security_type.type() == sec_type:
                await self.transport.send(pack("!B", sec_type))
                # print("sent security type.")
                await self.security_type.handshake(self.transport)
            else:
                raise (UserWarning("Server does not support desired security type!"))

    def _validate_security(self, text: bytes) -> bool:
        """Validate the server is using security we support.

        Args:
            text (bytes): initial server message

        Returns
        -------
            bool: true if we support, false if we don't (kills handshake)
        """
        if text in supported_versions:
            return True
        else:
            return False
