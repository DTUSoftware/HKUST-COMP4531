import asyncio
import math
from typing import Optional
import aiofiles
import os
import uuid
import zmq
import zmq.asyncio
import wave
from pydub import AudioSegment

# Import models
from SpeechRecognition.SpeechBrain import SpeechBrain as Speech
from SpeakerRecognition.SpeechBrain import SpeechBrain as Speaker

# Initialize models
speech: Optional[Speech] = None
speaker: Optional[Speaker] = None

SERVER_PORT = "5555"
SECONDS_PER_AUDIO_SEGMENT = 1


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


async def save_audio(audio_clip, is_segment=False, audio_id=None) -> str:
    # If audio directory does not exist, create it
    if not os.path.exists("audio_cache"):
        os.mkdir("audio_cache")
    if is_segment:
        if not os.path.exists("audio_cache/segments"):
            os.mkdir("audio_cache/segments")

    if not audio_id:
        audio_id = str(uuid.uuid4())

    # Save the audio clip to a file
    filename = f"audio_cache{'/segments' if is_segment else ''}/{audio_id}.wav"
    if isinstance(audio_clip, bytes):
        async with aiofiles.open(filename, "wb") as f:
            await f.write(audio_clip)

            return filename
    elif isinstance(audio_clip, AudioSegment):
        audio_clip.export(filename, format="wav")
        return filename
    else:
        raise TypeError(f"Invalid audio clip type {type(audio_clip)}, expected Bytes or AudioSegment")


async def enroll_speaker(audio_file: str, speaker_name: str):
    global speaker
    if not speaker:
        speaker = Speaker()
        # Load the speakers from file, so we don't accidentally delete all speakers if the first thing we do is enroll
        await speaker.load()
    speaker_person = await speaker.enroll(audio_file, speaker_name)
    if not speaker_person:
        print(f"Failed to enroll speaker {speaker_name}!")
    else:
        print(f"Successfully enrolled speaker {speaker_person.name}!")
        print("Saving speakers...")
        await speaker.save()
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

    audio_segment = AudioSegment.from_wav(audio_file)

    # Split the audio file into segments
    segments = []
    async with aiofiles.open(audio_file, "rb") as f:
        for i in range(0, math.floor(audio_duration*1000), math.floor(SECONDS_PER_AUDIO_SEGMENT*1000)):
            segment = audio_segment[i:i+SECONDS_PER_AUDIO_SEGMENT*1000]
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
        # Load the speakers from file
        await speaker.load()

    shift = 0
    for i in range(len(segments)):
        current_index = i + shift

        segment = segments[current_index]
        segments[current_index]["speaker"] = await speaker.recognize(segment["file"])

        # If this speaker is the same as last segment, then we can merge the segments
        print(f"Speaker in segment {current_index}: {segments[current_index]['speaker']}")
        if current_index > 0: print(f"Speaker in segment {current_index-1}: {segments[current_index-1]['speaker']}")
        if current_index > 0 and segments[current_index]["speaker"] == segments[current_index - 1]["speaker"]:
            print(f"Speaker in segment {current_index} is the same as segment {current_index - 1}! Merging segments...")
            segments[current_index - 1]["end"] = segments[current_index]["end"]

            # Load both audio files into memory and merge them into one file
            # async with aiofiles.open(segments[i - 1]["file"], "rb") as f1, aiofiles.open(segments[i]["file"], "rb") as f2:
            #     audio1 = await f1.read()
            #     audio2 = await f2.read()
            #
            #     merged_audio = audio1 + audio2
            #     merged_audio_file = await save_audio(merged_audio, is_segment=True, audio_id=f"{file_id}-{i - 1}")
            #     segments[i - 1]["file"] = merged_audio_file

            # use pydub to merge the audio files
            audio1_segment = AudioSegment.from_wav(segments[current_index - 1]["file"])
            audio2_segment = AudioSegment.from_wav(segments[current_index]["file"])

            merged_audio = audio1_segment + audio2_segment
            merged_audio_file = await save_audio(merged_audio, is_segment=True, audio_id=f"{file_id}-{current_index - 1}")
            segments[current_index - 1]["file"] = merged_audio_file

            segments.pop(current_index)

            # Since we merged the segments, we need to go back one index
            shift -= 1

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
