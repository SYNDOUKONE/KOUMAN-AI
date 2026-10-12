import os
import torch
import scipy.io.wavfile as wavfile
from transformers import AutoTokenizer, VitsModel, pipeline

class AudioService:
    def __init__(self):
        self.device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
        self.tts_model_id = "facebook/mms-tts-dyu"
        self.stt_model_id = "Dama12/whisper-tiny-dioula"
        
        self.tts_tokenizer = None
        self.tts_model = None
        self.stt_pipeline = None

    def load_tts(self):
        if self.tts_model is None:
            print(f"Chargement de MMS-TTS ({self.tts_model_id})...", flush=True)
            self.tts_tokenizer = AutoTokenizer.from_pretrained(self.tts_model_id)
            self.tts_model = VitsModel.from_pretrained(self.tts_model_id).to(self.device)

    def load_stt(self):
        if self.stt_pipeline is None:
            print(f"Chargement de Whisper STT ({self.stt_model_id})...", flush=True)
            dev = self.device if self.device != "mps" else "cpu"
            self.stt_pipeline = pipeline("automatic-speech-recognition", model=self.stt_model_id, device=dev)

    def text_to_speech(self, text_dioula: str, output_wav_path: str) -> str:
        self.load_tts()
        inputs = self.tts_tokenizer(text_dioula.lower(), return_tensors="pt").to(self.device)
        torch.manual_seed(555)
        with torch.no_grad():
            waveform = self.tts_model(**inputs).waveform[0].cpu().numpy()
        
        sampling_rate = self.tts_model.config.sampling_rate
        wavfile.write(output_wav_path, sampling_rate, waveform)
        return output_wav_path

    def speech_to_text(self, audio_path: str) -> str:
        self.load_stt()
        res = self.stt_pipeline(audio_path)
        return res.get("text", "")
