# `py-wsvnc` Developer Overview

This overview is for developers to help them understand the code base.

## Encodings

- Interface class to add additional encodings
  - Implements `read()`, `fetch_additional_data()` & `type()` functions
    - `read()` decodes a rectangle of the screen (a block of pixels), and saves it to a `PIL.Image.Image` object.
    - `fetch_additional_data()` verifies we have received all the data the encoding type requires, waits for more if not true.
    - `type()` Returns the 8-bit integer to represent the type of encoding.
- Currently implements raw, TightPNG, and CopyRect encodings, and pseudo encodings VMWare Define Cursor, JPEG10 Quality, and desktop size

## RFB

- Contains the RFB Client that satisfies the [protocol](https://datatracker.ietf.org/doc/html/rfc6143)
- Does all of the communication over the websocket between the client & server
- Can send & receive data simultaneously
- Saves any [FrameBufferUpdates](https://datatracker.ietf.org/doc/html/rfc6143#section-7.6.1) into a `PIL.Image.Image` object.

## Security

- Interface class that allows user to handle multiple different security types with
  VNC
  - Implements both `handshake()` & `type()` functions
  - `handshake()` completes the security handshake with the server so the client may
    authenticate. Different security protocols will have different handshakes.
  - `type()` returns the 8-bit integer value that represents the security type
- Implements [none](https://datatracker.ietf.org/doc/html/rfc6143#section-7.2.1) security type (standard with ESXi)
- Implements [VNC](https://datatracker.ietf.org/doc/html/rfc6143#section-7.2.2) authentication security type

## Server Messages

- Interface to add custom VNC server messages
  - Implements both `read()` & `type()` functions
  - `read()` handles the incoming message from the server for the client.
  - `type()` returns the 8-bit integer value to represent what kind of message it is.
- `FrameBufferUpdate` class handles pixels sent from the server to the client ([RFC](https://datatracker.ietf.org/doc/html/rfc6143#section-7.6.1)).
- `CutTextMessage` class handles when text is sent from the server to the client ([RFC](https://datatracker.ietf.org/doc/html/rfc6143#section-7.6.4)).
- `BellMessage` class handles when the server says an audible noise should be played on the
  client ([RFC](https://datatracker.ietf.org/doc/html/rfc6143#section-7.6.3)).

## Utils

Contains a logger for the entire package.

## VNC

- Contains the main client our agents and users should operate with.
- The client implements all of the standard actions a human would perform on a
  desktop.
- `WSVNCClient` is the class that
  establishes the websocket connection and allows for commands to be sent to
  the VNC server (our VMs).
  - Works by setting up an asynchronous websocket connection that can listen for messages and
    send new ones.
  - The Thread effectively runs the Client object in the background so it can be callable at any
    point to send a new command.

## Color, Constants, & Rectangles .py

- `color.py` is a class file to represent pixel data sent from the VNC server. It’s
  used by the encoding class to store a rectangles pixel data (RGB).
- `constants.py` contains some constants that can be used by the user (for
  the keyboard constants), and the `RFBClient` for a list of supported RFB
  protocol versions (which is only one right now).
- `rectangles.py` is a class file to represent a rectangle sent from the VNC
  server as part of its `FrameBufferUpdate` message.
  - Holds width, height, and the starting x and y coordinates of the rectangle.
  - Holds the encoding type used by the server, which in turn will hold the RGB color data for
    each pixel.

## pixel_format.py

- A class file that holds the pixel formatting that will be sent back by the server
  in `FrameBufferUpdate` messages.
- `read_format()` helper is useful to de-obfuscate the initial handshake in the
  RFB client. It initializes the `PixelFormat` object held by the RFB Client.
- `PixelFormat.write_pixel_format()` is a helper that packs the current
  object into bytes. It’s used when the client sends a [SetPixelFormat](https://datatracker.ietf.org/doc/html/rfc6143#section-7.5.1) message.
- `PixelFormat` is used to convert the pixel into its raw RGB components
  during `FrameBufferUpdates`.
  - Ex: `Red = (raw_pixel>>pf.red_shift & pf.red_max)&0xffff`

## tests

- Includes examples extending client functionality
  - Custom authentication test
  - Custom encoding test
- Also implements some tests to verify functionality we don’t use with ESXi
  - Color map test
  - Cut text test
  - VNC authentication test
  - Frame buffer test
  - Basic handshake test
