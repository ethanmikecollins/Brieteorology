import asyncio
import time
import board

from adafruit_seesaw import seesaw, digitalio, rotaryio
from websockets.asyncio.server import serve


i2c = board.I2C()

seesaw_board = seesaw.Seesaw(
    i2c,
    addr=0x36
)

seesaw_board.pin_mode(
    24,
    seesaw_board.INPUT_PULLUP
)

button = digitalio.DigitalIO(
    seesaw_board,
    24
)

encoder = rotaryio.IncrementalEncoder(
    seesaw_board
)

clients = set()

async def send_command(command):
    disconnected = []

    for client in clients:
        try:
            await client.send(command)
        except Exception:
            disconnected.append(client)

    for client in disconnected:
        clients.discard(client)


async def browser_connection(websocket):
    clients.add(websocket)

    try:
        async for _ in websocket:
            pass
    finally:
        clients.discard(websocket)


async def monitor_encoder():
    last_position = -encoder.position
    last_button = button.value

    while True:
        current_position = -encoder.position

        difference = (
            current_position
            - last_position
        )

        if difference > 0:
            for n in range(difference):
                await send_command("forward")
        elif difference < 0:
            for n in range(-difference):
                await send_command("backward")

        last_position = current_position
        current_button = button.value

        if (last_button and not current_button):
            await send_command("toggle")

        last_button = current_button

        await asyncio.sleep(0.005)


async def main():

    async with serve(
        browser_connection,
        "127.0.0.1",
        8765
    ):
        await monitor_encoder()


asyncio.run(main())