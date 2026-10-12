"""Schémas d'entrée/sortie (Pydantic v2)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=128, examples=["user-42"])
    lang: str = Field(..., examples=["dyu"])
    message: str = Field(..., min_length=1, examples=["I ni sɔgɔma"])


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
