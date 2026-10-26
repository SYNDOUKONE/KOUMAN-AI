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

try:
    from dotenv import load_dotenv

    load_dotenv(ROOT_DIR / ".env")
except ImportError:
    pass


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
    llm_backend: str = "stub"  # "stub" | "gemini" | "openrouter"
    audio_backend: str = "stub"  # "stub" | "real"
    tts_model_id: str = "facebook/mms-tts-dyu"
    tts_speaker: str = "Bourama"
    stt_model_id: str = "Dama12/whisper-tiny-dioula"
    stt_base_id: str = "openai/whisper-tiny"
    tts_default_speaking_rate: float = 1.0

    # --- Traducteur NLLB + LoRA ------------------------------------------
    # Modèle chargé par transformers : un identifiant Hugging Face ou un dossier local.
    # - NLLB de base + adaptateurs LoRA : laisser "facebook/nllb-200-1.3B" et renseigner
    #   KOUMA_ADAPTER_*.
    # - Modèle déjà fusionné (ex. syndou/nllb-200-dioula) : mettre son identifiant ici et
    #   laisser KOUMA_ADAPTER_* vides.
    nllb_base_model: str = "facebook/nllb-200-1.3B"
    # Version exacte du modèle (hash de commit Hugging Face) : évite qu'une mise à jour
    # du dépôt change les traductions sans que personne ne s'en aperçoive.
    nllb_revision: str | None = None
    # Un adaptateur par sens. Vide = modèle de base sans adaptateur pour ce sens.
    # Les deux peuvent pointer vers le même dossier (adaptateur bidirectionnel).
    adapter_fra_dyu: str | None = None
    adapter_dyu_fra: str | None = None
    device: str = "auto"  # "auto" | "cuda" | "mps" | "cpu"
    num_beams: int = 4
    # 64 = valeur recommandée par la carte du modèle (entraîné sur des phrases de 48 tokens
    # au plus). Les réponses du LLM sont traduites phrase par phrase : 64 suffit largement.
    max_new_tokens: int = 64
    no_repeat_ngram_size: int = 3
    max_concurrent_translations: int = 2
    postprocess_rules_path: Path = ROOT_DIR / "config" / "postprocess_rules.json"
    # Traduire la réponse du LLM phrase par phrase, en un seul lot (plus rapide et plus
    # fidèle : le modèle a été entraîné sur des phrases courtes). false = un seul bloc.
    split_reply_sentences: bool = True

    # --- LLM ---------------------------------------------------------------
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    system_prompt_path: Path = ROOT_DIR / "config" / "system_prompt_fr.txt"

    openrouter_api_key: str | None = None
    openrouter_model: str = "anthropic/claude-sonnet-5"
    # Plafond de tokens de la réponse. Les modèles « à raisonnement » (ex. GPT-5 Mini)
    # comptent aussi leur réflexion : en dessous de ~1000 ils tronquent (benchmark du 08/10).
    llm_max_tokens: int = 1000
    llm_timeout_seconds: float = 60.0

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
            audio_backend=_env("KOUMA_AUDIO", "stub"),
            tts_model_id=_env("KOUMA_TTS_MODEL", cls.tts_model_id),
            tts_speaker=_env("KOUMA_TTS_SPEAKER", cls.tts_speaker),
            stt_model_id=_env("KOUMA_STT_MODEL", cls.stt_model_id),
            stt_base_id=_env("KOUMA_STT_BASE_MODEL", cls.stt_base_id),
            tts_default_speaking_rate=float(
                _env("KOUMA_TTS_SPEED", str(cls.tts_default_speaking_rate))
            ),
            nllb_base_model=_env("KOUMA_NLLB_BASE_MODEL", cls.nllb_base_model),
            nllb_revision=_env("KOUMA_NLLB_REVISION"),
            adapter_fra_dyu=_env("KOUMA_ADAPTER_FRA_DYU"),
            adapter_dyu_fra=_env("KOUMA_ADAPTER_DYU_FRA"),
            device=_env("KOUMA_DEVICE", "auto"),
            num_beams=_env_int("KOUMA_NUM_BEAMS", 4),
            max_new_tokens=_env_int("KOUMA_MAX_NEW_TOKENS", cls.max_new_tokens),
            no_repeat_ngram_size=_env_int("KOUMA_NO_REPEAT_NGRAM_SIZE", 3),
            max_concurrent_translations=_env_int("KOUMA_MAX_CONCURRENT_TRANSLATIONS", 2),
            split_reply_sentences=_env_bool("KOUMA_SPLIT_REPLY_SENTENCES", True),
            gemini_api_key=_env("GEMINI_API_KEY"),
            gemini_model=_env("KOUMA_GEMINI_MODEL", cls.gemini_model),
            openrouter_api_key=_env("OPENROUTER_API_KEY"),
            openrouter_model=_env("KOUMA_OPENROUTER_MODEL", cls.openrouter_model),
            llm_max_tokens=_env_int("KOUMA_LLM_MAX_TOKENS", cls.llm_max_tokens),
            llm_timeout_seconds=float(
                _env("KOUMA_LLM_TIMEOUT_SECONDS", str(cls.llm_timeout_seconds))
            ),
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
