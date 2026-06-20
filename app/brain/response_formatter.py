"""
Babas V1 - Formateador de Respuestas.

Toma el JSON parseado devuelto por el LLM y lo estructura en el
formato estándar ChatResponse.
"""

import logging

from app.schemas.chat import ChatResponse, ToolCall, UIUpdate

logger = logging.getLogger(__name__)


class ResponseFormatter:
    """Formatea respuestas estructuradas (JSON) del LLM."""

    @staticmethod
    def format(
        llm_response: dict,
        memory_types_used: list[str],
        memories_created: list[str],
    ) -> ChatResponse:
        """
        Formatea el diccionario del LLM.

        Args:
            llm_response: Diccionario extraído del JSON del LLM.
            memory_types_used: Tipos de memoria utilizados en el contexto.
            memories_created: Memorias creadas durante esta interacción.

        Returns:
            ChatResponse estructurado.
        """
        # Si hubo un error en el parseo JSON del lado de LLMService
        if "error" in llm_response:
            return ResponseFormatter.format_error(f"Invalid JSON generated: {llm_response.get('raw_response', '')[:100]}")

        # Extraer campos con fallbacks seguros
        resp_type = llm_response.get("type", "answer")
        message = llm_response.get("message", "")
        
        # Parsear tool
        tool_data = llm_response.get("tool", {})
        tool = ToolCall(
            name=tool_data.get("name", "none"),
            intent=tool_data.get("intent", "NONE"),
            params=tool_data.get("params", {})
        )
        
        # Parsear UI
        ui_data = llm_response.get("ui", {})
        ui = UIUpdate(
            avatar=ui_data.get("avatar", "neutral"),
            panels=ui_data.get("panels", ["chat"])
        )
        
        confidence = float(llm_response.get("confidence", 0.5))

        return ChatResponse(
            type=resp_type,
            message=message,
            tool=tool,
            ui=ui,
            confidence=confidence,
            memory_used=memory_types_used,
            memories_created=memories_created,
        )

    @staticmethod
    def format_error(error_message: str) -> ChatResponse:
        """Formatea una respuesta de error en el formato esperado."""
        return ChatResponse(
            type="error",
            message=f"Lo siento, ocurrió un error interno: {error_message}",
            tool=ToolCall(name="none", intent="NONE"),
            ui=UIUpdate(avatar="neutral", panels=["chat"]),
            confidence=0.0,
            memory_used=[],
            memories_created=[],
        )
