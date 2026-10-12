"""Correspondance unique entre codes exposés par l'API et codes NLLB.

Ajouter une langue = ajouter une ligne ici, puis l'activer par
KOUMA_ENABLED_LANGUAGES. Aucun autre fichier n'a à connaître les codes NLLB.
"""

from __future__ import annotations

from dataclasses import dataclass

PIVOT = "fr"  # langue de travail du LLM et de l'historique


@dataclass(frozen=True)
class Language:
    code: str  # code exposé par l'API
    nllb: str  # code attendu par NLLB
    name: str


LANGUAGES: dict[str, Language] = {
    "fr": Language("fr", "fra_Latn", "Français"),
    "dyu": Language("dyu", "dyu_Latn", "Dioula"),
    "bam": Language("bam", "bam_Latn", "Bambara"),
    # "bci": Language("bci", "bci_Latn", "Baoulé"),  # phase 2 : absent de NLLB
}


def to_nllb(code: str) -> str:
    return LANGUAGES[code].nllb


def is_known(code: str) -> bool:
    return code in LANGUAGES
