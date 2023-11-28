import asyncio
import services.send_message_queue
import logging
import os
import sounddevice as sd
import threading
import numpy as np
from scipy.io import wavfile
import datetime

# Introducing logging to detect exceptions
logging.basicConfig(level=logging.INFO)

# Set default sound devices
sd.default.dtype = "int16"
# First for raspberry pi
if os.name == "posix":
    pass
    #sd.default.device = "ac108"
elif os.name == "nt":
    pass
    # sd.default.device = 0
elif os.name == "mac":
    pass
    # sd.default.device = "Built-in Microphone"

is_recording = False


def read_audio_file(path: str) -> bytes:
    try:
        with open(path, "rb") as f:
            audio_clip = f.read()
        return audio_clip
    except FileNotFoundError:
        logging.error(f"The audio file at {path} was not found.")
        raise
    except Exception as e:
        logging.error(f"An error occurred while reading the audio file: {e}")
        raise


# The system is trained with recordings sampled at 16kHz (single channel)
def record_audio(filename, fs=16000, channels=1):
    global is_recording
    is_recording = True
    with sd.InputStream(samplerate=fs, channels=channels) as stream:
        audio_data = []
        while is_recording:
            data, overflowed = stream.read(fs)
            audio_data.append(data)
        wavfile.write(filename, fs, np.concatenate(audio_data, axis=0))


async def stop_recording():
    global is_recording

    # Wait for recording to start
    print("Waiting for recording to start...")
    i = 0
    while not is_recording:
        await asyncio.sleep(1)
        i += 1
        if i > 10:
            print("Recording did not start, exiting...")
            exit(1)

    input("Press Enter to stop recording...")
    is_recording = False


async def main() -> None:
    while True:
        print("What do you want to do?")
        print("1. Enroll a speaker")
        print("2. Process an audio clip")
        print("3. Record a new audio clip")
        print("4. Exit")

        choice = input("Enter your choice: ")
        try:
            if choice == "1":
                speaker_name = input("Enter the name of the speaker: ")

                # Check if recordings directory exists, if not, create it
                if not os.path.exists("recordings"):
                    os.mkdir("recordings")

                # Make filename from current time
                filename = f"recordings/enroll-{speaker_name}-{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.wav"

                recording_thread = threading.Thread(target=record_audio, args=(filename,))
                input("Press Enter to start recording...")
                recording_thread.start()
                await stop_recording()
                recording_thread.join()
                print("Recording stopped.")

                submit = input("Do you want to submit the recording? (Y/n): ")
                if not submit.lower().startswith("n"):
                    audio_clip = read_audio_file(filename)
                    success = await services.send_message_queue.send_audio_clip_to_server(audio_clip,
                                                                                          processing_type="enroll",
                                                                                          speaker=speaker_name)
                    print(f"Success: {success}")
                else:
                    print("Recording discarded.")
            elif choice == "2":
                audio_file = input("Enter path to audio file (wav): ").strip()
                audio_clip = read_audio_file(audio_file)
                success = await services.send_message_queue.send_audio_clip_to_server(audio_clip)
                print(f"Success: {success}")
            elif choice == "3":
                # Check if recordings directory exists, if not, create it
                if not os.path.exists("recordings"):
                    os.mkdir("recordings")

                # Make filename from current time
                filename = f"recordings/meeting-{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.wav"

                recording_thread = threading.Thread(target=record_audio, args=(filename,))
                input("Press Enter to start recording...")
                recording_thread.start()
                await stop_recording()
                recording_thread.join()
                print("Recording stopped.")

                submit = input("Do you want to submit the recording? (Y/n): ")
                if not submit.lower().startswith("n"):
                    audio_clip = read_audio_file(filename)
                    success = await services.send_message_queue.send_audio_clip_to_server(audio_clip,
                                                                                          processing_type="meeting")
                    print(f"Success: {success}")
                else:
                    print("Recording discarded.")
            elif choice == "4":
                print("Exiting...")
                exit(0)
        except Exception as e:
            logging.error(f"An error occurred: {e}")


if __name__ == '__main__':
    # RuntimeWarning: Proactor event loop does not implement add_reader family of methods required for zmq.
    # Registering an additional selector thread for add_reader support via tornado.
    # Use `asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())` to avoid this warning.
    if os.name == "nt":
        from asyncio import WindowsSelectorEventLoopPolicy

        asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
