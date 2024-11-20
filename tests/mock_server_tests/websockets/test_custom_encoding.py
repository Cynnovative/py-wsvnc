import asyncio
from os import urandom
from struct import pack

from PIL import Image
from websockets import WebSocketServerProtocol

from tests.conftest import MockVNCBaseServer
from wsvnc.encodings.encoding_interface import EncodingInterface
from wsvnc.encodings.raw_encoding import RawEncoding
from wsvnc.pixel_format import PixelFormat
from wsvnc.utils.safe_transport import SafeTransport
from wsvnc.vnc.vnc_client import WSVNCClient


class MockVNCServer(MockVNCBaseServer):
    def __init__(self):
        super().__init__()
 
    async def frame_buffer_update(self, websocket: WebSocketServerProtocol):
        """Send a FBUR using the mock encoding style."""
        msg_type = 0
        num_rects = 1
        xpos, ypos, width, height = 0,0,100,100
        encoding_type = 30
        header = pack('>bxHHHHHi', msg_type, num_rects, xpos, ypos, width, height, encoding_type)
        pixel_data = b''
        for x in range(100):
            for y in range(100):
                # each pixel should be 4 bytes, we're assigning each byte to be random.
                pixel_0 = pack('>B', urandom(1)[0] ^ 1)
                pixel_1 = pack('>B', urandom(1)[0] ^ 2)
                pixel_2 = pack('>B', urandom(1)[0] ^ 3)
                pixel_3 = pack('>B', urandom(1)[0] ^ 4)
                pixel_data += pixel_0 + pixel_1 + pixel_2 + pixel_3
        
        msg = header + pixel_data
        await websocket.send(msg)
        
    async def handler(self, websocket: WebSocketServerProtocol):
        self.clients.add(websocket)
        try:
            await self.handshake(websocket)
            await websocket.recv()
            #msg = await websocket.recv()
            #print(msg)
            await self.frame_buffer_update(websocket)
        finally:
            self.clients.remove(websocket)
      
class MockEncoding(EncodingInterface):
    """This encoding will XOR each byte in a pixel by a different number. A pixel is 4
    bytes, Byte 1 XOR 0x1 Byte 2 XOR 0x2 Byte 3 XOR 0x3 Byte 4 XOR 0x4.

    This is just a proof of concept that a custom encoding can extend on the interface.
    """
    img: Image.Image
    
    def type(self) -> int:
        return 30
    
    async def fetch_additional_data(self, width: int, height: int, transport: SafeTransport, msg: bytes, pf: PixelFormat) -> bytes:
        return msg
    
    def read(self, width: int, height: int, msg: bytes, pf: PixelFormat) -> int:
        bytes_per_pixel=4
        self.img = Image.new('RGBA', (width, height), (0,0,0,0))
        
        offs = 0
        print("Mock Encoding in use.")
        for x in range(height):
            for y in range(width):
                pixel_bytes = msg[offs:offs+bytes_per_pixel]
                offs += bytes_per_pixel
                
                if len(pixel_bytes) < bytes_per_pixel:
                    raise ValueError("Failed to read enough pixel bytes")
                
                byte_1 = pixel_bytes[0] ^ 1
                byte_2 = pixel_bytes[1] ^ 2
                byte_3 = pixel_bytes[2] ^ 3
                byte_4 = pixel_bytes[3] ^ 4
                raw_pixel = byte_1 + byte_2 + byte_3 + byte_4
                    
                # determines the color of this pixel
                # the final "&0xffff" ensures its a uint16 type
                r=(raw_pixel>>pf.red_shift & pf.red_max)&0xffff
                g=(raw_pixel>>pf.green_shift & pf.green_max)&0xffff
                b=(raw_pixel>>pf.blue_shift & pf.blue_max)&0xffff
                
                self.img.putpixel((x,y), (r,g,b,255))
        
        return offs 
      
    
async def main():
    
    # start the server
    server = MockVNCServer()
    await asyncio.sleep(1)
    
    # start the client (using the VNCSecurity scheme)
    c = WSVNCClient(ticket_url="ws://localhost:8765")
    c.set_encodings([MockEncoding])
    
    
    # the pixels in the image here will be one of two colors, red or black, in a 100x100 square
    await asyncio.sleep(1) # wait for image to process
    img = c.get_screen()
    
    # verify each pixel is either red or black
    for x in range(100):
        for y in range(100):
            assert img.getpixel([x,y]) == (255, 0, 0, 255) or img.getpixel([x,y]) == (0, 0, 0, 255)
    #img.save('test-custom-encoding.png')
    
    assert c.get_encodings() == [MockEncoding, RawEncoding]
    
    # close server & client
    c.close()
    server.close()

def test():
    asyncio.run(main())


        
