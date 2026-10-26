"""Pipeline du chatbot : langue locale -> français -> LLM -> langue locale.

L'inférence (bloquante) tourne dans un pool de threads, pour ne pas figer
le serveur ; un sémaphore limite les traductions simultanées (mémoire GPU).
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
from dataclasses import dataclass, field

from app.core.languages import PIVOT
from app.core.timing import elapsed_ms
from app.services.llm import LLMClient, LLMUnavailable
from app.services.safety import Fallbacks, check_translation
from app.services.sessions import SessionStore
from app.services.translator import Translator

log = logging.getLogger("kouma")


def normalize_input(text: str, lang: str) -> str:
    """Point d'entrée de la future convention d'écriture (pour l'instant : espaces)."""
    return " ".join(text.split())


_BULLET = re.compile(r"^\s*(?:[-*•]+|\d+[.)])\s+")
_HEADING = re.compile(r"^\s*#+\s*")
_END_OF_SENTENCE = ".!?…:;"


def clean_llm_reply(text: str) -> str:
    """Prépare la réponse du LLM pour la traduction : une seule ligne, sans markdown.

    Le traducteur n'a vu que des phrases simples à l'entraînement : un retour à la ligne,
    une puce ou un « ** » le perturbent. Une ligne qui ne finit pas par une ponctuation
    reçoit un point, pour que deux lignes ne soient pas collées en une seule phrase.
    """
    lines = []
    for raw in text.replace("\r", "\n").split("\n"):
        line = _HEADING.sub("", _BULLET.sub("", raw))
        line = " ".join(line.replace("*", "").replace("`", "").split())
        if line:
            lines.append(line)
    for i in range(len(lines) - 1):
        if lines[i][-1] not in _END_OF_SENTENCE:
            lines[i] += "."
    return " ".join(lines)


_SENTENCE_END = re.compile(r"(?<=[.!?…])\s+")


def split_sentences(text: str) -> list[str]:
    """Découpe un texte en phrases, sur . ! ? … suivis d'un espace (ponctuation conservée)."""
    return [s for s in (part.strip() for part in _SENTENCE_END.split(text)) if s]


@dataclass
class ChatResult:
    reply: str
    fr_input: str
    fr_reply: str
    timings_ms: dict[str, float] = field(default_factory=dict)
    fallback_reason: str | None = None
    reply_lang: str = "dyu"


class ChatOrchestrator:
    def __init__(
        self,
        translator: Translator,
        llm: LLMClient,
        sessions: SessionStore,
        fallbacks: Fallbacks,
        system_prompt: str,
        max_concurrent_translations: int,
        split_reply_sentences: bool = True,
    ) -> None:
        self.translator = translator
        self.llm = llm
        self.sessions = sessions
        self.fallbacks = fallbacks
        self.system_prompt = system_prompt
        self._mt_slots = asyncio.Semaphore(max_concurrent_translations)
        self.split_reply_sentences = split_reply_sentences

    async def translate(self, text: str, src: str, tgt: str) -> str:
        async with self._mt_slots:
            return await asyncio.to_thread(self.translator.translate, text, src, tgt)

    async def translate_reply(self, text: str, src: str, tgt: str) -> str:
        """Traduit une réponse de plusieurs phrases en UN lot, une entrée par phrase.

        Le traducteur a été entraîné sur des phrases courtes : un bloc de 2-3 phrases
        est plus lent à décoder et souvent tronqué ou déformé.
        """
        sentences = split_sentences(text) if self.split_reply_sentences else [text]
        if len(sentences) <= 1:
            return await self.translate(text, src, tgt)
        async with self._mt_slots:
            parts = await asyncio.to_thread(self.translator.translate_batch, sentences, src, tgt)
        return " ".join(p.strip() for p in parts if p.strip())

    async def chat(
        self,
        session_id: str,
        text: str,
        lang: str = "dyu",
        tgt_lang: str | None = None,
    ) -> ChatResult:
        timings: dict[str, float] = {}
        session = self.sessions.get(session_id, lang, keep_history=True)
        text = normalize_input(text, lang)

        # Détection d'une consigne explicite de langue de réponse dans le texte
        lower_text = text.lower().strip()
        explicit_tgt: str | None = None
        if re.search(
            r"\b(r[ée]ponds?|parle|dis(?:-moi)?|explique|kouman)\s+(?:-moi\s+)?(?:en\s+)?français\b",
            lower_text,
        ) or re.search(r"\b(?:en\s+)?français\s*(?:s['’]il\s+te\s+pla[îi]t|svp)?\s*$", lower_text):
            explicit_tgt = PIVOT
        elif re.search(
            r"\b(r[ée]ponds?|parle|dis(?:-moi)?|explique|kouman)\s+(?:-moi\s+)?(?:en\s+)?(?:dioula|dyu|jula)\b",
            lower_text,
        ) or re.search(
            r"\b(a\s+f[ɔo]|kouman)\s+(?:dioula|jula|dioulakan|julakan|tubabukan)\b",
            lower_text,
        ) or re.search(r"\b(?:en\s+)?(?:dioula|dyu|jula)\s*(?:s['’]il\s+te\s+pla[îi]t|svp)?\s*$", lower_text):
            if "tubabukan" in lower_text:
                explicit_tgt = PIVOT
            else:
                explicit_tgt = "dyu"

        if explicit_tgt is not None:
            effective_tgt_lang = explicit_tgt
        elif tgt_lang in (PIVOT, "dyu"):
            effective_tgt_lang = tgt_lang
        elif getattr(session, "tgt_lang", None) in (PIVOT, "dyu"):
            effective_tgt_lang = session.tgt_lang
        else:
            effective_tgt_lang = lang

        session.tgt_lang = effective_tgt_lang

        if lang == PIVOT:
            fr_input = text
            timings["mt_in"] = 0.0
        else:
            # 1. Langue locale -> français
            t0 = time.perf_counter()
            fr_input = await self.translate(text, lang, PIVOT)
            timings["mt_in"] = elapsed_ms(t0)
            if (reason := check_translation(text, fr_input)) is not None:
                return ChatResult(
                    reply=self.fallbacks.get("not_understood", effective_tgt_lang),
                    fr_input=fr_input,
                    fr_reply="",
                    timings_ms=timings,
                    fallback_reason=f"mt_in:{reason}",
                    reply_lang=effective_tgt_lang,
                )

        # 2. Réponse du LLM, en français, avec l'historique en français
        t0 = time.perf_counter()
        history = [*session.history_fr, {"role": "user", "content": fr_input}]
        system_instruction = self.system_prompt
        if effective_tgt_lang == PIVOT:
            system_instruction += (
                "\nL'utilisateur souhaite que tu répondes directement et entièrement en FRANÇAIS, "
                "de façon claire, courtoise et concise (2 à 3 phrases maximum)."
            )
        else:
            system_instruction += (
                "\nL'utilisateur souhaite une réponse en DIOULA. Réponds en français simple, concis "
                "et direct (1 à 2 phrases courtes), qui sera traduite fidèlement en dioula."
            )

        try:
            raw_reply = await asyncio.to_thread(self.llm.reply, history, system_instruction)
        except Exception as exc:
            # Panne du LLM (réseau, quota, clé...) : le détail va dans les logs, pas au client.
            # On sort AVANT d'écrire dans l'historique : l'échange raté n'est pas mémorisé.
            log.exception("llm_erreur", extra={"fields": {"llm": self.llm.name}})
            raise LLMUnavailable(f"{self.llm.name} indisponible") from exc
        timings["llm"] = elapsed_ms(t0)
        fr_reply = clean_llm_reply(raw_reply)
        if not fr_reply:
            return ChatResult(
                reply=self.fallbacks.get("generic", effective_tgt_lang),
                fr_input=fr_input,
                fr_reply="",
                timings_ms=timings,
                fallback_reason="llm:vide",
                reply_lang=effective_tgt_lang,
            )

        if effective_tgt_lang == PIVOT:
            reply = fr_reply
            timings["mt_out"] = 0.0
            fallback_reason = None
        else:
            # 3. Français -> langue locale (dioula)
            t0 = time.perf_counter()
            reply = await self.translate_reply(fr_reply, PIVOT, "dyu")
            timings["mt_out"] = elapsed_ms(t0)
            fallback_reason = None
            if (reason := check_translation(fr_reply, reply)) is not None:
                reply = self.fallbacks.get("generic", "dyu")
                fallback_reason = f"mt_out:{reason}"

        # On mémorise l'échange en français, même si la sortie a été remplacée :
        # le LLM garde ainsi le fil de ce qu'il a voulu dire.
        self.sessions.append(session, fr_input, fr_reply)
        return ChatResult(
            reply=reply,
            fr_input=fr_input,
            fr_reply=fr_reply,
            timings_ms=timings,
            fallback_reason=fallback_reason,
            reply_lang=effective_tgt_lang,
        )
