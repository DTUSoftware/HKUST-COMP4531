import torchaudio
import torchaudio.transforms as T
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
    
    def preprocess_audio(self, audio_path: str) -> str:
        """
        Applies preprocessing steps to the audio file such as noise reduction, 
        normalization, etc., and saves the processed file to a temporary location.
        """

        waveform, sample_rate = torchaudio.load(audio_path)

        # Setting the low-frequency cutoff and high-frequency cutoff of a bandpass filter
        low_cutoff_freq = 100 #low-frequency off 100Hz
        high_cutoff_freq = 8000 #higt-frequency off 8000Hz

        bandpass_filter = T.BandpassBiquad(sample_rate, low_cutoff_freq, high_cutoff_freq)

        waveform_filtered = bandpass_filter(waveform)

        # Save the preprocessed audio to a temporary file
        processed_audio_path = "temp_processed_audio.wav"
        torchaudio.save(processed_audio_path, waveform_filtered, sample_rate)
    
        
        return processed_audio_path
