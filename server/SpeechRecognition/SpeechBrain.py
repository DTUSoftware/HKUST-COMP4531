from SpeechClass import SpeechClass
from speechbrain.pretrained import EncoderDecoderASR


class SpeechBrain(SpeechClass):
    def __init__(self, model: str):
        super().__init__()

        if model.lower() == "wav2vec2":
            self.asr_model = EncoderDecoderASR.from_hparams(source="speechbrain/asr-wav2vec2-commonvoice-en",
                                                            savedir="pretrained_models/asr-wav2vec2-commonvoice-en")
        elif model.lower() == "librispeech":
            self.asr_model = EncoderDecoderASR.from_hparams(source="speechbrain/asr-transformer-transformerlm-librispeech", savedir="pretrained_models/asr-transformer-transformerlm-librispeech")
        else:
            raise ValueError(f"Model {model} not supported")

    async def get_text(self, audio):
        transcription = self.asr_model.transcribe_file(audio)
        return transcription
