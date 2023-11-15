import asyncio
import aiomsg
import aiofiles
import os
import uuid
import zmq
import zmq.asyncio

# Comment this out when testing file sending!!
# # Import models
# from SpeechRecognition.SpeechBrain import SpeechBrain as Speech
# from SpeakerRecognition.SpeechBrain import SpeechBrain as Speaker
#
# # Initialize models
# speech: Speech
# speaker: Speaker

SERVER_PORT = "5555"


async def server() -> None:
    context = zmq.asyncio.Context()
    socket = context.socket(zmq.PULL)
    socket.bind(f"tcp://*:{SERVER_PORT}")

    while True:
        audio_clip = await socket.recv()

        audio_file = await save_audio(audio_clip)

        # Send status message back to client
        await socket.send(f"Processing audio as {audio_file}")

        # Comment this out when testing file sending!!
        # # Process audio
        # text, speaker = await process_audio(audio_file)
        # print(f"Text: {text}")
        # print(f"Speaker: {speaker}")
        #
        # # Send text back to client
        # await socket.send(text)


async def save_audio(audio_clip) -> str:
    # If audio directory does not exist, create it
    if not os.path.exists("audio"):
        os.mkdir("audio")

    # Give the audio clip a unique name
    audio_id = uuid.uuid4()

    # Save the audio clip to a file
    filename = f"audio/{audio_id}.wav"
    async with aiofiles.open(filename, "wb") as f:
        await f.write(audio_clip)

        return filename


# comment this out when testing file sending!!
# async def process_audio(audio_file: str):
#     # First we process the audio to get the text
#     global speech
#     if not speech:
#         speech = Speech("wav2vec2")
#     text = await speech.get_text(audio_file)
#
#     # Then we process the audio to get the speaker
#     # TODO: fix this lol
#     global speaker
#     if not speaker:
#         speaker = Speaker()
#     speaker_person = await speaker.enroll(audio_file, "test")
#
#     return text, speaker_person

if __name__ == '__main__':
    asyncio.run(server())
