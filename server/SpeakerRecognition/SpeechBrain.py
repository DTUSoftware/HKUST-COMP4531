from typing import Optional
from SpeakerClass import SpeakerClass, Speaker
import torchaudio
from speechbrain.pretrained import EncoderClassifier, SpeakerRecognition


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
        if embedding:
            if self.embeddings == embedding:
                print(f"Speaker {self.name} recognized through embeddings")
                return True
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
