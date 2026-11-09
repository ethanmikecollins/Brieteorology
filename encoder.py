import asyncio
import time
import board

from adafruit_seesaw import seesaw, digitalio, rotaryio
from websockets.asyncio.server import serve


# --------------------------------------------------
# Encoder setup
# --------------------------------------------------

i2c = board.I2C()

seesaw_board = seesaw.Seesaw(
    i2c,
    addr=0x36
)

# Encoder push button
seesaw_board.pin_mode(
    24,
    seesaw_board.INPUT_PULLUP
)

button = digitalio.DigitalIO(
    seesaw_board,
    24
)

# Rotary encoder
encoder = rotaryio.IncrementalEncoder(
    seesaw_board
)


# --------------------------------------------------
# Connected browser clients
# --------------------------------------------------

clients = set()


async def send_command(command):
    print(f"Sending: {command}")

    disconnected = []

    for client in clients:
        try:
            await client.send(command)
        except Exception:
            disconnected.append(client)

    for client in disconnected:
        clients.discard(client)


# --------------------------------------------------
# WebSocket connection
# --------------------------------------------------

async def browser_connection(websocket):
    clients.add(websocket)

    print("Browser connected to encoder")

    try:
        async for _ in websocket:
            pass
    finally:
        clients.discard(websocket)

        print("Browser disconnected from encoder")


# --------------------------------------------------
# Read encoder
# --------------------------------------------------

async def monitor_encoder():

    # Product #5880 reports rotation backwards,
    # so negate the encoder position.
    last_position = -encoder.position

    # Button uses INPUT_PULLUP:
    # True  = released
    # False = pressed
    last_button = button.value

    last_press_time = 0

    while True:

        # ------------------------------------------
        # Rotation
        # ------------------------------------------

        current_position = -encoder.position

        difference = (
            current_position
            - last_position
        )

        if difference > 0:

            for _ in range(difference):
                await send_command("advancePrediction")

        elif difference < 0:

            for _ in range(-difference):
                await send_command("reversePrediction")

        last_position = current_position


        # ------------------------------------------
        # Push button
        # ------------------------------------------

        current_button = button.value

        # Detect transition:
        # released -> pressed
        if (
            last_button
            and not current_button
        ):

            now = time.monotonic()

            # Simple debounce
            if now - last_press_time > 0.2:

                await send_command(
                    "togglePrediction"
                )

                last_press_time = now

        last_button = current_button


        # Poll at 200 Hz
        await asyncio.sleep(0.005)


# --------------------------------------------------
# Main
# --------------------------------------------------

async def main():

    async with serve(
        browser_connection,
        "127.0.0.1",
        8765
    ):

        print(
            "Encoder server running "
            "on port 8765"
        )

        await monitor_encoder()


asyncio.run(main())