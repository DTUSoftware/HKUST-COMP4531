import zmq
import zmq.asyncio

SERVER_IP = "localhost"
SERVER_PORT = "5555"


async def send_audio_clip_to_server(audio_clip):
    context = await zmq.asyncio.Context()
    socket = await context.socket(zmq.REQ)
    await socket.connect(f"tcp://{SERVER_IP}:{SERVER_PORT}")
    await socket.send(audio_clip)
    message = await socket.recv()
    return message
