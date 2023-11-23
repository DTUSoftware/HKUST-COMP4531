import asyncio
import services.send_message_queue
import logging
import os
import sounddevice as sd
from scipy.io import wavfile

PATH_TO_AUDIO_CLIP = "test-recordings/testmeeting.wav"
# Introducing logging to detect exceptions
logging.basicConfig(level=logging.INFO)


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
                audio_clip = read_audio_file(PATH_TO_AUDIO_CLIP)
                success = await services.send_message_queue.send_audio_clip_to_server(audio_clip, processing_type="enroll", speaker=speaker_name)
                logging.info(f"Success: {success}")
            elif choice == "2":
                audio_clip = read_audio_file(PATH_TO_AUDIO_CLIP)
                success = await services.send_message_queue.send_audio_clip_to_server(audio_clip)
                logging.info(f"Success: {success}")
            elif choice == "3":
                print("Recording audio until input is given...")
                fs = 44100
                # we want to record until the user presses enter
                recording = sd.rec(int(10 * fs), samplerate=fs, channels=2)


                audio_clip = read_audio_file(PATH_TO_AUDIO_CLIP)
                success = await services.send_message_queue.send_audio_clip_to_server(audio_clip)
                logging.info(f"Success: {success}")
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
