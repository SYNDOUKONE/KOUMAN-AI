"""Configuration du service, lue UNIQUEMENT depuis les variables d'environnement.

Changer d'implémentation (stub -> vrai modèle) se fait ici, jamais dans le code.
Toutes les variables sont préfixées KOUMA_, sauf GEMINI_API_KEY.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]


def _env(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name)
    return value if value not in (None, "") else default


def _env_bool(name: str, default: bool) -> bool:
    value = _env(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "oui", "on"}


def _env_int(name: str, default: int) -> int:
    value = _env(name)
    return int(value) if value is not None else default


def _env_list(name: str, default: list[str]) -> list[str]:
    value = _env(name)
    if value is None:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    # --- Implémentations -------------------------------------------------
    translator_backend: str = "stub"  # "stub" | "nllb"
    llm_backend: str = "stub"  # "stub" | "gemini"

    # --- Traducteur NLLB + LoRA ------------------------------------------
    nllb_base_model: str = "facebook/nllb-200-1.3B"
    # Un adaptateur par sens. Vide = modèle de base sans adaptateur pour ce sens.
    # Les deux peuvent pointer vers le même dossier (adaptateur bidirectionnel).
    adapter_fra_dyu: str | None = None
    adapter_dyu_fra: str | None = None
    device: str = "auto"  # "auto" | "cuda" | "mps" | "cpu"
    num_beams: int = 4
    max_new_tokens: int = 128
    no_repeat_ngram_size: int = 3
    max_concurrent_translations: int = 2
    postprocess_rules_path: Path = ROOT_DIR / "config" / "postprocess_rules.json"

    # --- LLM ---------------------------------------------------------------
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    system_prompt_path: Path = ROOT_DIR / "config" / "system_prompt_fr.txt"

    # --- Langues -----------------------------------------------------------
    enabled_languages: list[str] = field(default_factory=lambda: ["dyu"])

    # --- Conversation ------------------------------------------------------
    history_max_turns: int = 6
    session_ttl_seconds: int = 1800
    max_message_chars: int = 1000
    fallbacks_path: Path = ROOT_DIR / "config" / "fallbacks.json"

    # --- Sécurité ----------------------------------------------------------
    auth_enabled: bool = True
    api_keys_db: Path = ROOT_DIR / "data_runtime" / "api_keys.sqlite3"
    rate_limit_per_minute: int = 30
    cors_origins: list[str] = field(default_factory=list)
    debug_allowed: bool = False

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            translator_backend=_env("KOUMA_TRANSLATOR", "stub"),
            llm_backend=_env("KOUMA_LLM", "stub"),
            nllb_base_model=_env("KOUMA_NLLB_BASE_MODEL", cls.nllb_base_model),
            adapter_fra_dyu=_env("KOUMA_ADAPTER_FRA_DYU"),
            adapter_dyu_fra=_env("KOUMA_ADAPTER_DYU_FRA"),
            device=_env("KOUMA_DEVICE", "auto"),
            num_beams=_env_int("KOUMA_NUM_BEAMS", 4),
            max_new_tokens=_env_int("KOUMA_MAX_NEW_TOKENS", 128),
            no_repeat_ngram_size=_env_int("KOUMA_NO_REPEAT_NGRAM_SIZE", 3),
            max_concurrent_translations=_env_int("KOUMA_MAX_CONCURRENT_TRANSLATIONS", 2),
            gemini_api_key=_env("GEMINI_API_KEY"),
            gemini_model=_env("KOUMA_GEMINI_MODEL", cls.gemini_model),
            enabled_languages=_env_list("KOUMA_ENABLED_LANGUAGES", ["dyu"]),
            history_max_turns=_env_int("KOUMA_HISTORY_MAX_TURNS", 6),
            session_ttl_seconds=_env_int("KOUMA_SESSION_TTL_SECONDS", 1800),
            max_message_chars=_env_int("KOUMA_MAX_MESSAGE_CHARS", 1000),
            auth_enabled=_env_bool("KOUMA_AUTH_ENABLED", True),
            api_keys_db=Path(_env("KOUMA_API_KEYS_DB", str(cls.api_keys_db))),
            rate_limit_per_minute=_env_int("KOUMA_RATE_LIMIT_PER_MINUTE", 30),
            cors_origins=_env_list("KOUMA_CORS_ORIGINS", []),
            debug_allowed=_env_bool("KOUMA_DEBUG_ALLOWED", False),
        )


@lru_cache
def get_settings() -> Settings:
    return Settings.from_env()
