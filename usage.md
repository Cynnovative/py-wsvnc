# `py-wsvnc` Usage

Here we will cover what you can do with the api provided in `vnc/vnc_client.py`, which is where the main client is defined.

## Initializing, closing and resend flag

- ```python
  def __init__(
          self,
          ticket_url: str,
          ssl_context: Optional[SSLContext] = None,
          origin: str = "http://localhost",
          security_type: security_type_interface.SecurityTypeInterface = no_security.NoSecurity(),
          keep_screen_updated: bool = False,
          shared_flag: int = 1
      ):
  ```

  You must provide a `ticket_url` to the client to authenticate. This must be a WebSocket URL, plain WS or WSS.

  If using WSS you may also wish to provide an `ssl_context`, which can be helpful for self-signed certificates.

  If you want to use a different security type than none, then you must set the `security_type` variable to your desired type. See `tests/mock_server_tests/websockets/test_custom_authentication` to see how to design your own security type.

  If you wish to change your origin, then you may do so by setting the `origin` parameter.

  If you wish for the client to automatically send FBURs whenever an FBU is handled, then set the `keep_screen_updated` parameter to `True`.

  If you wish to close all VNC connections to the server, set the `shared_flag` parameter to 0.

- `def set_resend_flag(self, on: bool = True) -> None:`
  To tell the client to automatically send FBURs whenever an FBU is handled, you can set this flag, or disable it even. This is done at initialization if you set the `keep_screen_updated` parameter.

- `def close(self):`
  If you use the client outside a context manager, then you want to call `close()` when you're done to stop the thread and clean up the connection. Inside a context manager this function is called when the context is closed.

## mouse interactions

Below are the available APIs for sending mouse interactions to the server.

## pointer event

`def pointer_event(self, xpos: int, ypos: int, mask: int) -> None:`

`pointer_event()` sends a pointer event message to the server as defined in RFC 6143 7.5.5. This method is called by all the other mouse API calls covered. Use this if the provided mouse APIs don't provide what you need:

```python
with WSVNCClient(ticket_url=url) as vnc:
    vnc.pointer_event(100, 100, 1) # holds the left mouse button at 100, 100
```

## move & release

`def move(self, xpos: int, ypos: int) -> None:`
`def release(self, xpos: int, ypos: int) -> None:`

These methods will move the mouse with no button pressed to a specified location (will release any mouse buttons currently pressed):

```python
with WSVNCClient(ticket_url=url) as vnc:
    vnc.move(0, 0) # move the mouse to 0,0 (top left) on the screen
```

## left click

`def left_click(self, xpos: int, ypos: int) -> None:`

`left_click()` will first move the mouse using `move()` to a specified location, then press the left mouse button then release it:

```python
with WSVNCClient(ticket_url=url) as vnc:
    vnc.left_click(0, 0) # left click at 0,0
```

## double left click

`def double_left_click(self, xpos: int, ypos: int) -> None:`

`double_left_click()` makes two `left_click()` calls at a specified location separated by 50 milliseconds.

```python
with WSVNCClient(ticket_url=url) as vnc:
    vnc.double_left_click(0, 0) # double left click at 0,0
```

## press

`def press(self, xpos: int, ypos: int) -> None:`

`press()` will first use `move()` to move the mouse to a specified location, then press and hold the left mouse button:

```python
with WSVNCClient(ticket_url=url) as vnc:
    vnc.release(0, 0) # press and hold at 0,0
```

## right click

`def right_click(self, xpos: int, ypos: int) -> None:`

`right_click()` will first use `move()` to move the mouse to a specified location, then press the right click button then release it:

```python
with WSVNCClient(ticket_url=url) as vnc:
    vnc.right_click(0, 0) # right click at 0,0
```

## wheel up

`def wheel_up(self, xpos: int, ypos: int, delay_ms: int = 50) -> None:`

`wheel_up()` will use the scroll wheel up button at a specified location for a specified duration (defaults to 50 milliseconds):

```python
with WSVNCClient(ticket_url=url) as vnc:
    vnc.wheel_up(0, 0) # scroll up at 0,0 for 50 milliseconds (default)
```

## wheel down

`def wheel_down(self, xpos: int, ypos: int, delay_ms: int = 50) -> None:`

`wheel_donw()` does the same as `wheel_up()` except it uses the wheel down button:

```python
with WSVNCClient(ticket_url=url) as vnc:
    vnc.wheel_down(0, 0) # scroll down at 0,0 for 50 milliseconds (default)
```

## wheel

`def wheel(self, xpos: int, ypos: int, delay_ms: int, down: bool = False) -> None:`

`wheel()` will call either `wheel_down()` or `wheel_up()` at a specified location with a set delay depending on the `down` parameter:

```python
with WSVNCClient(ticket_url=url) as vnc:
    vnc.wheel(0, 0, 100, false) # scroll up at 0,0 for 100 milliseconds
    vnc.wheel(0, 0, 100, true) # scroll down at 0,0 for 100 milliseconds
```

## click and drag

`def click_and_drag(self, xpos: int, ypos: int, newx: int, newy: int) -> None:`

`click_and_drag()` first calls `move()` to move the mouse to `(xpos, ypos)`, then presses the left mouse button and holds it over to `(newx, newy)`:

```python
with WSVNCClient(ticket_url=url) as vnc:
    vnc.click_and_drag(0, 0, 100, 100) # left click at 0, 0 and hold the button to 100, 100
```

