"""
Jarvis V1 - Schemas comunes.

DTOs compartidos por múltiples endpoints.
"""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Respuesta del endpoint /health."""
    status: str = "ok"
    version: str = "1.0.0"
    service: str = "Jarvis V1"
    components: dict = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Respuesta de error estandarizada."""
    error: str
    detail: str = ""
    status_code: int = 500


class SuccessResponse(BaseModel):
    """Respuesta genérica de éxito."""
    message: str
    success: bool = True
