import zmq
import zmq.asyncio

SERVER_IP = "localhost"
SERVER_PORT = "5555"


async def send_audio_clip_to_server(audio_clip, processing_type="meeting", speaker=None):
    if processing_type != "meeting" and processing_type != "enroll":
        print(f"Invalid type {processing_type}")
        return False

    if processing_type == "enroll" and not speaker:
        print(f"No speaker provided for enrollment!")
        return False

    try:
        context = zmq.asyncio.Context()
        socket = context.socket(zmq.PUSH)
        print(f"Connecting to server at {SERVER_IP}:{SERVER_PORT}")
        with socket.connect(f"tcp://{SERVER_IP}:{SERVER_PORT}") as conn:
            print(f"Connected to server at {SERVER_IP}:{SERVER_PORT}")
            print(f"Sending audio clip of length {len(audio_clip)}")
            await conn.send(processing_type.encode("utf-8")+b':'+(speaker.encode("utf-8") if speaker else b'')+b':'+audio_clip)
            return True
    except Exception as e:
        print(f"An error occurred while sending the audio clip: {e}")
    return False
