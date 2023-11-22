from typing import Optional
from SpeakerClass import SpeakerClass, Speaker
import torchaudio
from speechbrain.pretrained import EncoderClassifier, SpeakerRecognition
import asyncio


class SpeechBrainSpeaker(Speaker):
    def __init__(self, name: str):
        super().__init__(name)
        self.verification = None
        self.audio_file = None
        self.embeddings = None

    def set_verification(self, verification: SpeakerRecognition):
        self.verification = verification

    def set_audio_file(self, audio_file: str):
        self.audio_file = audio_file

    def set_embeddings(self, embeddings):
        self.embeddings = embeddings

    async def is_speaker(self, audio: str) -> bool:
        """
        https://huggingface.co/speechbrain/spkrec-ecapa-voxceleb#perform-speaker-verification
        :param audio:
        :return:
        """
        score, prediction = self.verification.verify_files(self.audio_file, audio)
        print(f"Prediction for Speaker {self.name} is {prediction} ({score}) with files {self.audio_file} and {audio}")
        return prediction == 1


class SpeechBrain(SpeakerClass):
    def __init__(self):
        super().__init__()
        # Classifier for embeddings
        self.classifier = EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb")
        # Model for speaker recognition
        self.verification = SpeakerRecognition.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb",
                                                            savedir="pretrained_models/spkrec-ecapa-voxceleb")

        self.speakers: list[SpeechBrainSpeaker] = []

    async def get_embeddings(self, audio: str):
        """
        Get embeddings from audio
        https://huggingface.co/speechbrain/spkrec-ecapa-voxceleb#compute-your-speaker-embeddings
        :param audio:
        :return:
        """
        signal, fs = torchaudio.load(audio)
        embeddings = self.classifier.encode_batch(signal)
        return embeddings

    async def enroll(self, audio: str, name: str) -> Speaker:
        embeddings = await self.get_embeddings(audio)
        speaker = SpeechBrainSpeaker(name)
        speaker.set_verification(self.verification)
        speaker.set_audio_file(audio)
        speaker.set_embeddings(embeddings)
        self.speakers.append(speaker)
        return speaker

    async def recognize(self, audio: str) -> Optional[Speaker]:
        embeddings = await self.get_embeddings(audio)
        for speaker in self.speakers:
            if speaker.embeddings == embeddings:
                print(f"Speaker {speaker.name} recognized through embeddings")
                return speaker
        for speaker in self.speakers:
            if await speaker.is_speaker(audio):
                print(f"Speaker {speaker.name} recognized through verification")
                return speaker
        return None


async def main():
    pass


if __name__ == '__main__':
    asyncio.run(main())
