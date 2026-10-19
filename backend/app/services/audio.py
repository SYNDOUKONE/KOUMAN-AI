"""Services Audio pour KOUMA AI : TTS (synthèse vocale) et STT (reconnaissance vocale).

- TTS Dioula : facebook/mms-tts-dyu (VITS) avec contrôle de la vitesse via librosa.effects.time_stretch.
- STT Dioula : Dama12/whisper-tiny-dioula (Whisper) avec extraction audio à 16 kHz.
- Mode 'stub' pour tests automatisés et CI/CD sans GPU ni dépendances lourdes.
"""

from __future__ import annotations

import io
import math
import struct
import wave
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from app.core.config import Settings


class AudioService(Protocol):
    def info(self) -> dict: ...

    async def text_to_speech(
        self, text: str, speaking_rate: float = 0.75
    ) -> tuple[bytes, float, int]:
        """Convertit du texte en audio WAV.

        Retourne: (wav_bytes, duration_seconds, sampling_rate)
        """
        ...

    async def speech_to_text(self, audio_bytes: bytes, filename: str = "audio.wav") -> str:
        """Convertit des données audio en texte transcrit."""
        ...


class StubAudioService:
    """Service audio factice pour tests rapides et développement local sans modèle."""

    def __init__(self, default_speaking_rate: float = 0.75) -> None:
        self.default_speaking_rate = default_speaking_rate

    def info(self) -> dict:
        return {
            "mode": "stub",
            "tts_model": "stub-mms-dyu",
            "stt_model": "stub-whisper-dyu",
        }

    async def text_to_speech(
        self, text: str, speaking_rate: float = 0.75
    ) -> tuple[bytes, float, int]:
        rate = speaking_rate or self.default_speaking_rate
        sampling_rate = 16000
        duration = max(0.5, min(5.0, len(text) * 0.05 / max(rate, 0.1)))
        num_samples = int(sampling_rate * duration)

        # Générer un bip sinusoïdal doux (440 Hz) au format WAV PCM 16-bit
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sampling_rate)
            # Signal doux
            frames = bytearray()
            for i in range(num_samples):
                val = int(1000 * math.sin(2 * math.pi * 440 * i / sampling_rate))
                frames.extend(struct.pack("<h", val))
            wav_file.writeframes(frames)

        return buf.getvalue(), round(duration, 2), sampling_rate

    async def speech_to_text(self, audio_bytes: bytes, filename: str = "audio.wav") -> str:
        if not audio_bytes:
            return ""
        # Réponse déterministe en stub
        return "I ni sɔgɔma, i ka kɛnɛ wa ?"


