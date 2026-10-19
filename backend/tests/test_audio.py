"""Tests des points d'accès Audio (TTS, STT et Voice Chat)."""

from __future__ import annotations

import base64
import io
import wave
import pytest


def _make_dummy_wav() -> bytes:
    """Crée un fichier WAV factice valide pour les tests d'upload."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(16000)
        f.writeframes(b"\x00\x00" * 800)  # 50 ms de silence
    return buf.getvalue()


@pytest.fixture
def dummy_wav_bytes() -> bytes:
    return _make_dummy_wav()


def test_health_includes_audio_info(api):
    _, client = api
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "audio" in data
    assert data["audio"]["mode"] == "stub"
    assert "tts_model" in data["audio"]
    assert "stt_model" in data["audio"]


def test_audio_synthesize_json(api):
    _, client = api
    payload = {
        "text": "I ni sɔgɔma",
        "lang": "dyu",
        "speaking_rate": 0.75,
    }
    r = client.post("/api/v1/audio/synthesize", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["text"] == "I ni sɔgɔma"
    assert data["lang"] == "dyu"
    assert data["speaking_rate"] == 0.75
    assert "audio_base64" in data
    # Décode base64 pour vérifier que c'est bien du WAV
    wav_bytes = base64.b64decode(data["audio_base64"])
    assert wav_bytes[:4] == b"RIFF"
    assert data["duration_s"] > 0
    assert data["sampling_rate"] == 16000


def test_audio_synthesize_wav_binary(api):
    _, client = api
    payload = {
        "text": "An bɛ bɛn sini",
        "lang": "dyu",
        "speaking_rate": 1.0,
    }
    r = client.post("/api/v1/audio/synthesize?format=wav", json=payload)
    assert r.status_code == 200
    assert r.headers["content-type"] == "audio/wav"
    assert r.content[:4] == b"RIFF"


def test_audio_transcribe(api, dummy_wav_bytes):
    _, client = api
    files = {"file": ("test.wav", dummy_wav_bytes, "audio/wav")}
    r = client.post("/api/v1/audio/transcribe", files=files)
    assert r.status_code == 200
    data = r.json()
    assert data["lang"] == "dyu"
    assert len(data["text"]) > 0
    assert "time_ms" in data


def test_audio_transcribe_empty_file_fails(api):
    _, client = api
    files = {"file": ("empty.wav", b"", "audio/wav")}
    r = client.post("/api/v1/audio/transcribe", files=files)
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "audio_vide"


def test_chat_voice_pipeline(api, dummy_wav_bytes):
    _, client = api
    data = {
        "session_id": "sess-voice-1",
        "lang": "dyu",
        "speaking_rate": 0.8,
    }
    files = {"file": ("parole.wav", dummy_wav_bytes, "audio/wav")}
    r = client.post("/api/v1/chat/voice?debug=true", data=data, files=files)
    assert r.status_code == 200
    res = r.json()
    assert res["session_id"] == "sess-voice-1"
    assert res["lang"] == "dyu"
    assert len(res["user_transcript"]) > 0
    assert len(res["reply_text"]) > 0
    assert "audio_base64" in res
    wav_bytes = base64.b64decode(res["audio_base64"])
    assert wav_bytes[:4] == b"RIFF"

    # Vérification des chronométrages complets
    timings = res["timings_ms"]
    assert "stt" in timings
    assert "mt_in" in timings
    assert "llm" in timings
    assert "mt_out" in timings
    assert "tts" in timings
    assert "total" in timings

    # Vérification du mode debug
    assert "debug" in res
    assert res["debug"]["fr_input"]
    assert res["debug"]["fr_reply"]
