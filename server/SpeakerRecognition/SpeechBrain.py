from SpeakerClass import SpeakerClass


class SpeechBrain(SpeakerClass):
    def __init__(self):
        super().__init__()

    async def enroll(self, audio):
        pass

    async def recognize(self, audio):
        pass
