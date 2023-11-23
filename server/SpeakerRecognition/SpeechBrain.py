from typing import Optional
from SpeakerClass import SpeakerClass, Speaker
import torchaudio
from speechbrain.pretrained import EncoderClassifier, SpeakerRecognition
import asyncio


class SpeechBrainSpeaker(Speaker):
    def __init__(self, name: str, classifier=None, verification=None, audio_file=None, embeddings=None):
        super().__init__(name)
        self.verification = verification
        self.classifier = classifier
        self.audio_file = audio_file
        self.embeddings = embeddings

    async def is_speaker(self, audio: str, embedding=None) -> bool:
        """
        https://huggingface.co/speechbrain/spkrec-ecapa-voxceleb#perform-speaker-verification
        :param audio:
        :param embedding:
        :return:
        """
        if embedding is not None and self.embeddings is not None:
            print(f"Checking embeddings for speaker {self.name}")
            print(f"Speaker embeddings: {self.embeddings}")
            print(f"Embeddings to check: {embedding}")
            if (self.embeddings == embedding).all():
                print(f"Speaker {self.name} recognized through embeddings")
                return True

        score, prediction = self.verification.verify_files(self.audio_file, audio)
        print(f"Prediction for Speaker {self.name} is {prediction} ({score}) with files {self.audio_file} and {audio}")
        return prediction == 1


class SpeechBrain(SpeakerClass):
    def __init__(self):
        super().__init__()
        # Classifier for embeddings
        self.classifier = EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb",
                                                         savedir="pretrained_models/spkrec-ecapa-voxceleb")
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
        # The verify already uses embeddings so we can just skip this step - if we want to do it manually in the future
        # we can bring it back
        embeddings = None  # await self.get_embeddings(audio)
        speaker = SpeechBrainSpeaker(name=name, verification=self.verification, embeddings=embeddings, audio_file=audio,
                                     classifier=self.classifier)
        self.speakers.append(speaker)
        return speaker

    async def recognize(self, audio: str) -> Optional[Speaker]:
        embeddings = await self.get_embeddings(audio)
        for speaker in self.speakers:
            if await speaker.is_speaker(audio, embedding=embeddings):
                print(f"Speaker {speaker.name} recognized!")
                return speaker
        print(f"Speaker not recognized!")
        return None


async def main():
    speech_brain = SpeechBrain()
    speaker_marcus = await speech_brain.enroll("Marcus1.wav", "marcus1")
    speaker_mads = await speech_brain.enroll("Mads1.wav", "mads")
    who_is_it = await speech_brain.recognize("Mads2.wav")
    who_is_it = await speech_brain.recognize("neither.wav")


if __name__ == '__main__':
    asyncio.run(main())
