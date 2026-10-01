"""Tests avec le VRAI modèle. Ignorés par défaut.

    KOUMA_ADAPTER_FRA_DYU=/chemin/final KOUMA_ADAPTER_DYU_FRA=/chemin/final \
    pytest -m model
"""

from __future__ import annotations

import os
from dataclasses import replace

import pytest

from app.core.config import Settings

pytestmark = pytest.mark.model


@pytest.fixture(scope="module")
def translator():
    pytest.importorskip("torch")
    pytest.importorskip("peft")
    from app.services.translator import NllbLoraTranslator

    # Lit KOUMA_NLLB_BASE_MODEL, KOUMA_ADAPTER_*, KOUMA_DEVICE... depuis l'environnement.
    settings = replace(Settings.from_env(), translator_backend="nllb")
    return NllbLoraTranslator(settings)


def test_fr_to_dyu_returns_text(translator):
    out = translator.translate("Bonjour, comment allez-vous ?", "fr", "dyu")
    print("fr→dyu :", out)
    assert out.strip() and "[stub" not in out


def test_dyu_to_fr_returns_text(translator):
    sentence = os.environ.get("KOUMA_TEST_DYU_SENTENCE")
    if not sentence:
        pytest.skip("Fournir KOUMA_TEST_DYU_SENTENCE (phrase validée par un locuteur)")
    out = translator.translate(sentence, "dyu", "fr")
    print("dyu→fr :", out)
    assert out.strip()


def test_info_exposes_fingerprints(translator):
    info = translator.info()
    print(info)
    for direction in info["directions"].values():
        assert direction["fingerprint"] not in (None, "introuvable")
