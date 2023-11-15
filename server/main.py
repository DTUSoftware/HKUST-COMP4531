import asyncio
import aiomsg

SERVER_PORT = "5555"


async def server() -> None:
    context = await aiomsg.Context()
    socket = await context.socket(aiomsg.PULL)
    await socket.bind(f"tcp://*:{SERVER_PORT}")

    while True:
        audio_clip = await socket.recv()

        # Do something with the audio clip


if __name__ == '__main__':
    asyncio.run(server())
