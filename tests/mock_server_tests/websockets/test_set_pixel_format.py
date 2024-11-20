import asyncio
from struct import pack

from websockets import WebSocketServerProtocol

from tests.conftest import MockVNCBaseServer
from wsvnc.pixel_format import PixelFormat
from wsvnc.vnc.vnc_client import WSVNCClient


class MockVNCServer(MockVNCBaseServer):
    def __init__(self, pf: PixelFormat):
        super().__init__()
        self.pf = pf
    
    async def recv_set_pixel_format(self, websocket: WebSocketServerProtocol):
        set_pixel_format_msg = await websocket.recv()
        assert set_pixel_format_msg == pack("!Bxxx", 0) + self.pf.write_pixel_format()[1:]
        
        
    async def handler(self, websocket):
        self.clients.add(websocket)
        try:
            await self.handshake(websocket)
            await self.recv_set_pixel_format(websocket)
        finally:
            self.clients.remove(websocket)
            
async def main():
    
    # set pixel format
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
    
    # start the server
    server = MockVNCServer(pixel_format)
    await asyncio.sleep(1)  
    
    # start the client
    c = WSVNCClient(ticket_url="ws://localhost:8765")
    
    c.set_pixel_format(pixel_format)
    await asyncio.sleep(1)
    
    assert c.get_pixel_format() == pixel_format

    
    # close server & client
    c.close()
    server.close()

def test():
    asyncio.run(main())


        
