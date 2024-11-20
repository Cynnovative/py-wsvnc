# py-wsvnc

`py-wsvnc` is a python VNC client that operates over WebSocket connections. It was built to work with VMWares ESXi, but can be used for other WebSocket VNC servers like [x11vnc/libvncserver](http://libvncserver.sourceforge.net/), and proxied servers with [WebSockify](https://github.com/novnc/websockify).

The design was inspired by two existing VNC libraries, in order to make the client non-blocking, self-contained and easily expandable:
[pyVNC](https://github.com/cair/pyVNC)
and [go-vnc](https://github.com/mitchellh/go-vnc/)

Like other python VNC clients in the wild, `py-wsvnc` is excellent for automating tasks on a VNC server in a headless manner. However, unlike other VNC clients, `py-wsvnc` supports use with WebSocket based VNC servers. Additionally, `py-wsvnc` does not use the `twisted` package found in some of the more popular clients, instead relying on the `websockets` and `asyncio` packages.

## Benefits

- Enables VNC connections over websockets in a python client package (notable compared to pyVNC, asyncvnc, and vncdotool)
- Implements RFC 6143 core functionality (aside from limitations marked below)
- Threaded client that is non-blocking and can handle & send messages simultaneously.
- Capable of handling ESXi VNC connections using modern API features (`AcquireTicket()`).
- Capable of handling TCP VNC servers proxied by WebSockify.
- Multiple interfaces available to easily extend any custom encoding, server messages and security handshakes.

## Requirements

The project requires these python packages: `websockets~=12.0`, `pillow~=10.4.0`, `pycryptodomex~=13.9.0`

## Installation

Clone the repository and `pip` install:

```bash
git clone https://github.com/Cynnovative/py-wsvnc
cd py-wsvnc/
pip install .
```

Or install directly:

```bash
pip install git+https://github.com/Cynnovative/py-wsvnc
```

## Getting Started: Base Setup

If you already have a WebSocket VNC server ready to go, you can establish the VNC client like so (remember to replace `ws://localhost:5900` with your URI):

```python
from wsvnc.vnc.vnc_client import WSVNCClient
from time import sleep

vnc = WSVNCClient(ticket_url='ws://localhost:5900')
vnc.set_resend_flag()

# allow time for FBUR to process.
sleep(1)

# move mouse to position(500, 500)
vnc.move(500, 500)
# left click at position(500, 500)
sleep(.5)
vnc.left_click(500, 500)

sleep(1) # let the screen refresh.
vnc.get_screen().show()

vnc.close() # close the client.
```

## Getting Started: Context Manager

The client can also be used as a context manager:

```python
from wsvnc.vnc.vnc_client import WSVNCClient
from time import sleep

with WSVNCClient(ticket_url='ws://localhost:5900') as vnc:
    vnc.move(500, 500)
    vnc.update_screen() # send FBUR.

    sleep(1) # allow time for screen to update.
    vnc.get_screen().show() # displays image.
```

## Getting Started: ESXi Setup

You can use `pyvmomi` (not a requirement) to establish a VNC connection to a VM on an ESXi machine.

You must have `pyvmomi` installed separately.

```python
from ssl import CERT_NONE, PROTOCOL_TLS_CLIENT, SSLContext

from pyVmomi import vim
from pyVim.connect import SmartConnect
from time import sleep
from wsvnc.vnc.vnc_client import WSVNCClient

def connect_to_vcenter(server, user, password, ctx=None, port=443):
    try:
        si = SmartConnect(host=server, user=user, pwd=password, port=port, sslContext=ctx)
        print("Connected to vCenter server successfully!")
        return si
    except Exception as e:
        print(f"Failed to connect to vCenter server: {e}")
        return None

def main():
    server='esxi.host'
    password='password'
    user='username@vsphere.local'
    name = 'vm-name' # make sure this VM is turned on.
    # Bypass SSL certificate verification
    # ignore if you're not using TLS
    ctx = SSLContext(PROTOCOL_TLS_CLIENT)
    ctx.check_hostname=False
    ctx.verify_mode=CERT_NONE
    
    si = connect_to_vcenter(server, user, password, ctx) # connect to vSphere/ESXi
    
    # grab the VM with the provided name.
    content = si.RetrieveContent() 
    obj_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)
    vm_list = obj_view.view
    obj_view.Destroy()
    vm: vim.VirtualMachine = [vm for vm in vm_list if vm.name == name][0]
    
    # get the WebSocket url necessary to connect to the VM.
    mks_ticket = vm.AcquireTicket('webmks')
    url = mks_ticket.url
    
    # start client, fetch & show screen then disconnect.
    with WSVNCClient(ticket_url=url, ssl_context=ctx) as vnc:
        vnc.move(0, 0) # move the mouse
        vnc.set_resend_flag() # send continuous FBURs
        
        sleep(1) # allow time for the full screen to update.
        vnc.move(1024, 768)
        sleep(5)
        vnc.get_screen().show() # show the screen
    
if __name__ == "__main__":
    main()
```

Note: It's possible that `vm.AcquireTicket('webmks')` will provide a faulty hostname, you may need to manually check this and fix the host name.

Note: If you receive a mostly black screen from ESXi it's because the client is receiving incomplete frame buffer updates. You can either try moving the mouse more and waiting longer, or alternatively try using TightPNG encoding (specified below) which should solve that issue.

## More Options

If you want the screen to remain updated by default, set `keep_screen_updated` when instantiating the client:

```python
vnc = WSVNCClient(ticket_url='ws://localhost:5900', keep_screen_updated=True)
```

(Note client at startup will send a Framebuffer update request for the entire screen. After this it will
send FBURs for every FBU received with incremental set to `True`.)

If you want to disconnect any existing VNC connections to the server, set the shared_flag to 0:

```python
vnc = WSVNCClient(ticket_url='ws://localhost:5900', shared_flag=0)
```

If you want to use VNC security (or another security type you implement), set the security_type variable:

```python
from wsvnc.security.vnc_security import VNCSecurity

vnc = WSVNCClient(ticket_url='ws://localhost:5900', security_type=VNCSecurity('password'))
```

## Using special keys

If you want to use special keys specified in [RFC 7.5.4](https://datatracker.ietf.org/doc/html/rfc6143#section-7.5.4) then you can do so by importing them from `wsvnc/constants.py`:

```python
from wsvnc.constants import KEY_Return

vnc.send_key(KEY_Return) # presses the return/enter key on the server
```

## Using TightPNG Encoding on ESXi

You can also use TightPNG encoding with ESXi so FBUs are handled faster.

```python
from wsvnc.encodings.tightpng_encoding import TightPNGEncoding
from wsvnc.encodings.tightpng_encoding_jpeg_10 import TightPNGEncodingJpegQuality10

with WSVNCClient(ticket_url=url, ssl_context=ctx, keep_screen_updated=True) as vnc:
    vnc.set_encodings([TightPNGEncoding, TightPNGEncodingJpegQuality10])
    
    count = 100
    while count > 0:
        vnc.move(random.randint(0, 1024), random.randint(0, 728))
        sleep(1)
        vnc.get_screen().save("tightpng.png")
        count -= 1
```

## Using CopyRect Encoding on ESXi

To enable CopyRect encoding on ESXi you must use TightPNG & VMWDefineCursor encodings.

```python
from wsvnc.encodings.tightpng_encoding import TightPNGEncoding
from wsvnc.encodings.tightpng_encoding_jpeg_10 import TightPNGEncodingJpegQuality10
from wsvnc.encodings.copyrect_encoding import CopyRectEncoding
from wsvnc.encodings.vmware_define_cursor_encoding import VMWDefineCursorEncoding

with WSVNCClient(ticket_url=url, ssl_context=ctx, keep_screen_updated=True) as vnc:
        vnc.set_encodings([CopyRectEncoding, TightPNGEncoding, TightPNGEncodingJpegQuality10, VMWDefineCursorEncoding])
        
        count = 50
        while count > 0:
            vnc.move(random.randint(0, 1024), random.randint(0, 728))
            sleep(1)
            vnc.get_screen().save("tightpng.png")
            count -= 1
```

## Additional Uses

You can find an overview of our api in the [usage.md](usage.md) file at the root of the project. This document contains examples and functionality not necessarily covered in this README.

## Developing

We're open to additions to `py-wsvnc`. If you would like to make an addition, then please submit an issue or a PR on this github. You can find an overview of the structure of the project in [developer-overview.md](developer-overview.md) at the root.

To develop, make sure you have all developer dependencies installed:
`pip install .[dev]`

and that for whatever changes you make there are appropriate unit or functional tests in a corresponding file in `tests/` (put functional tests in `tests/mock_server_tests`). Additionally, ensure the coverage is still above 90% by running the following:

```bash
pip install -e .
coverage run -p --source=src -m pytest
coverage run -p --source=src -m pytest tests/mock_server_tests
coverage combine
coverage report
```

Also, verify you pass our linter checks:

```bash
mypy src
ruff check src
ruff format --check src
isort --check src
```

## Issues

If you have a feature request or bug please use the Github issues page and make your request there. Please include an appropriate title and description including any output so that we can help debug any problems.

## License

`py-wsvnc` is covered by the [MIT license](LICENSE).

## Acknowledgements

This research was developed with funding from the Defense Advanced Research Projects Agency (DARPA). The views, opinions and/or findings expressed are those of the author and should not be interpreted as representing the official views or policies of the Department of Defense or the U.S. Government.  

Distribution Statement A – Approved for Public Release, Distribution Unlimited

## Limitations

- The client does not currently support `VMWares TightDiff Comp` encoding as used in their WebMKS. That is currently a WIP, do not use
  that encoding with your project.
- The client does not implement [TRLE](https://datatracker.ietf.org/doc/html/rfc6143#section-7.7.5), [ZRLE](https://datatracker.ietf.org/doc/html/rfc6143#section-7.7.6), or [Cursor Pseudo Encoding](https://datatracker.ietf.org/doc/html/rfc6143#section-7.8.1) encodings from RFC 6143.
