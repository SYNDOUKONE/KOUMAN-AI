"""Clients LLM interchangeables. Le LLM ne voit que du FRANÇAIS."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.core.config import Settings

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class LLMUnavailable(Exception):
    """Le LLM n'a pas pu répondre (panne, quota, réseau...). Traduite en HTTP 503 par l'API."""


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
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt, temperature=0.3, max_output_tokens=200
                ),
            )
        except Exception as exc:
            raise LLMUnavailable(f"Gemini indisponible : {exc}") from exc

        # Gemini peut bloquer la réponse via les filtres de sécurité :
        # dans ce cas response.text lève une exception interne.
        # On récupère le texte de façon défensive.
        try:
            text = response.text
        except Exception:
            text = None

        if not text:
            # Tenter de récupérer le texte depuis les candidates directement
            try:
                text = response.candidates[0].content.parts[0].text
            except Exception:
                text = None

        if not text:
            finish_reason = "inconnu"
            try:
                finish_reason = str(response.candidates[0].finish_reason)
            except Exception:
                pass
            raise LLMUnavailable(
                f"Gemini a retourné une réponse vide (finish_reason={finish_reason}). "
                "Essayez de reformuler votre message."
            )

        return text.strip()


class OpenRouterLLM(LLMClient):
    name = "openrouter"

    def __init__(self, settings: Settings) -> None:
        if not settings.openrouter_api_key:
            raise RuntimeError(
                "OPENROUTER_API_KEY absente : impossible d'utiliser KOUMA_LLM=openrouter."
            )

        # Import ici, pas en tête de fichier : l'API et les tests doivent démarrer
        # sans le paquet `openai` tant qu'on n'utilise pas OpenRouter.
        from openai import OpenAI

        self.client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url=OPENROUTER_BASE_URL,
            timeout=settings.llm_timeout_seconds,
            max_retries=0,
        )
        self.model = settings.openrouter_model
        self.max_tokens = settings.llm_max_tokens

    def reply(
        self,
        history_fr: list[dict],
        system_prompt: str,
    ) -> str:

        messages = [
            {
                "role": "system",
                "content": system_prompt,
            }
        ]

        messages.extend(
            {
                "role": turn["role"],
                "content": turn["content"],
            }
            for turn in history_fr
        )

        # Utiliser max_tokens (norme OpenAI/OpenRouter) pour éviter que le fournisseur
        # ne réserve les crédits sur le contexte max du modèle (64k tokens)
        kwargs = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
        }

        try:
            response = self.client.chat.completions.create(**kwargs)
        except Exception as exc:
            # Si le modèle exige max_completion_tokens (ex: modèles o1/o3)
            err_str = str(exc)
            if "max_completion_tokens" in err_str:
                kwargs.pop("max_tokens", None)
                kwargs["max_completion_tokens"] = self.max_tokens
                try:
                    response = self.client.chat.completions.create(**kwargs)
                except Exception as exc2:
                    raise LLMUnavailable(f"OpenRouter indisponible : {exc2}") from exc2
            else:
                raise LLMUnavailable(f"OpenRouter indisponible : {exc}") from exc

        content = response.choices[0].message.content

        if not content:
            raise LLMUnavailable("OpenRouter a retourné une réponse vide.")

        return content.strip()


class GroqLLM(LLMClient):
    name = "groq"

    def __init__(self, settings: Settings) -> None:
        if not settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY absente : impossible d'utiliser Groq.")
        from openai import OpenAI

        self.client = OpenAI(
            api_key=settings.groq_api_key,
            base_url="https://api.groq.com/openai/v1",
            timeout=settings.llm_timeout_seconds,
            max_retries=1,
        )
        self.model = settings.groq_model
        self.max_tokens = min(settings.llm_max_tokens, 500)

    def reply(
        self,
        history_fr: list[dict],
        system_prompt: str,
    ) -> str:
        messages = [
            {
                "role": "system",
                "content": system_prompt,
            }
        ]
        messages.extend(
            {
                "role": turn["role"],
                "content": turn["content"],
            }
            for turn in history_fr
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
            )
        except Exception as exc:
            raise LLMUnavailable(f"Groq indisponible : {exc}") from exc

        content = response.choices[0].message.content
        if not content:
            raise LLMUnavailable("Groq a retourné une réponse vide.")

        return content.strip()


class FallbackChainLLM(LLMClient):
    """Enchaîne plusieurs fournisseurs LLM avec bascule automatique transparente."""

    name = "cascade"

    def __init__(self, clients: list[LLMClient]) -> None:
        if not clients:
            raise ValueError("Au moins un client LLM est requis pour la chaîne de bascule.")
        self.clients = clients
        self.active_client = clients[0]

    @property
    def model(self) -> str:
        return getattr(self.active_client, "model", self.active_client.name)

    def reply(self, history_fr: list[dict], system_prompt: str) -> str:
        import logging
        log = logging.getLogger("kouma")
        errors = []
        for idx, client in enumerate(self.clients):
            try:
                res = client.reply(history_fr, system_prompt)
                if res:
                    self.active_client = client
                    if idx > 0:
                        log.info(
                            "Bascule automatique réussie sur le LLM de secours : %s (%s)",
                            client.name,
                            getattr(client, "model", ""),
                        )
                    return res
            except Exception as exc:
                err_msg = f"{client.name} ({getattr(client, 'model', '')}): {exc}"
                log.warning("Échec LLM %s -> Bascule sur le modèle de secours...", err_msg)
                errors.append(err_msg)
                continue

        raise LLMUnavailable(f"Tous les fournisseurs LLM ont échoué : {' | '.join(errors)}")


def build_llm(settings: Settings) -> LLMClient:
    if settings.llm_backend == "stub":
        return StubLLM()

    # Initialisation des différents clients disponibles selon les clés présentes
    available_clients: dict[str, LLMClient] = {}

    if settings.openrouter_api_key:
        try:
            available_clients["openrouter"] = OpenRouterLLM(settings)
        except Exception:
            pass

    if settings.groq_api_key:
        try:
            available_clients["groq"] = GroqLLM(settings)
        except Exception:
            pass

    if settings.gemini_api_key:
        try:
            available_clients["gemini"] = GeminiLLM(settings)
        except Exception:
            pass

    if not available_clients:
        return StubLLM()

    # Déterminer la priorité de bascule
    primary = settings.llm_backend
    ordered_clients = []
    if primary in available_clients:
        ordered_clients.append(available_clients[primary])

    for k, cl in available_clients.items():
        if cl not in ordered_clients:
            ordered_clients.append(cl)

    if len(ordered_clients) == 1:
        return ordered_clients[0]

    return FallbackChainLLM(ordered_clients)
