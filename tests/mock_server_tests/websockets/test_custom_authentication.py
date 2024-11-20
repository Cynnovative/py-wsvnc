import asyncio
from os import urandom
from struct import pack, unpack

from websockets import WebSocketClientProtocol, WebSocketServerProtocol

from tests.conftest import MockVNCBaseServer
from wsvnc.pixel_format import PixelFormat
from wsvnc.security.security_type_interface import SecurityTypeInterface
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
        # use Mock authentication (11)
        await websocket.send(pack('>bb', 1, 11))
        client_sec_type = await websocket.recv()
        if client_sec_type != pack('>b', 11):
            print(f"Client sec type incorrect! {client_sec_type}")
            return
        
        # send random 16-byte challenge
        challenge = urandom(16)
        await websocket.send(challenge)
        
        # get back response from client (XOR password & challenge)
        resp = await websocket.recv()
        resp_decrypted = bytes(a ^ b for a,b in zip(resp, self.password))
        
        if resp_decrypted != challenge:
            print("Decrypted response does not equal challenge!")
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
            
class MockAuthentication(SecurityTypeInterface):
    
    def __init__(self, password: bytes):
        self.password = password
    
    def type(self) -> int:
        return 11
    
    async def handshake(self, transport: WebSocketClientProtocol):
        challenge_bytes: bytes = await transport.recv()
        challenge = unpack("!16s", challenge_bytes)[0]
        
        # this mock authentication will just
        # XOR the password provided and the challenge.
        
        xor = bytes(a ^ b for a,b in zip(challenge, self.password))
        
        await transport.send(xor)
    
async def main():
    # define password (for our mock the password needs to be length 16)
    password = urandom(16)
    
    # start the server
    server = MockVNCServer(password)
    await asyncio.sleep(1)
    
    # start the client (using the VNCSecurity scheme)
    c = WSVNCClient(ticket_url="ws://localhost:8765", security_type=MockAuthentication(password=password))
    
    # close server & client
    c.close()
    #await asyncio.sleep(1)
    server.close()

def test():
    asyncio.run(main())


        
