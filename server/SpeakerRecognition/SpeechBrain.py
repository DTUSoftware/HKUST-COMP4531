import os
import uuid
from typing import Optional
import aiofiles
from .SpeakerClass import SpeakerClass, Speaker
import torch
from speechbrain.pretrained import EncoderClassifier, SpeakerRecognition
import asyncio
import json


class SpeechBrainSpeaker(Speaker):
    def __init__(self, name: str, speaker_id=None, classifier=None, verification=None, audio_file=None, embeddings=None):
        super().__init__(name)
        self.speaker_id = speaker_id if speaker_id else str(uuid.uuid4())
        self.verification = verification
        self.classifier = classifier
        self.audio_file = audio_file
        self.embeddings = embeddings

        self.similarity = torch.nn.CosineSimilarity(dim=-1, eps=1e-6)

    async def is_speaker(self, audio: str, embeddings=None, threshold=0.25) -> bool:
        """
        https://huggingface.co/speechbrain/spkrec-ecapa-voxceleb#perform-speaker-verification
        :param audio: The audio to verify
        :param embeddings: The embeddings to use for verification
        :param threshold: The threshold for the similarity score
        :return:
        """
        # If we have embeddings, verify using embeddings manually
        if embeddings is not None and self.embeddings is not None:
            print(f"Checking using embeddings for speaker {self.name}")
            score = self.similarity(self.embeddings, embeddings)
            prediction = score > threshold
            print(f"Prediction for Speaker {self.name} is {prediction} ({score}) with embeddings.")
            return prediction == 1
        else:
            print("No embeddings provided, verifying audio files automatically")

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
        waveform = self.classifier.load_audio(audio)
        batch = waveform.unsqueeze(0)
        # signal, fs = torchaudio.load(audio)
        embeddings = self.classifier.encode_batch(batch)
        return embeddings

    async def enroll(self, audio: str, name: str) -> Speaker:
        # The verify already uses embeddings so we can just skip this step - if we want to do it manually in the future
        # we can bring it back
        embeddings = await self.get_embeddings(audio)
        speaker = SpeechBrainSpeaker(name=name, verification=self.verification, embeddings=embeddings, audio_file=audio,
                                     classifier=self.classifier)
        self.speakers.append(speaker)
        return speaker

    async def recognize(self, audio: str) -> Optional[Speaker]:
        embeddings = await self.get_embeddings(audio)
        for speaker in self.speakers:
            if await speaker.is_speaker(audio, embeddings=embeddings):
                print(f"Speaker {speaker.name} recognized!")
                return speaker
        print(f"Speaker not recognized!")
        return None

    async def save(self):
        """
        Saves the current speakers and their embeddings to a file, so that we can load them later
        :return:
        """
        # Make a speakers directory
        if not os.path.exists("speakers"):
            os.mkdir("speakers")

        async with aiofiles.open("speakers/speakers.json", "w") as f:
            speaker_objects = []
            for speaker in self.speakers:
                if speaker.embeddings is None or speaker.audio_file is None:
                    print(f"Skipping speaker {speaker.name} because it has no embeddings or audio file")
                    continue

                # Check if current audio file is in speakers directory
                if not os.path.exists(f"speakers/{speaker.speaker_id}.wav"):
                    # Copy audio file to speakers directory
                    async with aiofiles.open(speaker.audio_file, "rb") as f2:
                        audio_clip = await f2.read()
                        async with aiofiles.open(f"speakers/{speaker.speaker_id}.wav", "wb") as f3:
                            await f3.write(audio_clip)

                speaker_objects.append({
                    "name": speaker.name,
                    "speaker_id": speaker.speaker_id,
                    "embeddings": speaker.embeddings.tolist(),
                    "audio_file": f"speakers/{speaker.speaker_id}.wav"
                })

            await f.write(json.dumps(speaker_objects))

    async def load(self):
        """
        Loads the speakers from a file
        :return:
        """
        # Check if speakers file exists
        if os.path.exists("speakers/speakers.json"):
            async with aiofiles.open("speakers/speakers.json", "r") as f:
                try:
                    speakers = json.loads(await f.read())
                except json.JSONDecodeError:
                    print("Error loading speakers file, skipping loading speakers")
                    return False
                for speaker in speakers:
                    speaker_object = SpeechBrainSpeaker(name=speaker["name"], speaker_id=speaker["speaker_id"],
                                                        embeddings=torch.tensor(speaker["embeddings"]),
                                                        audio_file=speaker["audio_file"])
                    self.speakers.append(speaker_object)
            return True
        else:
            print("No speakers file found, skipping loading speakers")
        return False


async def main():
    speech_brain = SpeechBrain()
    if await speech_brain.load():
        print("Loaded speakers!")
    else:
        print("No speakers found, creating new speakers")
        speaker_marcus = await speech_brain.enroll("Marcus1.wav", "Marcus")
        speaker_mads = await speech_brain.enroll("Mads1.wav", "Mads")
        print("Enrolled speakers! Saving...")
        await speech_brain.save()
    who_is_it = await speech_brain.recognize("Mads2.wav")
    who_is_it = await speech_brain.recognize("neither.wav")


if __name__ == '__main__':
    asyncio.run(main())
