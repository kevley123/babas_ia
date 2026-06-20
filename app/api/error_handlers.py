"""
Jarvis V1 - Manejadores de errores globales.

Captura excepciones no controladas y las convierte en
respuestas HTTP estandarizadas.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from openai import APIError, AuthenticationError

logger = logging.getLogger(__name__)


def register_error_handlers(app: FastAPI) -> None:
    """Registra manejadores de errores globales en la app FastAPI."""

    @app.exception_handler(AuthenticationError)
    async def auth_error_handler(request: Request, exc: AuthenticationError):
        logger.error("Error de autenticación con DeepSeek API: %s", exc)
        return JSONResponse(
            status_code=503,
            content={
                "error": "llm_auth_error",
                "detail": "Error de autenticación con el servicio LLM. Verifica tu API key.",
                "status_code": 503,
            },
        )

    @app.exception_handler(APIError)
    async def api_error_handler(request: Request, exc: APIError):
        logger.error("Error del API LLM: %s", exc)
        return JSONResponse(
            status_code=503,
            content={
                "error": "llm_api_error",
                "detail": f"Error del servicio LLM: {str(exc)}",
                "status_code": 503,
            },
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        logger.warning("Error de validación: %s", exc)
        return JSONResponse(
            status_code=400,
            content={
                "error": "validation_error",
                "detail": str(exc),
                "status_code": 400,
            },
        )

    @app.exception_handler(Exception)
    async def general_error_handler(request: Request, exc: Exception):
        logger.error("Error no controlado: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "detail": "Error interno del servidor. Revisa los logs para más detalles.",
                "status_code": 500,
            },
        )
