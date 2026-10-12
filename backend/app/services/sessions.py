"""Sessions de conversation en mémoire, avec durée de vie.

Limite assumée : tout est perdu au redémarrage, et ne fonctionne qu'avec
UN seul processus (pas de --workers > 1). Suffisant pour la démo.
L'historique est stocké EN FRANÇAIS et n'est jamais retraduit.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field


@dataclass
class Session:
    lang: str
    history_fr: list[dict] = field(default_factory=list)
    last_seen: float = field(default_factory=time.monotonic)


class SessionStore:
    def __init__(self, ttl_seconds: int, max_turns: int) -> None:
        self.ttl = ttl_seconds
        self.max_turns = max_turns
        self._sessions: dict[str, Session] = {}
        self._lock = threading.Lock()

    def _purge(self, now: float) -> None:
        expired = [k for k, s in self._sessions.items() if now - s.last_seen > self.ttl]
        for k in expired:
            del self._sessions[k]

    def get(self, key: str, lang: str) -> Session:
        now = time.monotonic()
        with self._lock:
            self._purge(now)
            session = self._sessions.get(key)
            if session is None or session.lang != lang:
                # Changer de langue en cours de route = nouvelle conversation.
                session = Session(lang=lang)
                self._sessions[key] = session
            session.last_seen = now
            return session

    def append(self, session: Session, user_fr: str, assistant_fr: str) -> None:
        with self._lock:
            session.history_fr.append({"role": "user", "content": user_fr})
            session.history_fr.append({"role": "assistant", "content": assistant_fr})
            # Un tour = 2 messages ; on garde les N derniers tours.
            session.history_fr[:] = session.history_fr[-2 * self.max_turns :]

    def __len__(self) -> int:
        return len(self._sessions)
