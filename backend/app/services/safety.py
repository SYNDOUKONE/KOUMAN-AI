"""Filets de sécurité sur les sorties de traduction, et messages de repli."""

from __future__ import annotations

import json
import re
from pathlib import Path

_WORD = re.compile(r"\w+", re.UNICODE)


def _normalize(text: str) -> str:
    return " ".join(_WORD.findall(text.lower()))


def has_loop(text: str, n: int = 3, max_repeats: int = 3) -> bool:
    """Vrai si un même groupe de n mots se répète plus de max_repeats fois."""
    words = _WORD.findall(text.lower())
    counts: dict[tuple, int] = {}
    for i in range(len(words) - n + 1):
        gram = tuple(words[i : i + n])
        counts[gram] = counts.get(gram, 0) + 1
        if counts[gram] > max_repeats:
            return True
    return False


def check_translation(source: str, output: str) -> str | None:
    """Renvoie la raison du rejet, ou None si la sortie est acceptable."""
    if not output or not output.strip():
        return "sortie_vide"
    if _normalize(output) == _normalize(source) and len(_normalize(source)) > 0:
        return "identique_a_l_entree"
    if len(output) > 3 * len(source) + 50:
        return "trop_longue"
    if has_loop(output):
        return "repetition_en_boucle"
    return None


class Fallbacks:
    def __init__(self, path: Path) -> None:
        self.messages: dict[str, dict[str, str]] = json.loads(
            Path(path).read_text(encoding="utf-8")
        )["messages"]

    def get(self, kind: str, lang: str) -> str:
        return self.messages.get(kind, {}).get(lang) or self.messages["generic"]["fr"]
