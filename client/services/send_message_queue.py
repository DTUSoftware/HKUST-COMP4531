import zmq

SERVER_IP = "localhost"
SERVER_PORT = "5555"


def send_audio_clip_to_server(audio_clip):
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(f"tcp://{SERVER_IP}:{SERVER_PORT}")
    socket.send(audio_clip)
    message = socket.recv()
    return message
