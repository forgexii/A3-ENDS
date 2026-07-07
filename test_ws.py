import asyncio
import websockets
import json

async def test_ws():
    print("Connecting to ws://127.0.0.1:8000/api/ws/hitl")
    try:
        async with websockets.connect("ws://127.0.0.1:8000/api/ws/hitl") as websocket:
            print("Connected! Waiting for HITL messages...")
            while True:
                message = await websocket.recv()
                data = json.loads(message)
                print(f"RECEIVED: {data}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_ws())
