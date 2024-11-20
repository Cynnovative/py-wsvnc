import asyncio

from tests.conftest import MockVNCBaseServer
from wsvnc.vnc.vnc_client import WSVNCClient


class MockVNCServer(MockVNCBaseServer):
    def __init__(self):
        super().__init__()

    async def handler(self, websocket):
        self.clients.add(websocket)
        try:
            await self.handshake(websocket)
        finally:
            self.clients.remove(websocket)
            
    
        

async def main():
    # start the server
    server = MockVNCServer()
    await asyncio.sleep(1)  
    
    # start the client as a context manager
    with WSVNCClient(ticket_url="ws://localhost:8765") as c:
        assert c._handshake_done.is_set()
        
    server.close()

def test():
    asyncio.run(main())


        
