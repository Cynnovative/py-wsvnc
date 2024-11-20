import asyncio
from struct import pack

from websockets import WebSocketServerProtocol

from tests.conftest import MockVNCBaseServer
from wsvnc.vnc.vnc_client import WSVNCClient


class MockVNCServer(MockVNCBaseServer):
    def __init__(self):
        super().__init__()
    
    async def recv_key_event_down(self, websocket: WebSocketServerProtocol):
        key_event_msg = await websocket.recv()
        assert key_event_msg[0] == 4
        assert key_event_msg[1] == 1
        assert key_event_msg[4:8] == pack(">I", 500)
    
    async def recv_key_event_up(self, websocket: WebSocketServerProtocol):
        """Difference here is that we check to see if the down flag is false."""
        key_event_msg = await websocket.recv()
        assert key_event_msg[0] == 4
        assert key_event_msg[1] == 0
        assert key_event_msg[4:8] == pack(">I", 500)
        
        
    async def handler(self, websocket):
        self.clients.add(websocket)
        try:
            await self.handshake(websocket)
            await self.recv_key_event_down(websocket)
            await self.recv_key_event_up(websocket)
        finally:
            self.clients.remove(websocket)
            
async def main():
    
    # start the server
    server = MockVNCServer()
    await asyncio.sleep(1)  
    
    # start the client
    c = WSVNCClient(ticket_url="ws://localhost:8765")
    
    c.key_event(500, True)
    c.key_event(500, False)
    
    # close server & client
    c.close()
    server.close()

def test():
    asyncio.run(main())


        
