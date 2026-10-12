"""Clés d'API (une par application cliente) et limitation de débit.

Les clés sont stockées HACHÉES (SHA-256) dans SQLite : une fuite de la base
ne révèle pas les clés. La clé en clair n'est affichée qu'une fois, à la création.
"""

from __future__ import annotations

import hashlib
import secrets
import sqlite3
import threading
import time
from collections import defaultdict, deque
from pathlib import Path

KEY_PREFIX = "kma_"


def hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


class ApiKeyStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        with self._connect() as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS api_keys (
                       key_hash   TEXT PRIMARY KEY,
                       client     TEXT NOT NULL,
                       created_at REAL NOT NULL,
                       revoked    INTEGER NOT NULL DEFAULT 0
                   )"""
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def create(self, client: str) -> str:
        raw = KEY_PREFIX + secrets.token_urlsafe(32)
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO api_keys (key_hash, client, created_at) VALUES (?, ?, ?)",
                (hash_key(raw), client, time.time()),
            )
        return raw

    def revoke(self, client: str) -> int:
        with self._lock, self._connect() as conn:
            cur = conn.execute(
                "UPDATE api_keys SET revoked = 1 WHERE client = ? AND revoked = 0", (client,)
            )
            return cur.rowcount

    def lookup(self, raw_key: str) -> str | None:
        """Renvoie le nom du client si la clé est valide, sinon None."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT client FROM api_keys WHERE key_hash = ? AND revoked = 0",
                (hash_key(raw_key),),
            ).fetchone()
        return row[0] if row else None

    def list_clients(self) -> list[tuple[str, float, bool]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT client, created_at, revoked FROM api_keys ORDER BY created_at"
            ).fetchall()
        return [(c, t, bool(r)) for c, t, r in rows]


class RateLimiter:
    """Fenêtre glissante de 60 s par client, en mémoire (un seul processus)."""

    def __init__(self, per_minute: int) -> None:
        self.per_minute = per_minute
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, client: str) -> bool:
        if self.per_minute <= 0:
            return True
        now = time.monotonic()
        with self._lock:
            hits = self._hits[client]
            while hits and now - hits[0] > 60:
                hits.popleft()
            if len(hits) >= self.per_minute:
                return False
            hits.append(now)
            return True
