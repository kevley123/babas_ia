"""
Jarvis V1 - Schemas de Perfil.

DTOs para los endpoints de perfil.
"""

from pydantic import BaseModel, Field


class ProfileEntryCreate(BaseModel):
    """Crear o actualizar una entrada de perfil."""
    category: str = Field(
        ...,
        description="Categoría: nombre, objetivo, proyecto, interés, hábito, tecnología, otro"
    )
    key: str = Field(..., description="Clave identificadora (ej: 'nombre', 'carrera')")
    value: str = Field(..., description="Valor de la entrada")


class ProfileEntryUpdate(BaseModel):
    """Actualizar una entrada existente."""
    category: str | None = None
    key: str | None = None
    value: str | None = None


class ProfileEntryResponse(BaseModel):
    """Respuesta con una entrada de perfil."""
    id: int
    category: str
    key: str
    value: str
    created_at: str
    updated_at: str


class ProfileResponse(BaseModel):
    """Respuesta con el perfil completo."""
    entries: list[ProfileEntryResponse]
    total: int
