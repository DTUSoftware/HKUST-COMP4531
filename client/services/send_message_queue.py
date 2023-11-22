import zmq
import zmq.asyncio

SERVER_IP = "localhost"
SERVER_PORT = "5555"


async def send_audio_clip_to_server(audio_clip):
    try:
        context = zmq.asyncio.Context()
        socket = context.socket(zmq.PUSH)
        print(f"Connecting to server at {SERVER_IP}:{SERVER_PORT}")
        with socket.connect(f"tcp://{SERVER_IP}:{SERVER_PORT}") as conn:
            print(f"Connected to server at {SERVER_IP}:{SERVER_PORT}")
            print(f"Sending audio clip of length {len(audio_clip)}")
            await conn.send(audio_clip)
            return True
    except Exception as e:
        print(f"An error occurred while sending the audio clip: {e}")
    return False
