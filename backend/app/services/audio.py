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

    async def speech_to_text(self, audio_bytes: bytes, filename: str = "audio.wav", lang: str = "dyu") -> str:
        if not audio_bytes:
            return ""
        # Réponse déterministe en stub
        return "I ni sɔgɔma, i ka kɛnɛ wa ?"


class RealAudioService:
    """Service audio utilisant transformers (MMS-TTS / Spark-TTS Bambara et Whisper Tiny Dioula)."""

    def __init__(
        self,
        tts_model_id: str = "facebook/mms-tts-dyu",
        stt_model_id: str = "Dama12/whisper-tiny-dioula",
        stt_base_id: str = "openai/whisper-tiny",
        device: str = "auto",
        default_speaking_rate: float = 0.75,
        tts_speaker: str = "Bourama",
    ) -> None:
        self.tts_model_id = tts_model_id
        self.tts_speaker = tts_speaker
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
        self.tts_codec = None
        self.stt_model = None
        self.stt_feature_extractor = None
        self.stt_tokenizer = None
        self._stt_device = "cpu"  # Whisper avec aten::isin plus stable sur CPU que MPS

    @property
    def is_spark_tts(self) -> bool:
        mid = (self.tts_model_id or "").lower()
        return "bambara-tts" in mid or "spark" in mid

    def info(self) -> dict:
        return {
            "mode": "real",
            "tts_model": self.tts_model_id,
            "tts_speaker": self.tts_speaker if self.is_spark_tts else None,
            "stt_model": self.stt_model_id,
            "device": self.device,
        }

    def _ensure_tts(self) -> None:
        if self.tts_model is not None:
            return

        if self.is_spark_tts:
            import torch
            from huggingface_hub import snapshot_download
            from transformers import AutoModelForCausalLM, AutoTokenizer
            from maliba_ai.sparktts.models.audio_tokenizer import BiCodecTokenizer

            spark_dir = snapshot_download(
                "SparkAudio/Spark-TTS-0.5B",
                allow_patterns=["config.yaml", "BiCodec/*"],
            )

            self.tts_tokenizer = AutoTokenizer.from_pretrained(
                self.tts_model_id, use_fast=False
            )
            # Toujours utiliser float32 pour Qwen2 TTS (float16 produit un underflow '!' sur MPS)
            compute_dtype = torch.float32
            self.tts_model = AutoModelForCausalLM.from_pretrained(
                self.tts_model_id,
                torch_dtype=compute_dtype,
            ).to(self.device)
            self.tts_model.eval()

            self.tts_codec = BiCodecTokenizer(
                model_dir=spark_dir, device=self.device, load_wav2vec2=False
            )
        else:
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

        if self.stt_feature_extractor is None:
            self.stt_feature_extractor = WhisperFeatureExtractor.from_pretrained(self.stt_base_id)
        # Tokenizer dyu : utilise le prompt natif de Dama12 (generation_config contient
        # [[1, None], [2, 50359]] → détection langue auto + tâche transcription)
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

    def _ensure_stt_fr(self) -> None:
        """Charge openai/whisper-tiny pour la transcription du français."""
        if getattr(self, "_stt_fr_model", None) is not None:
            return
        from transformers import (
            WhisperFeatureExtractor,
            WhisperForConditionalGeneration,
            WhisperTokenizer,
        )

        # Réutilise le même feature extractor si déjà chargé
        if self.stt_feature_extractor is None:
            self.stt_feature_extractor = WhisperFeatureExtractor.from_pretrained(self.stt_base_id)
        self._stt_fr_tokenizer = WhisperTokenizer.from_pretrained(
            self.stt_base_id, language="french", task="transcribe"
        )
        self._stt_fr_forced_ids = self._stt_fr_tokenizer.get_decoder_prompt_ids(
            language="french", task="transcribe"
        )
        self._stt_fr_model = WhisperForConditionalGeneration.from_pretrained(self.stt_base_id).to(
            self._stt_device
        )
        self._stt_fr_model.eval()

    async def text_to_speech(
        self, text: str, speaking_rate: float = 0.75
    ) -> tuple[bytes, float, int]:
        import asyncio

        def _generate():
            import re
            import librosa
            import scipy.io.wavfile as wavfile
            import torch

            self._ensure_tts()

            if self.is_spark_tts:
                try:
                    from maliba_ai.utils.utils import normalize_text
                    norm_text = normalize_text(text)
                except Exception:
                    norm_text = text

                speaker = getattr(self, "tts_speaker", "Bourama") or "Bourama"
                formatted = f"{speaker}: {norm_text}"
                prompt = (
                    f"<|task_tts|><|start_content|>{formatted}<|end_content|><|start_global_token|>"
                )
                inputs = self.tts_tokenizer([prompt], return_tensors="pt").to(self.device)
                with torch.inference_mode():
                    generated_ids = self.tts_model.generate(
                        **inputs,
                        max_new_tokens=512,
                        do_sample=True,
                        temperature=0.8,
                        top_k=50,
                        top_p=1.0,
                        eos_token_id=self.tts_tokenizer.eos_token_id,
                        pad_token_id=self.tts_tokenizer.pad_token_id,
                    )
                    trimmed = generated_ids[:, inputs.input_ids.shape[1] :]
                    predicted_text = self.tts_tokenizer.batch_decode(
                        trimmed, skip_special_tokens=False
                    )[0]

                semantic_re = re.compile(r"<\|bicodec_semantic_(\d+)\|>")
                global_re = re.compile(r"<\|bicodec_global_(\d+)\|>")
                semantic_ids = [int(t) for t in semantic_re.findall(predicted_text)]
                global_ids = [int(t) for t in global_re.findall(predicted_text)]

                waveform = self.tts_codec.wav_from_token_ids(global_ids, semantic_ids)
                sampling_rate = 16000
            else:
                inputs = self.tts_tokenizer(text.lower(), return_tensors="pt").to(self.device)
                torch.manual_seed(42)
                with torch.no_grad():
                    waveform = self.tts_model(**inputs).waveform[0].cpu().numpy()
                sampling_rate = self.tts_model.config.sampling_rate

            rate = speaking_rate or self.default_speaking_rate
            if rate != 1.0 and len(waveform) > 0:
                waveform = librosa.effects.time_stretch(waveform, rate=rate)

            buf = io.BytesIO()
            wavfile.write(buf, sampling_rate, waveform)
            duration = float(len(waveform) / sampling_rate) if sampling_rate else 0.0
            return buf.getvalue(), round(duration, 2), sampling_rate

        return await asyncio.to_thread(_generate)

    async def speech_to_text(
        self, audio_bytes: bytes, filename: str = "audio.wav", lang: str = "dyu"
    ) -> str:
        import asyncio

        def _transcribe():
            import subprocess
            import librosa
            import numpy as np
            import torch

            # --- Conversion universelle vers WAV 16kHz mono ---------------
            raw_bytes = audio_bytes
            try:
                cmd = [
                    "ffmpeg", "-y", "-i", "pipe:0",
                    "-f", "wav", "-ar", "16000", "-ac", "1", "pipe:1",
                ]
                proc = subprocess.run(
                    cmd, input=audio_bytes, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                if proc.returncode == 0 and len(proc.stdout) > 44:
                    raw_bytes = proc.stdout
            except Exception:
                pass

            buf = io.BytesIO(raw_bytes)
            audio, _ = librosa.load(buf, sr=16000, mono=True)

            # --- Normalisation amplitude + trim silence -------------------
            if len(audio) == 0:
                return ""
            # Trim silence (top_db=25 : seuil adapté au micro navigateur)
            audio, _ = librosa.effects.trim(audio, top_db=25)
            # Normalisation à 0.95 pour éviter la saturation
            peak = np.max(np.abs(audio))
            if peak > 0:
                audio = audio / peak * 0.95

            # --- Préparer le modèle et feature extractor selon la langue ---
            if lang == "fr":
                # Whisper tiny standard, forcé sur le français
                self._ensure_stt_fr()
                stt_model = self._stt_fr_model
                stt_tokenizer = self._stt_fr_tokenizer
                forced_ids = self._stt_fr_forced_ids
            else:
                # Whisper Dioula fine-tuné (Dama12), prompt depuis generation_config
                self._ensure_stt()
                stt_model = self.stt_model
                stt_tokenizer = self.stt_tokenizer
                forced_ids = None

            inputs = self.stt_feature_extractor(
                audio, sampling_rate=16000, return_tensors="pt"
            ).to(self._stt_device)

            # --- Transcription selon la langue ----------------------------
            with torch.no_grad():
                gen_kwargs = {
                    "num_beams": 3,
                    "max_new_tokens": 128,
                }
                if forced_ids is not None:
                    gen_kwargs["forced_decoder_ids"] = forced_ids
                predicted_ids = stt_model.generate(
                    inputs["input_features"],
                    **gen_kwargs,
                )
            text = stt_tokenizer.batch_decode(
                predicted_ids, skip_special_tokens=True
            )[0].strip()

            return text

        return await asyncio.to_thread(_transcribe)


def build_audio_service(settings: Settings) -> AudioService:
    if settings.audio_backend == "real":
        return RealAudioService(
            tts_model_id=settings.tts_model_id,
            tts_speaker=getattr(settings, "tts_speaker", "Bourama"),
            stt_model_id=settings.stt_model_id,
            stt_base_id=settings.stt_base_id,
            device=settings.device,
            default_speaking_rate=settings.tts_default_speaking_rate,
        )
    return StubAudioService(default_speaking_rate=settings.tts_default_speaking_rate)
