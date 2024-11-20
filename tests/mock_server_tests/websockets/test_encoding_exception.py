import asyncio
from os import urandom
from struct import pack

from websockets import WebSocketServerProtocol

from tests.conftest import MockVNCBaseServer
from wsvnc.vnc.vnc_client import WSVNCClient

"""This tests our connection does not close if we encounter
an exception like a bad encoding type."""

class MockVNCServer(MockVNCBaseServer):
    def __init__(self):
        super().__init__()
        
    async def bad_frame_buffer_update(self, websocket: WebSocketServerProtocol):
        """Send the FrameBufferUpdate message with 1 rectangle 100x100 using raw
        encoding."""
        msg_type = 0
        num_rects = 1
        xpos, ypos, width, height = 0,0,100,100
        encoding_type = 1 # set to 1 for bad encoding type
        header = pack('>bxHHHHHI', msg_type, num_rects, xpos, ypos, width, height, encoding_type)
        pixel_data = b''
        for x in range(100):
            for y in range(100):
                # each pixel should be 4 bytes, we're assigning each byte to be random.
                pixel_0 = pack('>c', urandom(1))
                pixel_1 = pack('>c', urandom(1))
                pixel_2 = pack('>c', urandom(1))
                pixel_3 = pack('>c', urandom(1))
                pixel_data += pixel_0 + pixel_1 + pixel_2 + pixel_3
        
        msg = header + pixel_data
        await websocket.send(msg)
           
    async def handler(self, websocket):
        self.clients.add(websocket)
        try:
            await self.handshake(websocket)
            await self.bad_frame_buffer_update(websocket)
        finally:
            self.clients.remove(websocket)
            
    
async def main():
    # start the server
    server = MockVNCServer()
    await asyncio.sleep(1)  
    
    # start the client (using the VNCSecurity scheme)
    c = WSVNCClient(ticket_url="ws://localhost:8765")
    
    await asyncio.sleep(1)
    
    # close server & client
    c.close()
    server.close()

def test():
    asyncio.run(main())


        
