"""
Jarvis V1 - Endpoint: Memory (Episódica).

CRUD y búsqueda semántica para memorias episódicas.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_episodic_memory
from app.memory.episodic_memory import EpisodicMemoryStore
from app.schemas.memory import (
    MemoryEntryResponse,
    MemoryListResponse,
    MemorySearchResponse,
)
from app.schemas.common import SuccessResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=MemoryListResponse)
async def list_memories(
    limit: int = 20,
    memory: EpisodicMemoryStore = Depends(get_episodic_memory),
):
    """Lista las memorias episódicas más recientes."""
    memories = memory.get_recent(limit=limit)
    return MemoryListResponse(
        memories=[
            MemoryEntryResponse(
                id=m["id"],
                content=m["content"],
                category=m.get("category", ""),
                timestamp=m.get("timestamp", ""),
                metadata=m.get("metadata", {}),
            )
            for m in memories
        ],
        total=len(memories),
    )


@router.get("/search", response_model=MemorySearchResponse)
async def search_memories(
    q: str,
    n: int = 5,
    category: str | None = None,
    memory: EpisodicMemoryStore = Depends(get_episodic_memory),
):
    """
    Búsqueda semántica en memorias episódicas.

    Usa embeddings para encontrar memorias relevantes al query.
    """
    results = memory.search(query=q, n_results=n, category_filter=category)
    return MemorySearchResponse(
        results=[
            MemoryEntryResponse(
                id=r["id"],
                content=r["content"],
                category=r.get("category", ""),
                timestamp=r.get("timestamp", ""),
                metadata=r.get("metadata", {}),
            )
            for r in results
        ],
        query=q,
        total=len(results),
    )


@router.delete("/{memory_id}", response_model=SuccessResponse)
async def delete_memory(
    memory_id: str,
    memory: EpisodicMemoryStore = Depends(get_episodic_memory),
):
    """Elimina una memoria episódica por ID."""
    deleted = memory.delete(memory_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memoria no encontrada")

    return SuccessResponse(message=f"Memoria {memory_id} eliminada")
