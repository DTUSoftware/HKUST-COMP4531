import asyncio
import aiofiles
import os
import uuid
import zmq
import zmq.asyncio
import wave

# Import models
from SpeechRecognition.SpeechBrain import SpeechBrain as Speech
from SpeakerRecognition.SpeechBrain import SpeechBrain as Speaker

# Initialize models
speech: Speech
speaker: Speaker

SERVER_PORT = "5555"
SECONDS_PER_AUDIO_SEGMENT = 5


async def server() -> None:
    context = zmq.asyncio.Context()
    socket = context.socket(zmq.PULL)
    socket.bind(f"tcp://*:{SERVER_PORT}")

    print(f"Server listening on port {SERVER_PORT}")

    while True:
        message = await socket.recv()
        print(f"Received message of length {len(message)}")

        if b':' not in message or (message.split(b':')[0] != b'meeting' and message.split(b':')[0] != b'enroll'):
            print(f"Invalid message {message}")
            continue

        audio_clip = b':'.join(message.split(b':')[2:])
        print(f"Received audio clip of length {len(audio_clip)}")

        audio_file = await save_audio(audio_clip)
        print(f"Saved audio clip to {audio_file}")

        processing_type = message.split(b':')[0].decode("utf-8")
        print(f"Processing audio using type = {processing_type}...")
        data = message.split(b':')[1].split(b':')[0].decode("utf-8")

        if processing_type == "enroll":
            print(f"Enrolling speaker {data}...")
            speaker_person = await enroll_speaker(audio_file, data)
            if not speaker_person:
                print(f"Failed to enroll speaker {data}!")
            else:
                print(f"Successfully enrolled speaker {speaker_person.name}!")
        else:
            print(f"Processing audio...")
            result = await process_audio(audio_file)
            print(f"Result: {result}")

            # Save the result to a file
            if not os.path.exists("results"):
                os.mkdir("results")

            async with aiofiles.open(f"results/{str(uuid.uuid4())}.txt", "w") as f:
                await f.write(result)


async def save_audio(audio_clip, is_segment=False, audio_id=str(uuid.uuid4())) -> str:
    # If audio directory does not exist, create it
    if not os.path.exists("audio_cache"):
        os.mkdir("audio_cache")
    if is_segment:
        if not os.path.exists("audio_cache/segments"):
            os.mkdir("audio_cache/segments")

    # Save the audio clip to a file
    filename = f"audio_cache{'/segments' if is_segment else ''}/{audio_id}.wav"
    async with aiofiles.open(filename, "wb") as f:
        await f.write(audio_clip)

        return filename


async def enroll_speaker(audio_file: str, speaker_name: str):
    global speaker
    if not speaker:
        speaker = Speaker()
    speaker_person = await speaker.enroll(audio_file, speaker_name)
    return speaker_person


# comment this out when testing file sending!!
async def process_audio(audio_file: str):
    file_id = audio_file.split("/")[1].split(".")[0]

    # Load the audio file to get info from audio file
    with wave.open(audio_file, "rb") as wave_file:
        frame_rate = wave_file.getframerate()
        num_frames = wave_file.getnframes()
        num_channels = wave_file.getnchannels()
        sample_width = wave_file.getsampwidth()

    # Get duration of audio file in seconds
    audio_duration = num_frames / frame_rate

    print(f"Audio file information:\n"
          f"- Frame rate: {frame_rate}\n"
          f"- Number of frames: {num_frames}\n"
          f"- Number of channels: {num_channels}\n"
          f"- Sample width: {sample_width}\n"
          f"- Duration: {audio_duration} seconds\n")

    # Split the audio file into segments
    segments = []
    async with aiofiles.open(audio_file, "rb") as f:
        for i in range(0, num_frames, frame_rate * SECONDS_PER_AUDIO_SEGMENT):
            segment = await f.read(frame_rate * SECONDS_PER_AUDIO_SEGMENT)
            # Save each segment to a file
            segment_file = await save_audio(segment, is_segment=True, audio_id=f"{file_id}-{i}")

            # Add the segment to the list of segments
            segments.append({
                "file": segment_file,
                "start": i,
                "end": i + frame_rate * SECONDS_PER_AUDIO_SEGMENT
            })

    # First we want to recognize the speaker in each segment
    global speaker
    if not speaker:
        speaker = Speaker()

    for i in range(len(segments)):
        segment = segments[i]
        segments[i]["speaker"] = await speaker.recognize(segment["file"])

        # If this speaker is the same as last segment, then we can merge the segments
        if i > 0 and segments[i]["speaker"] == segments[i - 1]["speaker"]:
            print(f"Speaker in segment {i} is the same as segment {i - 1}! Merging segments...")
            segments[i - 1]["end"] = segments[i]["end"]

            # Load both audio files into memory and merge them into one file
            async with aiofiles.open(segments[i - 1]["file"], "rb") as f1, aiofiles.open(segments[i]["file"], "rb") as f2:
                audio1 = await f1.read()
                audio2 = await f2.read()
                merged_audio = audio1 + audio2
                merged_audio_file = await save_audio(merged_audio, is_segment=True, audio_id=f"{file_id}-{i - 1}")
                segments[i - 1]["file"] = merged_audio_file

            segments.pop(i)

            # Since we merged the segments, we need to go back one index
            i -= 1

    # Now, time to parse the audio file segments to get the text
    print("Finished processing audio file segments. Getting text from each segment...")
    global speech
    if not speech:
        speech = Speech("wav2vec2")

    for segment in segments:
        segment["text"] = await speech.get_text(segment["file"])
        print(f"Segment {segment['file']} text: {segment['text']}")

    # Now we can merge the text from each segment into one text
    text = ""
    for segment in segments:
        # If the text is empty, then we can skip the segment
        if not segment["text"]:
            continue

        # [Speaker] Text dialogue goes here...!
        text += f"[{segment['speaker'].name if segment['speaker'] else 'Unknown Speaker'}] {segment['text']}\n"

    return text

if __name__ == '__main__':
    # RuntimeWarning: Proactor event loop does not implement add_reader family of methods required for zmq.
    # Registering an additional selector thread for add_reader support via tornado.
    # Use `asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())` to avoid this warning.
    if os.name == "nt":
        from asyncio import WindowsSelectorEventLoopPolicy
        asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())
    asyncio.run(server())
