"""Schémas d'entrée/sortie (Pydantic v2)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=128, examples=["user-42"])
    lang: str = Field(..., examples=["dyu"])
    message: str = Field(..., min_length=1, examples=["I ni sɔgɔma"])
    tgt_lang: str | None = Field(default=None, examples=["fr", "dyu"], description="Langue de réponse souhaitée")


class ChatDebug(BaseModel):
    fr_input: str
    fr_reply: str
    timings_ms: dict[str, float]
    fallback_reason: str | None = None


class ChatResponse(BaseModel):
    session_id: str
    lang: str
    reply: str
    debug: ChatDebug | None = None


class TranslateRequest(BaseModel):
    text: str = Field(..., min_length=1, examples=["Bonjour, comment vas-tu ?"])
    src: str = Field(..., examples=["fr"])
    tgt: str = Field(..., examples=["dyu"])


class TranslateResponse(BaseModel):
    text: str
    src: str
    tgt: str
    translation: str
    time_ms: float


class LanguageInfo(BaseModel):
    code: str
    name: str
    enabled: bool


class AudioSynthesizeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000, examples=["I ni sɔgɔma, i ka kɛnɛ wa ?"])
    lang: str = Field(default="dyu", examples=["dyu"])
    speaking_rate: float = Field(
        default=1.0, ge=0.5, le=2.0, description="Vitesse de voix (1.0 = normal, 0.75 = ralenti)"
    )


class AudioSynthesizeResponse(BaseModel):
    text: str
    lang: str
    speaking_rate: float
    audio_base64: str
    sampling_rate: int
    duration_s: float
    time_ms: float


class AudioTranscribeResponse(BaseModel):
    text: str
    lang: str
    time_ms: float


class VoiceChatResponse(BaseModel):
    session_id: str
    lang: str
    user_transcript: str
    reply_text: str
    audio_base64: str | None = None
    reply_lang: str = "dyu"
    timings_ms: dict[str, float]
    debug: ChatDebug | None = None
