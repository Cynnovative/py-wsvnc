import asyncio
from os import urandom
from struct import pack

from PIL import ImageChops
from websockets import WebSocketServerProtocol

from tests.conftest import MockVNCBaseServer
from wsvnc.encodings.raw_encoding import RawEncoding
from wsvnc.vnc.vnc_client import WSVNCClient


class MockVNCServer(MockVNCBaseServer):
    def __init__(self):
        super().__init__()
        
    async def frame_buffer_update(self, websocket: WebSocketServerProtocol):
        """Send the FrameBufferUpdate message with 1 rectangle 100x100 using raw
        encoding."""
        msg_type = 0
        num_rects = 1
        xpos, ypos, width, height = 0,0,100,100
        encoding_type = 0
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
        self.compare_pixel_data = pixel_data
        await websocket.send(msg)
           
    async def handler(self, websocket):
        self.clients.add(websocket)
        try:
            await self.handshake(websocket)
            await self.frame_buffer_update(websocket)
        finally:
            self.clients.remove(websocket)
            
    
async def main():
    # start the server
    server = MockVNCServer()
    await asyncio.sleep(1)  
    
    # start the client (using the VNCSecurity scheme)
    c = WSVNCClient(ticket_url="ws://localhost:8765")
    
    # the image here will be a 100x100 square of random pixels, encoded using raw encoding.
    await asyncio.sleep(1) # wait for image to process
    img = c.get_screen()
    
    # we will verify the image is the same as one constructed using raw encoding
    raw_enc = RawEncoding()
    raw_enc.read(100, 100, server.compare_pixel_data, c.get_pixel_format())
    raw_img = raw_enc.img
    # each pixel should be the same for our image generated by the FBU and here manually.
    assert ImageChops.difference(img, raw_img).getbbox() is None
    #img.save('test-framebuffer.png')
    
    # close server & client
    c.close()
    server.close()

def test():
    asyncio.run(main())


        
