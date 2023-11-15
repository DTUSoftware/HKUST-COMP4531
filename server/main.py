import asyncio
import zmq
import zmq.asyncio

SERVER_PORT = "5555"


async def server() -> None:
    context = await zmq.asyncio.Context()
    socket = await context.socket(zmq.PULL)
    await socket.bind(f"tcp://*:{SERVER_PORT}")

    while True:
        audio_clip = await socket.recv()

        # Do something with the audio clip


if __name__ == '__main__':
    asyncio.run(server())
