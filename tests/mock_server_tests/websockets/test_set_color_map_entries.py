import asyncio
import random
from struct import pack

from websockets import WebSocketServerProtocol

from tests.conftest import MockVNCBaseServer
from wsvnc.pixel_format import PixelFormat
from wsvnc.vnc.vnc_client import WSVNCClient


class MockVNCServer(MockVNCBaseServer):
    def __init__(self):
        super().__init__()
    
    async def handshake(self, websocket):
        """RFB handshake from the servers perspective.

        Uses color map. RFC 6143 section 7.1
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
        pixel_format.true_color = 0 # set false to use color map.
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

    async def color_map_entries_message(self, websocket: WebSocketServerProtocol):
        header = pack("!BxHH", 1, 0, 10000)
        colors: bytes = b''
        for _ in range(10000):
            colors += pack(">HHH", random.randint(0, 256), random.randint(0, 256), random.randint(0, 256))
        msg = header + colors
        await websocket.send(msg)
    
    async def frame_buffer_update(self, websocket: WebSocketServerProtocol):
        """Send a FBUR where each pixel is alternated between the first & last items in
        the color map."""
        msg_type = 0
        num_rects = 1
        xpos, ypos, width, height = 0,0,100,100
        encoding_type = 0
        header = pack('>bxHHHHHI', msg_type, num_rects, xpos, ypos, width, height, encoding_type)
        pixel_data = b''
        for x in range(100):
            for y in range(100):
                # each pixel should be 4 bytes, we're assigning each byte to be random.
                if ((x + y) % 2) == 0:
                    pixel_data += pack(">I", 0)
                else:
                    pixel_data += pack(">I", 9999)
        
        msg = header + pixel_data
        await websocket.send(msg)
        
    async def handler(self, websocket):
        self.clients.add(websocket)
        try:
            await self.handshake(websocket)
            await self.color_map_entries_message(websocket)
            await asyncio.sleep(1)
            await self.frame_buffer_update(websocket)
            
        finally:
            self.clients.remove(websocket)
              
async def main():
    # start the server
    server = MockVNCServer()
    await asyncio.sleep(1)  
    
    # start the client
    c = WSVNCClient(ticket_url="ws://localhost:8765")
    await asyncio.sleep(3) # wait for image to process
    
    assert c.get_pixel_format().color_map is not None
    
    img = c.get_screen()
    
    # the image here is a 100x100 checkered square where every other
    # pixel is either the first color in the map or the last
    first_color = c.get_pixel_format().color_map[0]
    last_color = c.get_pixel_format().color_map[9999]
    first_pixel = (first_color.r, first_color.g, first_color.b, 255)
    last_pixel = (last_color.r, last_color.g, last_color.b, 255)
    for x in range(100):
        for y in range(100):
            if ((x + y) % 2) == 0:
                    assert img.getpixel([x, y]) == first_pixel
            else:
                assert img.getpixel([x, y]) == last_pixel
    #img.save('test-color-map-entries.png')
    
    # close server & client
    c.close()
    server.close()

def test():
    asyncio.run(main())


        
