import asyncio
from struct import pack

from websockets import WebSocketServerProtocol

from tests.conftest import MockVNCBaseServer
from wsvnc.vnc.vnc_client import WSVNCClient


class MockVNCServer(MockVNCBaseServer):
    def __init__(self):
        super().__init__()
        
    async def recv_frame_buffer_update_request(self, websocket: WebSocketServerProtocol):
        fbur = await websocket.recv()
        assert fbur[0] == 3
        assert  fbur[1] == 0
        assert fbur[2:4] == pack(">H", 0)
        assert fbur[4:6] == pack(">H", 0)
        
           
    async def handler(self, websocket):
        self.clients.add(websocket)
        try:
            await self.handshake(websocket)
            await self.recv_frame_buffer_update_request(websocket)
        finally:
            self.clients.remove(websocket)
            
    
async def main():
    # start the server
    server = MockVNCServer()
    await asyncio.sleep(1)  
    
    # start the client (using the VNCSecurity scheme)
    c = WSVNCClient(ticket_url="ws://localhost:8765")
    
    # save the image from the client to a file for this test
    # should be some random pixels
    await asyncio.sleep(1) # wait for image to process
    
    # update the screen
    c.update_screen()
    
    # close server & client
    c.close()
    server.close()

def test():
    asyncio.run(main())


        
