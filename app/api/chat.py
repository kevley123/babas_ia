"""
Jarvis V1 - Endpoint: Chat.

POST /chat — Endpoint principal del cerebro.
"""

import logging

from fastapi import APIRouter, Depends

from app.api.dependencies import get_reasoning_engine
from app.brain.reasoning import ReasoningEngine
from app.schemas.chat import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    brain: ReasoningEngine = Depends(get_reasoning_engine),
):
    """
    Envía un mensaje al cerebro de Jarvis.

    El cerebro:
    1. Recupera memorias relevantes.
    2. Construye contexto personalizado.
    3. Consulta al LLM (DeepSeek).
    4. Extrae y almacena nueva información si es relevante.
    5. Retorna respuesta estructurada.
    """
    logger.info("POST /chat — mensaje: '%s'", request.message[:100])
    response = await brain.process_message(request.message)
    return response


@router.delete("/session")
async def clear_session(
    brain: ReasoningEngine = Depends(get_reasoning_engine),
):
    """Limpia el historial de sesión actual."""
    brain.clear_session()
    return {"message": "Historial de sesión limpiado", "success": True}
