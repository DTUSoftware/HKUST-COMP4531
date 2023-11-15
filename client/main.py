import asyncio
import services

PATH_TO_AUDIO_CLIP = "path/to/audio/clip"


def read_audio_file(path: str) -> bytes:
    with open(path, "rb") as f:
        audio_clip = f.read()
    return audio_clip


async def main() -> None:
    audio_clip = read_audio_file(PATH_TO_AUDIO_CLIP)
    response = await services.send_message_queue.send_audio_clip_to_server(audio_clip)


if __name__ == '__main__':
    asyncio.run(main())
