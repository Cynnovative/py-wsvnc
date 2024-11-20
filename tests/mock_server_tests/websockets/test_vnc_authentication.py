import asyncio
from os import urandom
from struct import pack

from Cryptodome.Cipher import DES
from websockets import WebSocketServerProtocol

from tests.conftest import MockVNCBaseServer
from wsvnc.pixel_format import PixelFormat
from wsvnc.security.vnc_security import VNCSecurity
from wsvnc.vnc.vnc_client import WSVNCClient


class MockVNCServer(MockVNCBaseServer):
    """Mock VNC server that will pretend to handle standard messages, and will attempt
    to use VNC authentication as its security handshake."""
    def __init__(self, password):
        super().__init__()
        self.password = password
    
    async def handshake(self, websocket: WebSocketServerProtocol):
        """Implements the RFB handshake from the servers perspective.

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
        # use VNC authentication (2)
        await websocket.send(pack('>bb', 1, 2))
        client_sec_type = await websocket.recv()
        if client_sec_type != pack('>b', 2):
            print(f"Client sec type incorrect! {client_sec_type}")
            return
        
        # send random 16-byte challenge
        challenge = urandom(16)
        await websocket.send(challenge)
        
        # get back response from client (DES encrypted challenge using password as key)
        resp = await websocket.recv()
        key = bytes(sum((128 >> i) if (k & (1 << i)) else 0 for i in range(8)) for k in self.password)
        des = DES.new(key, DES.MODE_ECB)
        if des.decrypt(resp) != challenge:
            print(f"Decrypted response does not equal challenge! {des.decrypt(resp)}")
            await websocket.send(pack('>I', 1))
            return
        else:
            await websocket.send(pack('>I', 0)) # tell client security result is good
        
        ## Handle client init
        client_share_flag = await websocket.recv()
        if client_share_flag != pack('>b', 1):
            print("Client share flag incorrect!")
            return
        
        ## Handle server init
        # the frame buffer width + height
        framebuffer_width = pack('>H', 1080)
        framebuffer_height = pack('>H', 720)
        
        # the pixel format the server will use
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
        pixel_format_bytes = pixel_format.write_pixel_format()
        
        # make up a name for the desktop
        name = pack(">8s", b"testname")
        name_len = pack(">I", 8)
        
        await websocket.send(framebuffer_width + framebuffer_height + pixel_format_bytes + name_len + name)
    
    async def handler(self, websocket):
        self.clients.add(websocket)
        try:
            await self.handshake(websocket)
        finally:
            self.clients.remove(websocket)
            
    
async def main():
    # define password
    password = urandom(8)
    
    # start the server
    server = MockVNCServer(password)
    await asyncio.sleep(1)  
    
    # start the client (using the VNCSecurity scheme)
    c = WSVNCClient(ticket_url="ws://localhost:8765", security_type=VNCSecurity(password=password))
    
    # close server & client
    c.close()
    server.close()

def test():
    asyncio.run(main())


        
