import asyncio
import services.send_message_queue
import logging
import os

PATH_TO_AUDIO_CLIP = "test-recordings/recording-scoopdewoop-231122.wav"
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
    try:
        audio_clip = read_audio_file(PATH_TO_AUDIO_CLIP)
        success = await services.send_message_queue.send_audio_clip_to_server(audio_clip)
        logging.info(f"Success: {success}")
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
