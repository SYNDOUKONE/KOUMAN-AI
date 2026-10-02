"""Clients LLM interchangeables. Le LLM ne voit que du FRANÇAIS."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.core.config import Settings


class LLMClient(ABC):
    name: str = "abstract"

    @abstractmethod
    def reply(self, history_fr: list[dict], system_prompt: str) -> str:
        """history_fr : [{"role": "user"|"assistant", "content": "..."}], dernier = user."""


class StubLLM(LLMClient):
    name = "stub"

    def reply(self, history_fr: list[dict], system_prompt: str) -> str:
        last = history_fr[-1]["content"] if history_fr else ""
        return f"Réponse de test. Vous avez dit : {last}"


class GeminiLLM(LLMClient):
    name = "gemini"

    def __init__(self, settings: Settings) -> None:
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY absente : impossible d'utiliser KOUMA_LLM=gemini.")
        from google import genai
        from google.genai import types

        self._types = types
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.gemini_model

    def reply(self, history_fr: list[dict], system_prompt: str) -> str:
        types = self._types
        # Le message utilisateur reste un message séparé : jamais concaténé
        # dans la consigne système (limite l'injection de consignes).
        contents = [
            types.Content(
                role="model" if turn["role"] == "assistant" else "user",
                parts=[types.Part(text=turn["content"])],
            )
            for turn in history_fr
        ]
        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt, temperature=0.3, max_output_tokens=200
            ),
        )
        return (response.text or "").strip()


def build_llm(settings: Settings) -> LLMClient:
    if settings.llm_backend == "stub":
        return StubLLM()
    if settings.llm_backend == "gemini":
        return GeminiLLM(settings)
    raise ValueError(f"KOUMA_LLM inconnu : {settings.llm_backend!r}")
