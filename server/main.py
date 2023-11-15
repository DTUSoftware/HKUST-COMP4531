import zmq

SERVER_PORT = "5555"

if __name__ == '__main__':
    context = zmq.Context()
    socket = context.socket(zmq.PULL)
    socket.bind(f"tcp://*:{SERVER_PORT}")

    audio_clip = socket.recv()

    # Do something with the audio clip