class RealAudioService:
    """Service audio utilisant transformers (MMS-TTS Dioula et Whisper Tiny Dioula)."""

    def __init__(
        self,
        tts_model_id: str = "facebook/mms-tts-dyu",
        stt_model_id: str = "Dama12/whisper-tiny-dioula",
        stt_base_id: str = "openai/whisper-tiny",
        device: str = "auto",
        default_speaking_rate: float = 0.75,
    ) -> None:
        self.tts_model_id = tts_model_id
        self.stt_model_id = stt_model_id
        self.stt_base_id = stt_base_id
        self.default_speaking_rate = default_speaking_rate

        import torch

        if device == "auto":
            self.device = (
                "mps"
                if torch.backends.mps.is_available()
                else ("cuda" if torch.cuda.is_available() else "cpu")
            )
        else:
            self.device = device

        self.tts_tokenizer = None
        self.tts_model = None
        self.stt_model = None
        self.stt_feature_extractor = None
        self.stt_tokenizer = None
        self._stt_device = "cpu"  # Whisper avec aten::isin plus stable sur CPU que MPS

    def info(self) -> dict:
        return {
            "mode": "real",
            "tts_model": self.tts_model_id,
            "stt_model": self.stt_model_id,
            "device": self.device,
        }

    def _ensure_tts(self) -> None:
        if self.tts_model is not None:
            return
        from transformers import AutoTokenizer, VitsModel

        self.tts_tokenizer = AutoTokenizer.from_pretrained(self.tts_model_id)
        self.tts_model = VitsModel.from_pretrained(self.tts_model_id).to(self.device)
        self.tts_model.eval()

    def _ensure_stt(self) -> None:
        if self.stt_model is not None:
            return
        from transformers import (
            WhisperFeatureExtractor,
            WhisperForConditionalGeneration,
            WhisperTokenizer,
        )

        self.stt_feature_extractor = WhisperFeatureExtractor.from_pretrained(self.stt_base_id)
        try:
            self.stt_tokenizer = WhisperTokenizer.from_pretrained(
                self.stt_base_id, language="dyu", task="transcribe"
            )
        except Exception:
            self.stt_tokenizer = WhisperTokenizer.from_pretrained(
                self.stt_base_id, task="transcribe"
            )
        self.stt_model = WhisperForConditionalGeneration.from_pretrained(self.stt_model_id).to(
            self._stt_device
        )
        self.stt_model.eval()

    async def text_to_speech(
        self, text: str, speaking_rate: float = 0.75
    ) -> tuple[bytes, float, int]:
        import asyncio

        def _generate():
            import librosa
            import scipy.io.wavfile as wavfile
            import torch

            self._ensure_tts()
            inputs = self.tts_tokenizer(text.lower(), return_tensors="pt").to(self.device)
            torch.manual_seed(42)
            with torch.no_grad():
                waveform = self.tts_model(**inputs).waveform[0].cpu().numpy()

            sampling_rate = self.tts_model.config.sampling_rate
            rate = speaking_rate or self.default_speaking_rate
            if rate != 1.0:
                waveform = librosa.effects.time_stretch(waveform, rate=rate)

            buf = io.BytesIO()
            wavfile.write(buf, sampling_rate, waveform)
            duration = float(len(waveform) / sampling_rate)
            return buf.getvalue(), round(duration, 2), sampling_rate

        return await asyncio.to_thread(_generate)

    async def speech_to_text(self, audio_bytes: bytes, filename: str = "audio.wav") -> str:
        import asyncio

        def _transcribe():
            import subprocess
            import librosa
            import torch

            self._ensure_stt()

            # Conversion universelle de tout flux audio (WebM, Opus, MP4, OGG, WAV) en WAV 16kHz mono
            raw_bytes = audio_bytes
            try:
                cmd = ["ffmpeg", "-y", "-i", "pipe:0", "-f", "wav", "-ar", "16000", "-ac", "1", "pipe:1"]
                proc = subprocess.run(
                    cmd, input=audio_bytes, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                if proc.returncode == 0 and len(proc.stdout) > 44:
                    raw_bytes = proc.stdout
            except Exception:
                pass

            buf = io.BytesIO(raw_bytes)
            audio, _ = librosa.load(buf, sr=16000, mono=True)
            inputs = self.stt_feature_extractor(
                audio, sampling_rate=16000, return_tensors="pt"
            ).to(self._stt_device)
            with torch.no_grad():
                predicted_ids = self.stt_model.generate(
                    inputs["input_features"],
                    max_new_tokens=128,
                )
            text = self.stt_tokenizer.batch_decode(predicted_ids, skip_special_tokens=True)[
                0
            ].strip()
            return text

        return await asyncio.to_thread(_transcribe)


def build_audio_service(settings: Settings) -> AudioService:
    if settings.audio_backend == "real":
        return RealAudioService(
            tts_model_id=settings.tts_model_id,
            stt_model_id=settings.stt_model_id,
            stt_base_id=settings.stt_base_id,
            device=settings.device,
            default_speaking_rate=settings.tts_default_speaking_rate,
        )
    return StubAudioService(default_speaking_rate=settings.tts_default_speaking_rate)
