import logging
from multiprocessing import Process
from os import urandom
from socket import socket
from struct import pack
from time import sleep

from tests.conftest import MockTCPBaseServer, run_websockify_proxy
from wsvnc.pixel_format import PixelFormat
from wsvnc.vnc.vnc_client import WSVNCClient

logging.basicConfig(level=logging.DEBUG)

class MockTCPServer(MockTCPBaseServer):
    
    def framebufferupdate(self, connection: socket):
        """Send the FrameBufferUpdate message with 10 rectangles of 100x100 using raw
        encoding."""
        msg_type = 0
        num_rects = 10
        msg = pack('>bxH', msg_type, num_rects)
        xpos, ypos, width, height = 0,0,100,100
        encoding_type = 0
        for r in range(num_rects):
            pixel_data = b''
            rectangle = pack('>HHHHI', xpos, ypos, width, height, encoding_type)
            for x in range(100):
                for y in range(100):
                    # each pixel should be 4 bytes, we're assigning each byte to be random.
                    pixel_0 = pack('>c', urandom(1))
                    pixel_1 = pack('>c', urandom(1))
                    pixel_2 = pack('>c', urandom(1))
                    pixel_3 = pack('>c', urandom(1))
                    pixel_data += pixel_0 + pixel_1 + pixel_2 + pixel_3
            msg += rectangle + pixel_data
            xpos += 100
            ypos += 100
        connection.send(msg)
    
    def handshake(self, connection: socket):
        """RFB handshake from the servers perspective.

        RFC 6143 section 7.1
        """
        # the websocket handling the connection
        #websocket = list(self.s.websockets)[0]
        
        ## Protocol Version handshake
        # verify client RFB version
        connection.send(b'RFB 003.008\n')
        client_rfb_version = connection.recv(12)
        if client_rfb_version != b'RFB 003.008\n':
            print("Client RFB version incorrect!")
            return

        ## Security handshake
        # use No authentication (length of security types is 1, and type 1 is no security)
        connection.send(pack('>bb', 1, 1))
        client_sec_type = connection.recv(1)
        if client_sec_type != pack('>b', 1):
            print(f"Client sec type incorrect! {client_sec_type}")
            return
        connection.send(pack('>I', 0)) # tell client security result is good
        
        ## Handle client init
        client_share_flag = connection.recv(1)
        if client_share_flag != pack('>b', 1):
            print("Client share flag incorrect!")
            return
        
        ## Handle server init
        # the frame buffer width + height
        framebuffer_width = pack('>H', 1000)
        framebuffer_height = pack('>H', 1000)
        
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
        
        connection.send(framebuffer_width + framebuffer_height + pixel_format_bytes + name_len + name)
    
    def handle_client(self, connection: socket, address):
        print(f"Connected by {address}")
        try:
            self.handshake(connection)
            while True:
                self.framebufferupdate(connection)
                connection.recv(2)
                break
        finally:
            connection.close()

def run_tcp_server():
    server = MockTCPServer()
    server.run()

def test():
    # Run TCP server 
    tcp_server_process = Process(target=run_tcp_server)
    tcp_server_process.start()

    # Run Websockify proxy 
    proxy_process = Process(target=run_websockify_proxy)
    proxy_process.start()

    # wait a second for both to start
    sleep(1)

    # test
    c = WSVNCClient('ws://0.0.0.0:5910')
    sleep(3)
    
    # the image here will be a 1000x1000 square with 100x100 squares running along the top_left -> bottom_right diagonal
    # being the visible pixels, with the remaining image being empty.
    # we will test here that this is true.
    img = c.get_screen()
    
    # verifies that the pixels along the diagonal are not empty
    for i in range(0, 1000, 100):
        for x in range(i, i + 100):
            for y in range(i, i + 100):
                pixel = img.getpixel((x, y))
                assert pixel != (0, 0, 0, 0), f"Expected non-empty pixel at ({x}, {y}), but found {pixel}"
    
    # verifies remaining pixels are empty
    for x in range(1000):
        for y in range(1000):
            if not (x // 100 == y // 100):  # Exclude diagonal squares
                pixel = img.getpixel((x, y))
                assert pixel == (0, 0, 0, 0), f"Expected empty pixel at ({x}, {y}), but found {pixel}"
    
    #img.save('test-websockify-framebuffer.png')
    
    # Clean up
    sleep(1)
    c.close()
    tcp_server_process.terminate()
    proxy_process.terminate()
