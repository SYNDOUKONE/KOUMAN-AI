"""Points d'accès de l'API."""

from __future__ import annotations

import time

from fastapi import APIRouter, Depends, Query, Request
from fastapi.security import APIKeyHeader

from app.core.errors import ApiError
from app.core.languages import LANGUAGES, PIVOT
from app.core.logging import log_event
from app.core.timing import elapsed_ms
from app.schemas import (
    ChatDebug,
    ChatRequest,
    ChatResponse,
    LanguageInfo,
    TranslateRequest,
    TranslateResponse,
)
from app.services.llm import LLMUnavailable

router = APIRouter(prefix="/api/v1")
public_router = APIRouter()

# Déclarer la clé comme schéma de sécurité (et non comme simple en-tête) :
# Swagger affiche alors un bouton « Authorize » et un cadenas sur les routes protégées.
# auto_error=False : c'est nous qui renvoyons le 401, au format d'erreur uniforme.
api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False,
    description="Clé d'API de l'application cliente (créée avec scripts/manage_keys.py).",
)


# --------------------------------------------------------------------------- #
# Dépendances                                                                 #
# --------------------------------------------------------------------------- #
def get_state(request: Request):
    state = request.app.state
    if not getattr(state, "ready", False):
        raise ApiError(503, "modele_indisponible", "Le service démarre, réessayez dans un instant.")
    return state


def require_client(request: Request, x_api_key: str | None = Depends(api_key_header)) -> str:
    state = get_state(request)
    if not state.settings.auth_enabled:
        client = "anonyme"
    else:
        client = state.key_store.lookup(x_api_key) if x_api_key else None
        if client is None:
            raise ApiError(401, "cle_invalide", "Clé d'API absente ou invalide (X-API-Key).")
    if not state.rate_limiter.allow(client):
        raise ApiError(429, "trop_de_requetes", "Trop de requêtes, réessayez dans une minute.")
    request.state.client = client
    return client


def _check_lang(state, code: str, allow_pivot: bool) -> None:
    if code == PIVOT and allow_pivot:
        return
    if code not in LANGUAGES or code == PIVOT:
        raise ApiError(422, "langue_inconnue", f"Langue inconnue : {code!r}.")
    if code not in state.settings.enabled_languages:
        raise ApiError(422, "langue_desactivee", f"Langue non activée : {code!r}.")


def _check_length(state, text: str) -> None:
    if len(text) > state.settings.max_message_chars:
        raise ApiError(
            422,
            "message_trop_long",
            f"Message trop long (max {state.settings.max_message_chars} caractères).",
        )


# --------------------------------------------------------------------------- #
# Points d'accès publics                                                       #
# --------------------------------------------------------------------------- #
@public_router.get("/health", tags=["service"])
def health(request: Request):
    state = request.app.state
    ready = getattr(state, "ready", False)
    body = {"status": "ok" if ready else "chargement", "version": request.app.version}
    if ready:
        body.update(
            translator=state.translator.info(),
            llm=state.llm.name,
            languages_enabled=state.settings.enabled_languages,
            sessions_actives=len(state.sessions),
        )
    return body


@router.get("/languages", response_model=list[LanguageInfo], tags=["service"])
def languages(request: Request):
    enabled = get_state(request).settings.enabled_languages
    return [
        LanguageInfo(code=lang.code, name=lang.name, enabled=lang.code in enabled)
        for lang in LANGUAGES.values()
        if lang.code != PIVOT
    ]


# --------------------------------------------------------------------------- #
# Points d'accès protégés                                                      #
# --------------------------------------------------------------------------- #
@router.post("/translate", response_model=TranslateResponse, tags=["traduction"])
async def translate(req: TranslateRequest, request: Request, client: str = Depends(require_client)):
    state = request.app.state
    _check_lang(state, req.src, allow_pivot=True)
    _check_lang(state, req.tgt, allow_pivot=True)
    if req.src == req.tgt or PIVOT not in (req.src, req.tgt):
        raise ApiError(422, "sens_invalide", "Seuls les sens français ↔ langue locale sont gérés.")
    _check_length(state, req.text)

    t0 = time.perf_counter()
    translation = await state.orchestrator.translate(req.text, req.src, req.tgt)
    elapsed = elapsed_ms(t0)
    log_event(
        "translate",
        request_id=request.state.request_id,
        client=client,
        sens=f"{req.src}-{req.tgt}",
        time_ms=elapsed,
    )
    return TranslateResponse(
        text=req.text, src=req.src, tgt=req.tgt, translation=translation, time_ms=elapsed
    )


@router.post("/chat", response_model=ChatResponse, response_model_exclude_none=True, tags=["chat"])
async def chat(
    req: ChatRequest,
    request: Request,
    debug: bool = Query(default=False, description="Détails internes (si autorisé par la config)"),
    client: str = Depends(require_client),
):
    state = request.app.state
    _check_lang(state, req.lang, allow_pivot=False)
    _check_length(state, req.message)

    # La session est rattachée au client : deux applis ne partagent jamais un historique.
    try:
        result = await state.orchestrator.chat(f"{client}:{req.session_id}", req.message, req.lang)
    except LLMUnavailable as exc:
        raise ApiError(
            503, "llm_indisponible", "Le service de conversation est indisponible, réessayez."
        ) from exc
    log_event(
        "chat",
        request_id=request.state.request_id,
        client=client,
        lang=req.lang,
        timings_ms=result.timings_ms,
        fallback=result.fallback_reason,
    )
    response = ChatResponse(session_id=req.session_id, lang=req.lang, reply=result.reply)
    if debug and state.settings.debug_allowed:
        response.debug = ChatDebug(
            fr_input=result.fr_input,
            fr_reply=result.fr_reply,
            timings_ms=result.timings_ms,
            fallback_reason=result.fallback_reason,
        )
    return response
