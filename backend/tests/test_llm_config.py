"""Configuration des clients LLM (sans réseau)."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from app.core.config import Settings
from app.services.llm import build_llm

ROOT = Path(__file__).resolve().parents[1]


def test_openrouter_default_model_is_not_gemini(monkeypatch):
    monkeypatch.delenv("KOUMA_OPENROUTER_MODEL", raising=False)
    assert Settings.from_env().openrouter_model == "anthropic/claude-sonnet-5"


def test_openrouter_model_and_tokens_from_env(monkeypatch):
    monkeypatch.setenv("KOUMA_OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct")
    monkeypatch.setenv("KOUMA_LLM_MAX_TOKENS", "400")
    s = Settings.from_env()
    assert s.openrouter_model == "meta-llama/llama-3.3-70b-instruct"
    assert s.llm_max_tokens == 400


def test_gemini_settings_are_still_read(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "cle-de-test")
    monkeypatch.setenv("KOUMA_GEMINI_MODEL", "gemini-x")
    s = Settings.from_env()
    assert (s.gemini_api_key, s.gemini_model) == ("cle-de-test", "gemini-x")


def test_openrouter_without_key_fails_clearly(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("KOUMA_LLM", "openrouter")
    with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY"):
        build_llm(Settings.from_env())


def test_api_starts_without_importing_openai():
    """Régression du 08/10 : `from openai import OpenAI` en tête de llm.py cassait tout."""
    code = "import sys, app.main; print('openai' in sys.modules)"
    out = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True, cwd=ROOT
    )
    assert out.stdout.strip() == "False"


def test_openrouter_client_uses_settings(monkeypatch):
    pytest.importorskip("openai")
    monkeypatch.setenv("OPENROUTER_API_KEY", "cle-de-test")
    monkeypatch.setenv("KOUMA_LLM_MAX_TOKENS", "321")
    llm = build_llm(replace(Settings.from_env(), llm_backend="openrouter"))
    assert llm.name == "openrouter"
    assert llm.max_tokens == 321
    assert str(llm.client.base_url).startswith("https://openrouter.ai/api/v1")
