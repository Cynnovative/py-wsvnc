import asyncio
from struct import pack

from websockets import WebSocketServerProtocol

from tests.conftest import MockVNCBaseServer
from wsvnc.vnc.vnc_client import WSVNCClient


class MockVNCServer(MockVNCBaseServer):
    def __init__(self):
        super().__init__()
    
    async def bell_message(self, websocket: WebSocketServerProtocol):
        header = pack("!B", 2)
        await websocket.send(header)
        
    async def handler(self, websocket):
        self.clients.add(websocket)
        try:
            await self.handshake(websocket)
            await self.bell_message(websocket)
        finally:
            self.clients.remove(websocket)
            
async def main():
    
    # start the server
    server = MockVNCServer()
    await asyncio.sleep(1)  
    
    # start the client
    c = WSVNCClient(ticket_url="ws://localhost:8765")
    
    await asyncio.sleep(1)
    assert c.get_bell() is not None
    assert c.get_bell().sig == 0
    
    # close server & client
    c.close()
    server.close()

def test():
    asyncio.run(main())


        
