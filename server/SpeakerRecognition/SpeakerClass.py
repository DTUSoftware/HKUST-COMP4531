from typing import Optional
from pyannote.audio import Model
from pyannote.core import Segment
#"pyannote.audio" library seems to work for speech recognition


class Speaker:
    def __init__(self, name: str):
        self.name = name

    async def is_speaker(self, audio: str) -> bool:
        pass


class SpeakerClass:
    def __init__(self):
        self.speakers: list[Speaker] = []

    async def enroll(self, audio: str, name: str) -> Speaker:
        pass

    async def recognize(self, audio: str) -> Optional[Speaker]:
        pass