## key interactions

Below are key interaction API calls you can make with the client.

## key event

`def key_event(self, key: int, down: bool) -> None:`

`key_event()` sends a key event message to the server as defined in RFC 6143 7.5.4. This method is called by all the other key based API calls covered. Use this if the other key APIs don't provide what you need:

```python
with WSVNCClient(ticket_url=url) as vnc:
    vnc.key_event(ord("s"), true) # tells server to hold down the "s" key.
```

## send key

`def send_key(self, key: int) -> None:`

`send_key()` will press a button on the keyboard as defined by the key parameter, then wait 100 milliseconds and release it:

```python
with WSVNCClient(ticket_url=url) as vnc:
    vnc.send_key(ord("s")) # types "s" on the screen
```

## emit text

`def emit_text(self, text: str) -> None:`

`emit_text()` writes the text provided on the screen for standard character keys on an US keyboard. It does this by pressing the shift button if the key is special (for keys `!@#$%^&*()_+{}|:"<>?`), or if the character is capitalized in the text. It then presses the key by using the `send_key()` method.

This method only works with certain special characters on standard US keyboards, and only with the English alphanumeric alphabet.

```python
with WSVNCClient(ticket_url=url) as vnc:
    vnc.emit_text("Hel!0") # types Hel!0 on the screen
```

## other client to server messages

the following APIs are to implement the rest of the RFC 6143 server to client interactions, section 7.5

## set pixel format

`def set_pixel_format(self, pf: PixelFormat) -> None:`

`set_pixel_format()` tells the server to use a different pixel format as defined in RFC 6143 7.5.1. You must initialize a `PixelFormat` object to use this.

```python
with WSVNCClient(ticket_url=url) as vnc:
    pixel_format = PixelFormat()
    pixel_format.bpp = 32
    pixel_format.depth = 0
    pixel_format.big_endian = 1
    pixel_format.true_color = 1
    pixel_format.red_max = 256
    pixel_format.green_max = 256
    pixel_format.blue_max = 256
    pixel_format.red_shift = 0
    pixel_format.green_shift = 8
    pixel_format.blue_shift = 16
    vnc.set_pixel_format(pixel_format) # tells the server to use the pixel format provided.
```

## set encodings

`def set_encodings(self, encs: List[Type[EncodingInterface]]) -> None:`

`set_encodings()` tells the server to use encodings specified in the `encs` parameter list. You must provide the types, DO NOT provide the objects for the encodings (IE, provide `[RawEncoding]`, not `[RawEncoding()]`). This implements RFC 6143 7.5.2:

```python
from wsvnc.encodings.tightpng_encoding import TightPNGEncoding
from wsvnc.encodings.tightpng_encoding_jpeg_10 import TightPNGEncodingJpegQuality10
from wsvnc.encodings.copyrect_encoding import CopyRectEncoding
from wsvnc.encodings.vmware_define_cursor_encoding import VMWDefineCursorEncoding

with WSVNCClient(ticket_url=url) as vnc:
    # tells an ESXi server to use CopyRect, TightPNG encodings (the two others are pseudo encodings required for ESXi)
    vnc.set_encodings([CopyRectEncoding, TightPNGEncoding, TightPNGEncodingJpegQuality10, VMWDefineCursorEncoding])
```

## cut text

`def cut_text(self, text: str) -> None:`

`cut_text()` sends a cut text message as defined in RFC 6143 7.5.6. The client tells the server it has text in its clipboard:

```python
with WSVNCClient(ticket_url=url) as vnc:
    vnc.cut_text("text") # client tells the server that 'text' is in its clipboard
```

## update screen

`def update_screen(self, width: Optional[int]=None, height: Optional[int]=None, incremental: bool=False, x: int=0, y: int=0) -> None:`

`update_screen()` sends a FBUR to the server that is specified by its width, height, if its an incremental or not and the position at (x, y). If you don't provide width or height then the entire screen will be requested. This implementation is defined in RFC 6143 7.5.3:

```python
with WSVNCClient(ticket_url=url) as vnc:
    vnc.update_screen() # client sends a non-incremental FBUR for the entire screen
```

## getters

There are a few different getters you can use to fetch data from the client.

- `def get_screen(self) -> Image.Image | None:`
  returns the `PIL.Image.Image` object associated with the screen if it has been initialized by a frame buffer update. If the client has not yet received a frame buffer update, this method will return None.

- `def get_screen_bytes(self) -> bytes | None:`
  returns the byte representation of the `PIL.Image.Image` object, or None if the screen has not been initialized due to the client not yet receiving an FBU.

- `def get_clipboard(self) -> str:`
  returns any text in the clipboard for the client either set by `cut_text()` above or handled by receiving a `ServerCutText` message from the server as defined in RFC 6143 7.6.4

- `def get_pixel_format(self) -> PixelFormat:`
  returns the current pixel format used by the client, which is either set by a `set_pixel_format()` client request or during the handshake.

- `def get_server_name(self) -> str:`
  returns the name of the server the client is connected to (provided during the opening handshake)

- `def get_encodings(self) -> List[Type[EncodingInterface]]:`
  returns all the encodings currently in use by the client and server.

- `def get_bell(self) -> BellMessage | None:`
  returns a BellMessage object if the client received a bell from the server, or None otherwise.
