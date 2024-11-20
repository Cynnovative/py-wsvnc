"""Base VNC Server that is used by all mock tests."""

import asyncio
import logging
import socket
import threading
import time
from struct import pack

from websockets.server import serve
from websockify import WebSocketProxy

from wsvnc.pixel_format import PixelFormat

logging.basicConfig(level=logging.DEBUG)

class MockVNCBaseServer:
    """Mock VNC server that will pretend to handle standard messages."""
    
    def __init__(self, ):
        self.clients = set()
        self.loop = asyncio.new_event_loop()
        self.stop = self.loop.create_future()
        self.run()
    
    async def handshake(self, websocket):
        """RFB handshake from the servers perspective.

        RFC 6143 section 7.1
        """
        # the websocket handling the connection
        #websocket = list(self.s.websockets)[0]
        
        ## Protocol Version handshake
        # verify client RFB version
        await websocket.send(b'RFB 003.008\n')
        client_rfb_version = await websocket.recv()
        if client_rfb_version != b'RFB 003.008\n':
            print("Client RFB version incorrect!")
            return

        ## Security handshake
        # use No authentication (length of security types is 1, and type 1 is no security)
        await websocket.send(pack('>bb', 1, 1))
        client_sec_type = await websocket.recv()
        if client_sec_type != pack('>b', 1):
            print(f"Client sec type incorrect! {client_sec_type}")
            return
        await websocket.send(pack('>I', 0)) # tell client security result is good
        
        ## Handle client init
        client_share_flag = await websocket.recv()
        if client_share_flag != pack('>b', 1):
            print("Client share flag incorrect!")
            return
        
        ## Handle server init
        # the frame buffer width + height
        framebuffer_width = pack('>H', 100)
        framebuffer_height = pack('>H', 100)
        
        # the pixel format the server will use
        pixel_format = PixelFormat()
        pixel_format.bpp = 32
        pixel_format.depth = 0
        pixel_format.big_endian = 1
        pixel_format.true_color = 1 # set false to use color map.
        pixel_format.red_max = 256
        pixel_format.green_max = 256
        pixel_format.blue_max = 256
        pixel_format.red_shift = 0
        pixel_format.green_shift = 8
        pixel_format.blue_shift = 16
        pixel_format_bytes = pixel_format.write_pixel_format()
        
        # make up a name for the desktop
        name = pack(">8s", b"testname")
        name_len = pack(">I", 8)
        
        await websocket.send(framebuffer_width + framebuffer_height + pixel_format_bytes + name_len + name)

    async def main_loop(self):
        """Create asynchronous websocket server."""
        async with serve(self.handler, "localhost", 8765) as s:
            self.s = s
            await self.stop  # run forever
    
    def run(self):
        asyncio.set_event_loop(self.loop)
        self.loop.create_task(self.main_loop())
        self.thread = threading.Thread(target=self.loop.run_forever)
        self.thread.start()
    
    async def _close(self):
        self.stop.set_result(None)
    
    def close(self):
        asyncio.run_coroutine_threadsafe(self._close(), self.loop)
        time.sleep(1)
        #self.stop.set_result(None)
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join()
            
class MockTCPBaseServer:
    """Mock TCP server that will pretend to handle standard messages."""
    
    def __init__(self, tcp_host='127.0.0.1', tcp_port=5909, ws_port=5910):
        self.tcp_host = tcp_host
        self.tcp_port = tcp_port
        self.ws_port = ws_port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.tcp_host, self.tcp_port))
        self.server.listen()
        self.proxy_thread = None
    
    def run(self):
        """Start a TCP server."""
        print(f"TCP Server listening on {self.tcp_host}:{self.tcp_port}")
        try:
            while True:
                conn, addr = self.server.accept()
                client_thread = threading.Thread(target=self.handle_client, args=(conn, addr))
                client_thread.start()
        finally:
            self.server.close()
            

def run_websockify_proxy():
    """Start a websockify proxy."""
    try:
        logging.debug("Starting Websockify proxy")
        proxy = WebSocketProxy(target_host="127.0.0.1", target_port=5909, listen_port=5910)
        proxy.start_server()
    except Exception as e:
        logging.error(f"Failed to start Websockify proxy: {e}")