"""VNC Client class, the main entrypoint for agents."""

from __future__ import annotations

import asyncio
import threading
import time
from io import BytesIO
from ssl import SSLContext
from types import TracebackType
from typing import List, Optional, Type

import websockets
from PIL import Image

from wsvnc.encodings.encoding_interface import EncodingInterface
from wsvnc.pixel_format import PixelFormat
from wsvnc.rfb.rfb_client import RFBClient
from wsvnc.security import no_security, security_type_interface
from wsvnc.server_messages.bell import BellMessage
from wsvnc.utils.logger import get_logger

logger = get_logger(__name__)


class WSVNCClient:
    def __init__(
        self,
        ticket_url: str,
        ssl_context: Optional[SSLContext] = None,
        origin: str = "http://localhost",
        security_type: security_type_interface.SecurityTypeInterface = no_security.NoSecurity(),
        keep_screen_updated: bool = False,
        shared_flag: int = 1,
    ) -> None:
        self.ticket_url = ticket_url
        self.origin = origin
        self.security_type = security_type
        self.ssl_context = ssl_context
        self.shared_flag = shared_flag
        # event loop
        self._loop = asyncio.new_event_loop()
        # start the client
        self._handshake_done = threading.Event()
        self._caught_exception: Exception | None = None
        self._run()
        self._handshake_done.wait(30)

        # if we have an exception during initial
        # connection we will throw it here
        # this will notify the user and prevent them
        # from accidentally using the client when it never connected
        if self._caught_exception:
            raise self._caught_exception

        if keep_screen_updated:
            self.set_resend_flag()

    def set_resend_flag(self, on: bool = True) -> None:
        """Set FBUR resend flag.

        If this is set to True, the screen will continually update in the background.

        Args:
            on (bool): Resend flag value.
        """
        self._rfb_client.resend_flag = on
        if on:
            self.update_screen()

    def set_pixel_format(self, pf: PixelFormat) -> None:
        """Set the pixel formatting the server will use.

        Args:
            pf (PixelFormat): Pixel format object
        """
        asyncio.run_coroutine_threadsafe(
            self._rfb_client.set_pixel_format(pf), self._loop
        )

    def set_encodings(self, encs: List[Type[EncodingInterface]]) -> None:
        """Set the encodings the client will use.

        Args:
            encs (List[Type[EncodingInterface]]): encodings that implement the interface.
        """
        asyncio.run_coroutine_threadsafe(
            self._rfb_client.set_encodings(encs), self._loop
        )

    def send_key(self, key: int) -> None:
        """Press a key then release.

        Args:
            key (int): Key ID
        """
        self.key_event(key, True)
        time.sleep(0.1)
        self.key_event(key, False)

    def move(self, xpos: int, ypos: int) -> None:
        """Move mouse to position(xpos,ypos).

        Used before any other click action to ensure cursor is in the correct position.

        Args:
            xpos (int)
            ypos (int)
        """
        self.pointer_event(xpos, ypos, 0)

    def release(self, xpos: int, ypos: int) -> None:
        """Relase is the same as move().

        Args:
            xpos (int)
            ypos (int)
        """
        self.move(xpos, ypos)

    def left_click(self, xpos: int, ypos: int) -> None:
        """Left click at position(xpos, ypos).

        Args:
            xpos (int)
            ypos (int)
        """
        self.move(xpos, ypos)
        self.pointer_event(xpos, ypos, 1)
        self.pointer_event(xpos, ypos, 0)

    def double_left_click(self, xpos: int, ypos: int) -> None:
        """Double left click at position(xpos, ypos).

        Args:
            xpos (int)
            ypos (int)
        """
        self.move(xpos, ypos)
        self.left_click(xpos, ypos)
        time.sleep(0.05)
        self.left_click(xpos, ypos)

    def press(self, xpos: int, ypos: int) -> None:
        """Left-Press and then hold.

        Args:
            xpos (int)
            ypos (int)
        """
        self.move(xpos, ypos)
        self.pointer_event(xpos, ypos, 1)

    def right_click(self, xpos: int, ypos: int) -> None:
        """Right click at position(xpos, ypos).

        Args:
            xpos (int)
            ypos (int)
        """
        self.move(xpos, ypos)
        self.pointer_event(xpos, ypos, 4)
        self.pointer_event(xpos, ypos, 0)

    def wheel_up(self, xpos: int, ypos: int, delay_ms: int = 50) -> None:
        """Scrolls up at position(xpos, ypos) for duration delay_ms.

        Args:
            xpos (int)
            ypos (int)
            delay_ms (int, optional): time to scroll up. Defaults to 50.
        """
        self.pointer_event(xpos, ypos, 8)
        time.sleep(delay_ms * 0.001)
        self.pointer_event(xpos, ypos, 0)

    def wheel_down(self, xpos: int, ypos: int, delay_ms: int = 50) -> None:
        """Scrolls down at position(xpos, ypos) for duration delay_ms.

        Args:
            xpos (int)
            ypos (int)
            delay_ms (int, optional): time to scroll down. Defaults to 50.
        """
        self.pointer_event(xpos, ypos, 16)
        time.sleep(delay_ms * 0.001)
        self.pointer_event(xpos, ypos, 0)

    def wheel(self, xpos: int, ypos: int, delay_ms: int, down: bool = False) -> None:
        """Use mouse wheel.

        If down is set to true the mouse wheel will scroll down, if not it will scroll up.

        Args:
            xpos (int)
            ypos (int)
            delay_ms (int): time mouse wheel will scroll in milliseconds
            down (bool): true=wheel down, false=wheel up
        """
        if down:
            self.wheel_down(xpos, ypos, delay_ms)
        else:
            self.wheel_up(xpos, ypos, delay_ms)

    def click_and_drag(self, xpos: int, ypos: int, newx: int, newy: int) -> None:
        """Clicks at position(xpos, ypos) and hold to position(newx, newy).

        Args:
            xpos (int): starting x coord.
            ypos (int): starting y coord.
            newx (int): end x coord.
            newy (int): end y coord.
        """
        self.move(xpos, ypos)
        self.pointer_event(xpos, ypos, 1)
        self.pointer_event(newx, newy, 1)

    def emit_text(self, text: str) -> None:
        """Type text on the server. These should be strictly [a-Z0-9].

        Args:
            text (str): text to be emitted.
        """
        for chr in text:
            if self._is_shift_required(chr):
                self.key_event(65505, True)  # press shift
                time.sleep(0.1)
                self.send_key(ord(chr))
                self.key_event(65505, False)  # release shift
            else:
                self.send_key(ord(chr))

    def cut_text(self, text: str) -> None:
        """Client tells the server it has text in its clipboard.

        Args:
            text (str): _description_
        """
        asyncio.run_coroutine_threadsafe(self._rfb_client.cut_text(text), self._loop)

    def _is_shift_required(self, c: str) -> bool:
        """Determine if we should press shift when typing this letter.

        Does not check for caps lock, so don't set caps lock.

        Args:
            c (str): a character

        Returns
        -------
            bool: true if it shift is needed on the keyboard, false otherwise
        """
        if c.isupper():
            return True

        special = '!@#$%^&*()_+{}|:"<>?'
        if c in special:
            return True

        return False

    def update_screen(
        self,
        width: Optional[int] = None,
        height: Optional[int] = None,
        incremental: bool = False,
        x: int = 0,
        y: int = 0,
    ) -> None:
        """Send a remote framebuffer update request that will update the screen.

        If resend flag is False, this will run once in the background.
        If no parameters are set then the FBUR will request the entire screen.

        Args:
            width (Optional[int]): Width of the frame. Defaults to None.
            height (Optional[int]): Height of the frame. Defaults to None.
            incremental (bool, optional): Incremental flag (see RFC 7.5.3). Defaults to False.
            x (int, optional): Starting x coord of frame. Defaults to 0.
            y (int, optional): Starting y coord of frame. Defaults to 0.
        """
        if width is None:
            width = self._rfb_client.width
        if height is None:
            height = self._rfb_client.height
        asyncio.run_coroutine_threadsafe(
            self._rfb_client.framebuffer_update_request(
                x, y, width, height, incremental
            ),
            self._loop,
        )

    def key_event(self, key: int, down: bool) -> None:
        """Non-abstracted key event call.

        Use this command if you need something beyond the key event abstractions.

        Args:
            key (int): Key ID
            down (bool): press down
        """
        asyncio.run_coroutine_threadsafe(
            self._rfb_client.key_event(key, down), self._loop
        )

    def pointer_event(self, xpos: int, ypos: int, mask: int) -> None:
        """Non-abstracted pointer event call.

        Use this command if you need something beyond the pointer event abstractions.

        Args:
            xpos (int)
            ypos (int)
            mask (int): the mouse button ID
        """
        asyncio.run_coroutine_threadsafe(
            self._rfb_client.pointer_event(xpos, ypos, mask), self._loop
        )

    def get_screen(self) -> Image.Image | None:
        """Return latest update of the screen.

        Will return None if screen was never updated with update_screen().

        Returns
        -------
            Image: The RGBA image of the screen
        """
        return self._rfb_client.img

    def get_screen_bytes(self) -> bytes | None:
        """Return latest update of the screen in bytes.

        Will return None if screen was never updated with update_screen().

        Returns
        -------
            bytes: Image of the screen in byte format
        """
        buffer = BytesIO()
        img = self.get_screen()
        if img is not None:
            img.save(buffer, format="PNG")
            return buffer.getvalue()

        return None

    def get_clipboard(self) -> str:
        """Return the clipboard of the client.

        Returns
        -------
            str: clipboard of the client
        """
        return self._rfb_client.clipboard

    def get_pixel_format(self) -> PixelFormat:
        """Return the current PixelFormat in use.

        Returns
        -------
            PixelFormat: PixelFormat in use
        """
        return self._rfb_client.pixel_format

    def get_server_name(self) -> str:
        """Return the name of the server.

        Returns
        -------
            str: Server name
        """
        return self._rfb_client.server_name

    def get_encodings(self) -> List[Type[EncodingInterface]]:
        """Return the encodings we are using.

        Returns
        -------
            List[Type[EncodingInterface]]: List of encodings in use
        """
        return self._rfb_client.encs

    def get_bell(self) -> BellMessage | None:
        """Return a bell message if we received one.

        Returns
        -------
            BellMessage | None: A bell message if received by the client
        """
        return self._rfb_client.bell

    async def _main_loop(self) -> None:
        """Loop will keep the websocket connection alive and listen for messages."""
        try:
            async with websockets.connect(
                self.ticket_url,
                ssl=self.ssl_context,
                origin=self.origin,  # type: ignore
                subprotocols=["binary"],  # type: ignore
                ping_interval=None,
                max_size=2**25,
                read_limit=2**25,
            ) as conn:
                self._rfb_client = RFBClient(conn, self.security_type, self.shared_flag)
                await self._rfb_client.handshake()
                self._handshake_done.set()
                await self._rfb_client.listen()  # handles exceptions internally
                logger.info("VNC Client no longer listening")
        except Exception as e:
            # this block runs if the websocket connection fails for any reason
            # will set the handshake so the thread doesn't block
            # can only trigger during __init__()
            self._caught_exception = e
            self._handshake_done.set()
            raise

    async def _close(self) -> None:
        """Close the websocket connection."""
        await self._rfb_client.close()

    def _run(self) -> None:
        """Start the thread to run an asynchronous connection over a websocket."""
        logger.info("Starting VNC Client")
        asyncio.set_event_loop(self._loop)

        # create the connection task
        self._loop.create_task(self._main_loop())

        # thread is a variable now.
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()

    def close(self) -> None:
        """Terminates the thread and closes the websocket connection."""
        # takes a moment to shut down everything, wait one second after closing websocket connection.
        asyncio.run_coroutine_threadsafe(self._close(), self._loop)
        time.sleep(1)
        self._loop.call_soon_threadsafe(self._loop.stop)

        self._thread.join()
        logger.info("Client shutdown complete.")

    def __enter__(self) -> WSVNCClient:
        """Context manager enter method.

        Returns
        -------
            WSVNCClient: The client
        """
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> bool:
        """Context manager exit method.

        Args:
            exc_type (Optional[Type[BaseException]]): exception type
            exc_val (Optional[BaseException]): exception value
            exc_tb (Optional[TracebackType]): exception traceback

        Returns
        -------
            bool: client closed (in)correctly
        """
        if exc_type is not None:
            logger.error(
                f"Exception type: {exc_type}\n Exception value: {exc_val}\n Exception traceback: {exc_tb}"
            )
            return False
        self.close()
        return True
