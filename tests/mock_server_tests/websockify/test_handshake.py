import logging
from multiprocessing import Process
from socket import socket
from struct import pack
from time import sleep

from tests.conftest import MockTCPBaseServer, run_websockify_proxy
from wsvnc.pixel_format import PixelFormat
from wsvnc.vnc.vnc_client import WSVNCClient

logging.basicConfig(level=logging.DEBUG)

class MockTCPServer(MockTCPBaseServer):
    
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
        
        connection.send(framebuffer_width + framebuffer_height + pixel_format_bytes + name_len + name)
    
    def handle_client(self, connection: socket, address):
        print(f"Connected by {address}")
        try:
            self.handshake(connection)
            while True:
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
    sleep(1)
    assert c._rfb_client is not None
    
    # Clean up
    c.close()
    tcp_server_process.terminate()
    proxy_process.terminate()
