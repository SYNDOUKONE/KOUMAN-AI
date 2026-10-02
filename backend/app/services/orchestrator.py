"""Pipeline du chatbot : langue locale -> français -> LLM -> langue locale.

L'inférence (bloquante) tourne dans un pool de threads, pour ne pas figer
le serveur ; un sémaphore limite les traductions simultanées (mémoire GPU).
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

from app.core.languages import PIVOT
from app.core.timing import elapsed_ms
from app.services.llm import LLMClient
from app.services.safety import Fallbacks, check_translation
from app.services.sessions import SessionStore
from app.services.translator import Translator


def normalize_input(text: str, lang: str) -> str:
    """Point d'entrée de la future convention d'écriture (pour l'instant : espaces)."""
    return " ".join(text.split())


@dataclass
class ChatResult:
    reply: str
    fr_input: str
    fr_reply: str
    timings_ms: dict[str, float] = field(default_factory=dict)
    fallback_reason: str | None = None


class ChatOrchestrator:
    def __init__(
        self,
        translator: Translator,
        llm: LLMClient,
        sessions: SessionStore,
        fallbacks: Fallbacks,
        system_prompt: str,
        max_concurrent_translations: int,
    ) -> None:
        self.translator = translator
        self.llm = llm
        self.sessions = sessions
        self.fallbacks = fallbacks
        self.system_prompt = system_prompt
        self._mt_slots = asyncio.Semaphore(max_concurrent_translations)

    async def translate(self, text: str, src: str, tgt: str) -> str:
        async with self._mt_slots:
            return await asyncio.to_thread(self.translator.translate, text, src, tgt)

    async def chat(self, session_id: str, text: str, lang: str) -> ChatResult:
        timings: dict[str, float] = {}
        session = self.sessions.get(session_id, lang)
        text = normalize_input(text, lang)

        # 1. Langue locale -> français
        t0 = time.perf_counter()
        fr_input = await self.translate(text, lang, PIVOT)
        timings["mt_in"] = elapsed_ms(t0)
        if (reason := check_translation(text, fr_input)) is not None:
            return ChatResult(
                reply=self.fallbacks.get("not_understood", lang),
                fr_input=fr_input,
                fr_reply="",
                timings_ms=timings,
                fallback_reason=f"mt_in:{reason}",
            )

        # 2. Réponse du LLM, en français, avec l'historique en français
        t0 = time.perf_counter()
        history = [*session.history_fr, {"role": "user", "content": fr_input}]
        fr_reply = await asyncio.to_thread(self.llm.reply, history, self.system_prompt)
        timings["llm"] = elapsed_ms(t0)
        if not fr_reply:
            return ChatResult(
                reply=self.fallbacks.get("generic", lang),
                fr_input=fr_input,
                fr_reply="",
                timings_ms=timings,
                fallback_reason="llm:vide",
            )

        # 3. Français -> langue locale
        t0 = time.perf_counter()
        reply = await self.translate(fr_reply, PIVOT, lang)
        timings["mt_out"] = elapsed_ms(t0)
        fallback_reason = None
        if (reason := check_translation(fr_reply, reply)) is not None:
            reply = self.fallbacks.get("generic", lang)
            fallback_reason = f"mt_out:{reason}"

        # On mémorise l'échange en français, même si la sortie a été remplacée :
        # le LLM garde ainsi le fil de ce qu'il a voulu dire.
        self.sessions.append(session, fr_input, fr_reply)
        return ChatResult(reply, fr_input, fr_reply, timings, fallback_reason)
