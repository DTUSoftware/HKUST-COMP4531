import asyncio
import services
import logging

PATH_TO_AUDIO_CLIP = "path/to/audio/clip"
#Introducing logging to detect exceptions 
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
        response = await services.send_message_queue.send_audio_clip_to_server(audio_clip)
        logging.info(f"Server responded with: {response}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

if __name__ == '__main__':
    asyncio.run(main())
