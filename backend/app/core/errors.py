"""Format d'erreur JSON uniforme : {"error": {"code": ..., "message": ...}}."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class ApiError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


def _body(code: str, message: str, request: Request, details=None) -> dict:
    error = {"code": code, "message": message}
    if details is not None:
        error["details"] = details
    return {"error": error, "request_id": getattr(request.state, "request_id", None)}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(request: Request, exc: ApiError):
        return JSONResponse(
            status_code=exc.status_code, content=_body(exc.code, exc.message, request)
        )

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError):
        details = [
            {"champ": ".".join(str(p) for p in e["loc"]), "message": e["msg"]} for e in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=_body("requete_invalide", "Requête invalide.", request, details),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=_body("http_error", str(exc.detail), request),
        )

    @app.exception_handler(Exception)
    async def _unexpected(request: Request, exc: Exception):
        # Le détail part dans les logs, jamais au client.
        import logging

        logging.getLogger("kouma").exception("erreur_inattendue")
        return JSONResponse(
            status_code=500,
            content=_body("erreur_interne", "Erreur interne du serveur.", request),
        )
