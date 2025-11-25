import asyncio
import websockets
import json

started = False

async def receiver(websocket):
    global started
    while True:
        try:
            message = await websocket.recv()
            print("Received:", message)

            event = json.loads(message).get("event")

            if event == "session_start":
                started = True
                print("== Session Started ==")

            elif event == "session_stop":
                started = False
                print("== Session Stopped ==")

        except websockets.ConnectionClosed:
            print("Connection closed by server.")
            break


async def sender(websocket):
    global started
    data_count = 0

    while True:
        if started:
            if data_count < 15:
                event_name = "preparation"
            else:
                event_name = "steaming"

            payload = {
                "event": event_name,
                "humidity": 0.0,
                "water_temperature": 0.0,
                "air_temperature": 0.0,
                "water_sufficient": True
            }

            await websocket.send(json.dumps(payload))
            print("Sent:", payload)

            data_count += 1

        await asyncio.sleep(2)  # keep connection alive, but sending only when started


async def main():
    async with websockets.connect("ws://localhost:8000/ws/esps/string") as websocket:
        # run receiver + sender together
        await asyncio.gather(
            receiver(websocket),
            sender(websocket)
        )

if __name__ == "__main__":
    asyncio.run(main())
