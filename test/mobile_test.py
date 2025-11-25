import asyncio
import websockets

async def hello():
    async with websockets.connect("ws://localhost:8000/ws/mobile/18") as websocket:
        message = await websocket.recv()
        print(message)

if __name__ == "__main__":
    asyncio.run(hello())