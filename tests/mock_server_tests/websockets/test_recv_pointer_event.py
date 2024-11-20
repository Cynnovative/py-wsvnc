import asyncio
from struct import pack

from websockets import WebSocketServerProtocol

from tests.conftest import MockVNCBaseServer
from wsvnc.vnc.vnc_client import WSVNCClient


class MockVNCServer(MockVNCBaseServer):
    def __init__(self):
        super().__init__()
    
    async def recv_pointer_event(self, websocket: WebSocketServerProtocol):
        key_event_msg = await websocket.recv()
        assert key_event_msg[0] == 5
        assert key_event_msg[1] == 1
        assert key_event_msg[2:4] == pack(">H", 500)
        assert key_event_msg[4:6] == pack(">H", 500)
        
        
    async def handler(self, websocket):
        self.clients.add(websocket)
        try:
            await self.handshake(websocket)
            await self.recv_pointer_event(websocket)
        finally:
            self.clients.remove(websocket)
            
async def main():
    
    # start the server
    server = MockVNCServer()
    await asyncio.sleep(1)  
    
    # start the client
    c = WSVNCClient(ticket_url="ws://localhost:8765")
    
    c.pointer_event(500, 500, 1)
    
    # close server & client
    c.close()
    server.close()

def test():
    asyncio.run(main())


        
