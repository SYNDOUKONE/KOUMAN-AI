"""Tests unitaires : sécurité, filets, sessions, post-traitement."""

from __future__ import annotations

import json

from app.core.security import ApiKeyStore, RateLimiter, hash_key
from app.services.orchestrator import clean_llm_reply
from app.services.safety import check_translation, has_loop
from app.services.sessions import SessionStore
from app.services.translator import PostProcessor


def test_keys_are_stored_hashed(tmp_path):
    store = ApiKeyStore(tmp_path / "k.sqlite3")
    key = store.create("appli")
    raw = (tmp_path / "k.sqlite3").read_bytes()
    assert key.encode() not in raw
    assert hash_key(key).encode() in raw
    assert store.lookup(key) == "appli"
    assert store.lookup("kma_faux") is None


def test_rate_limiter_zero_means_unlimited():
    limiter = RateLimiter(0)
    assert all(limiter.allow("c") for _ in range(100))


def test_check_translation():
    assert check_translation("Bonjour", "") == "sortie_vide"
    assert check_translation("Bonjour !", "bonjour") == "identique_a_l_entree"
    assert check_translation("Oui", "a " * 100) == "trop_longue"
    assert check_translation("Bonjour", "I ni sɔgɔma") is None


def test_has_loop_detects_repetition():
    assert has_loop("a b c a b c a b c a b c a b c")
    assert not has_loop("un deux trois quatre cinq six")


def test_session_changes_when_language_changes():
    store = SessionStore(ttl_seconds=60, max_turns=3)
    s = store.get("k", "dyu")
    store.append(s, "q", "r")
    assert store.get("k", "bam").history_fr == []


def test_session_expires(monkeypatch):
    import app.services.sessions as mod

    now = [1000.0]
    monkeypatch.setattr(mod.time, "monotonic", lambda: now[0])
    store = SessionStore(ttl_seconds=10, max_turns=3)
    store.append(store.get("k", "dyu"), "q", "r")
    now[0] += 11
    assert store.get("k", "dyu").history_fr == []


def test_postprocessor_respects_enabled_flag(tmp_path):
    path = tmp_path / "rules.json"
    rule = {"pair": "fr-dyu", "pattern": "^A\\b", "replacement": "B", "reason": "test"}
    path.write_text(json.dumps({"version": "t", "rules": [{**rule, "enabled": True}]}))
    assert PostProcessor(path).apply("A x", "fr", "dyu") == "B x"
    assert PostProcessor(path).apply("A x", "dyu", "fr") == "A x"
    path.write_text(json.dumps({"version": "t", "rules": [{**rule, "enabled": False}]}))
    assert PostProcessor(path).apply("A x", "fr", "dyu") == "A x"


def test_clean_llm_reply():
    assert clean_llm_reply("Bonjour !\nComment allez-vous ?") == "Bonjour ! Comment allez-vous ?"
    assert clean_llm_reply("Une idée\nUne autre idée.") == "Une idée. Une autre idée."
    assert clean_llm_reply("## Titre\n**Gras** et `code`") == "Titre. Gras et code"
    assert (
        clean_llm_reply("Voici deux conseils :\n1. Buvez de l'eau\n2) Reposez-vous\n")
        == "Voici deux conseils : Buvez de l'eau. Reposez-vous"
    )
    assert clean_llm_reply("  \n \r\n ") == ""
    assert clean_llm_reply("Déjà propre.") == "Déjà propre."
