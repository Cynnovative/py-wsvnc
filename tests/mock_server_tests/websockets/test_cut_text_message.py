import asyncio
from struct import pack

from websockets import WebSocketServerProtocol

from tests.conftest import MockVNCBaseServer
from wsvnc.vnc.vnc_client import WSVNCClient


class MockVNCServer(MockVNCBaseServer):
    def __init__(self):
        super().__init__()
    
    async def cut_text_message(self, websocket: WebSocketServerProtocol):
        header = pack("!BxxxI", 3, 12)
        text = pack(">12s", b"Hello World!")
        msg = header + text
        await websocket.send(msg)
        
    async def handler(self, websocket):
        self.clients.add(websocket)
        try:
            await self.handshake(websocket)
            await self.cut_text_message(websocket)
        finally:
            self.clients.remove(websocket)
            
async def main():
    
    # start the server
    server = MockVNCServer()
    await asyncio.sleep(1)  
    
    # start the client
    c = WSVNCClient(ticket_url="ws://localhost:8765")
    
    if c.get_clipboard() != b"Hello World!":
        assert "TEST FAILED!!!!"
    
    # close server & client
    c.close()
    server.close()

def test():
    asyncio.run(main())


        
