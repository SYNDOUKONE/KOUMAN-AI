"""Point d'entrée de l'API KOUMA AI.

Lancement :  uvicorn app.main:app --host 0.0.0.0 --port 8000
Les modèles sont chargés UNE fois, au démarrage (lifespan).
"""

from __future__ import annotations

import asyncio
import re
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import public_router, router
from app.core.config import Settings, get_settings
from app.core.errors import register_error_handlers
from app.core.logging import log_event, setup_logging
from app.core.security import ApiKeyStore, RateLimiter
from app.services.llm import build_llm
from app.services.orchestrator import ChatOrchestrator
from app.services.safety import Fallbacks
from app.services.sessions import SessionStore
from app.services.translator import build_translator

VERSION = "0.2.0"
_REQUEST_ID = re.compile(r"[A-Za-z0-9_-]{1,64}")


def _load_components(app: FastAPI, settings: Settings) -> None:
    state = app.state
    state.settings = settings
    state.key_store = ApiKeyStore(settings.api_keys_db)
    state.rate_limiter = RateLimiter(settings.rate_limit_per_minute)
    state.sessions = SessionStore(settings.session_ttl_seconds, settings.history_max_turns)
    state.translator = build_translator(settings)
    state.llm = build_llm(settings)
    state.orchestrator = ChatOrchestrator(
        translator=state.translator,
        llm=state.llm,
        sessions=state.sessions,
        fallbacks=Fallbacks(settings.fallbacks_path),
        system_prompt=settings.system_prompt_path.read_text(encoding="utf-8"),
        max_concurrent_translations=settings.max_concurrent_translations,
    )
    state.ready = True


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    setup_logging()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.ready = False
        # Chargement dans un thread : le chargement de NLLB prend du temps.
        await asyncio.to_thread(_load_components, app, settings)
        log_event(
            "demarrage",
            translator=app.state.translator.info(),
            llm=app.state.llm.name,
            langues=settings.enabled_languages,
        )
        yield

    app = FastAPI(
        title="KOUMA AI",
        description="Chatbot et traduction français ↔ dioula (pipeline MT → LLM → MT).",
        version=VERSION,
        lifespan=lifespan,
    )
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_methods=["GET", "POST"],
            allow_headers=["X-API-Key", "Content-Type"],
        )

    @app.middleware("http")
    async def request_id(request: Request, call_next):
        incoming = request.headers.get("X-Request-ID", "")
        request.state.request_id = (
            incoming if _REQUEST_ID.fullmatch(incoming) else uuid.uuid4().hex[:12]
        )
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id  # ASCII uniquement
        return response

    register_error_handlers(app)
    app.include_router(public_router)
    app.include_router(router)
    return app


app = create_app()
