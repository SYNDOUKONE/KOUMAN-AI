"""Points d'accès de l'API."""

from __future__ import annotations

import base64
import time

from fastapi import APIRouter, Depends, File, Form, Query, Request, Response, UploadFile
from fastapi.security import APIKeyHeader

from app.core.errors import ApiError
from app.core.languages import LANGUAGES, PIVOT
from app.core.logging import log_event
from app.core.timing import elapsed_ms
from app.schemas import (
    AudioSynthesizeRequest,
    AudioSynthesizeResponse,
    AudioTranscribeResponse,
    ChatDebug,
    ChatRequest,
    ChatResponse,
    LanguageInfo,
    TranslateRequest,
    TranslateResponse,
    VoiceChatResponse,
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
    if code not in LANGUAGES:
        raise ApiError(422, "langue_inconnue", f"Langue inconnue : {code!r}.")
    if code == PIVOT and not allow_pivot:
        raise ApiError(422, "langue_invalide", "Cette opération nécessite une langue locale (ex: 'dyu').")
    if code != PIVOT and code not in state.settings.enabled_languages:
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
            llm_model=getattr(state.llm, "model", None),
            audio=getattr(state, "audio", None) and state.audio.info(),
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
    _check_lang(state, req.lang, allow_pivot=True)
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


# --------------------------------------------------------------------------- #
# Points d'accès Audio (TTS, STT & Voice Chat)                                 #
# --------------------------------------------------------------------------- #
@router.post("/audio/synthesize", response_model=AudioSynthesizeResponse, tags=["audio"])
async def audio_synthesize(
    req: AudioSynthesizeRequest,
    request: Request,
    format: str = Query(
        default="base64",
        description="Format de retour : 'base64' (JSON) ou 'wav' (flux audio/wav binaire)",
    ),
    client: str = Depends(require_client),
):
    """Synthèse vocale (TTS) Dioula via Meta MMS-TTS avec modulation de vitesse."""
    state = request.app.state
    _check_lang(state, req.lang, allow_pivot=False)
    _check_length(state, req.text)

    t0 = time.perf_counter()
    wav_bytes, duration_s, sr = await state.audio.text_to_speech(
        req.text, speaking_rate=req.speaking_rate
    )
    elapsed = elapsed_ms(t0)

    log_event(
        "audio_synthesize",
        request_id=request.state.request_id,
        client=client,
        lang=req.lang,
        speaking_rate=req.speaking_rate,
        duration_s=duration_s,
        time_ms=elapsed,
    )

    if format == "wav" or request.headers.get("accept") == "audio/wav":
        return Response(content=wav_bytes, media_type="audio/wav")

    return AudioSynthesizeResponse(
        text=req.text,
        lang=req.lang,
        speaking_rate=req.speaking_rate,
        audio_base64=base64.b64encode(wav_bytes).decode("ascii"),
        sampling_rate=sr,
        duration_s=duration_s,
        time_ms=elapsed,
    )


@router.post("/audio/transcribe", response_model=AudioTranscribeResponse, tags=["audio"])
async def audio_transcribe(
    request: Request,
    file: UploadFile = File(..., description="Fichier audio WAV, MP3 ou OGG"),
    lang: str = Query(default="dyu", description="Langue de transcription"),
    client: str = Depends(require_client),
):
    """Reconnaissance vocale (STT) Dioula via Whisper Dioula (16 kHz mono)."""
    state = request.app.state
    _check_lang(state, lang, allow_pivot=False)

    audio_bytes = await file.read()
    if not audio_bytes:
        raise ApiError(422, "audio_vide", "Le fichier audio fourni est vide.")

    t0 = time.perf_counter()
    text = await state.audio.speech_to_text(audio_bytes, filename=file.filename or "audio.wav")
    elapsed = elapsed_ms(t0)

    log_event(
        "audio_transcribe",
        request_id=request.state.request_id,
        client=client,
        lang=lang,
        filename=file.filename,
        time_ms=elapsed,
    )
    return AudioTranscribeResponse(text=text, lang=lang, time_ms=elapsed)


@router.post(
    "/chat/voice",
    response_model=VoiceChatResponse,
    response_model_exclude_none=True,
    tags=["chat", "audio"],
)
async def chat_voice(
    request: Request,
    session_id: str = Form(..., description="Identifiant de session de conversation"),
    lang: str = Form(default="dyu", description="Langue de conversation"),
    speaking_rate: float = Form(
        default=0.75, description="Vitesse TTS (<1.0 = plus lent, 1.0 = normal)"
    ),
    file: UploadFile = File(..., description="Fichier audio parlé par l'utilisateur"),
    debug: bool = Query(default=False, description="Détails internes si autorisés"),
    client: str = Depends(require_client),
):
    """Pipeline multimodal complet : Audio parlé Dioula -> STT -> LLM -> TTS audio Dioula."""
    state = request.app.state
    _check_lang(state, lang, allow_pivot=False)

    audio_bytes = await file.read()
    if not audio_bytes:
        raise ApiError(422, "audio_vide", "Le fichier audio fourni est vide.")

    timings = {}
    total_t0 = time.perf_counter()

    # 1. Reconnaissance vocale (STT)
    t0 = time.perf_counter()
    user_transcript = await state.audio.speech_to_text(
        audio_bytes, filename=file.filename or "audio.wav"
    )
    timings["stt"] = elapsed_ms(t0)

    if not user_transcript:
        raise ApiError(422, "audio_inintelligible", "Impossible de transcrire l'audio envoyé.")

    # 2. Pipeline conversationnel (dyu -> fr -> LLM -> fr -> dyu)
    try:
        chat_result = await state.orchestrator.chat(
            f"{client}:{session_id}", user_transcript, lang
        )
    except LLMUnavailable as exc:
        raise ApiError(
            503, "llm_indisponible", "Le service de conversation est indisponible, réessayez."
        ) from exc
    timings.update(chat_result.timings_ms)

    # 3. Synthèse vocale de la réponse dioula (TTS)
    t0 = time.perf_counter()
    wav_bytes, duration_s, _ = await state.audio.text_to_speech(
        chat_result.reply, speaking_rate=speaking_rate
    )
    timings["tts"] = elapsed_ms(t0)
    timings["total"] = elapsed_ms(total_t0)

    log_event(
        "chat_voice",
        request_id=request.state.request_id,
        client=client,
        lang=lang,
        timings_ms=timings,
        fallback=chat_result.fallback_reason,
    )

    response = VoiceChatResponse(
        session_id=session_id,
        lang=lang,
        user_transcript=user_transcript,
        reply_text=chat_result.reply,
        audio_base64=base64.b64encode(wav_bytes).decode("ascii"),
        timings_ms=timings,
    )
    if debug and state.settings.debug_allowed:
        response.debug = ChatDebug(
            fr_input=chat_result.fr_input,
            fr_reply=chat_result.fr_reply,
            timings_ms=timings,
            fallback_reason=chat_result.fallback_reason,
        )
    return response
