"""Mesure des durées, partagée par les routes et l'orchestrateur."""

from __future__ import annotations

import time


def elapsed_ms(start: float) -> float:
    """Millisecondes écoulées depuis `start` (time.perf_counter()), arrondies à 0,01 ms.

    On garde des décimales : un stub répond en moins d'une milliseconde, et un
    arrondi à l'entier afficherait 0, impossible à distinguer d'un chrono cassé.
    """
    return round((time.perf_counter() - start) * 1000, 2)
