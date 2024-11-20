import asyncio

import pytest

from wsvnc.vnc.vnc_client import WSVNCClient


async def main():
    
    # start the client will not connect to anything
    with pytest.raises(Exception):
        WSVNCClient(ticket_url="ws://localhost:8765")
    

def test():
    asyncio.run(main())


        
