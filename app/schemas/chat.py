"""
Jarvis V1 - Schemas de Chat.

DTOs para el endpoint principal POST /chat.
"""

from typing import Any
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Mensaje del usuario al cerebro."""
    message: str = Field(..., min_length=1, max_length=5000, description="Mensaje del usuario")


class ToolCall(BaseModel):
    """Estructura de llamada a herramienta."""
    name: str = Field(..., description="Nombre de la herramienta (ej. music, memory, tasks, none)")
    intent: str = Field(..., description="Intención o acción a realizar")
    params: dict[str, Any] = Field(default_factory=dict, description="Parámetros de la acción")


class UIUpdate(BaseModel):
    """Estructura para actualizar la interfaz del cliente."""
    avatar: str = Field(default="neutral", description="Estado de ánimo del avatar (happy, thinking, focused, neutral, excited)")
    panels: list[str] = Field(default_factory=list, description="Paneles activos (music, tasks, chat, memory)")


class ChatResponse(BaseModel):
    """Respuesta estructurada del cerebro (Agente)."""
    type: str = Field(
        default="answer",
        description="Tipo de respuesta: tool_call, answer, ui_update"
    )
    message: str = Field(..., description="Explicación corta natural para el usuario")
    tool: ToolCall = Field(..., description="Detalles de la herramienta a invocar")
    ui: UIUpdate = Field(..., description="Actualizaciones de la UI")
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Nivel de confianza de la respuesta"
    )
    
    # Metadatos internos (opcionales para el frontend, pero útiles para debugging)
    memory_used: list[str] = Field(
        default_factory=list,
        description="Tipos de memoria utilizados (profile, episodic, knowledge, skills)"
    )
    memories_created: list[str] = Field(
        default_factory=list,
        description="Descripciones de memorias creadas a partir de este mensaje"
    )
