"""
Jarvis V1 - Endpoint: Profile.

CRUD para la memoria de perfil del usuario.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_profile_memory
from app.memory.profile_memory import ProfileMemory
from app.schemas.profile import (
    ProfileEntryCreate,
    ProfileEntryResponse,
    ProfileResponse,
)
from app.schemas.common import SuccessResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=ProfileResponse)
async def get_profile(
    category: str | None = None,
    memory: ProfileMemory = Depends(get_profile_memory),
):
    """
    Retorna el perfil del usuario.

    Opcionalmente filtra por categoría:
    nombre, objetivo, proyecto, interés, hábito, tecnología, otro.
    """
    if category:
        entries = await memory.get_by_category(category)
    else:
        entries = await memory.get_all()

    return ProfileResponse(
        entries=[
            ProfileEntryResponse(**e.to_dict())
            for e in entries
        ],
        total=len(entries),
    )


@router.put("", response_model=ProfileEntryResponse)
async def upsert_profile(
    entry: ProfileEntryCreate,
    memory: ProfileMemory = Depends(get_profile_memory),
):
    """
    Crea o actualiza una entrada del perfil.

    Si ya existe una entrada con la misma categoría y clave,
    se actualiza el valor. Si no, se crea una nueva.
    """
    result = await memory.upsert(
        category=entry.category,
        key=entry.key,
        value=entry.value,
    )
    logger.info("PUT /profile — %s.%s = %s", entry.category, entry.key, entry.value)
    return ProfileEntryResponse(**result.to_dict())


@router.delete("/{entry_id}", response_model=SuccessResponse)
async def delete_profile_entry(
    entry_id: int,
    memory: ProfileMemory = Depends(get_profile_memory),
):
    """Elimina una entrada del perfil por ID."""
    deleted = await memory.delete(entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Entrada no encontrada")

    return SuccessResponse(message=f"Entrada {entry_id} eliminada")


@router.get("/search", response_model=ProfileResponse)
async def search_profile(
    q: str,
    memory: ProfileMemory = Depends(get_profile_memory),
):
    """Busca en el perfil por texto."""
    entries = await memory.search(q)
    return ProfileResponse(
        entries=[
            ProfileEntryResponse(**e.to_dict())
            for e in entries
        ],
        total=len(entries),
    )
