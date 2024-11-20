import asyncio

from websockets import WebSocketServerProtocol

from tests.conftest import MockVNCBaseServer
from wsvnc.vnc.vnc_client import WSVNCClient


class MockVNCServer(MockVNCBaseServer):
    def __init__(self, text):
        super().__init__()
        self.text = text
    
    async def recv_cut_text(self, websocket: WebSocketServerProtocol):
        cut_text_msg = await websocket.recv()

        # first 8 bytes are the header
        text = cut_text_msg[8:].decode()
        assert text == self.text
        
        
    async def handler(self, websocket):
        self.clients.add(websocket)
        try:
            await self.handshake(websocket)
            await self.recv_cut_text(websocket)
        finally:
            self.clients.remove(websocket)
            
async def main():
    
    # start the server
    text = "Hello World!"
    server = MockVNCServer(text)
    await asyncio.sleep(1)  
    
    # start the client
    c = WSVNCClient(ticket_url="ws://localhost:8765")
    
    c.cut_text(text)
    
    # close server & client
    c.close()
    server.close()

def test():
    asyncio.run(main())


        
