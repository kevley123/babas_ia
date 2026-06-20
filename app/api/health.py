"""
Jarvis V1 - Endpoint: Health Check.

GET /health — Estado del sistema.
"""

from datetime import datetime

from fastapi import APIRouter

from app.api.dependencies import (
    get_episodic_memory,
    get_knowledge_base,
    get_profile_memory,
    get_skill_memory,
)
from app.schemas.common import HealthResponse

router = APIRouter()

_start_time = datetime.now()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Verifica el estado del sistema y sus componentes."""
    uptime = (datetime.now() - _start_time).total_seconds()

    # Verificar componentes
    components = {
        "uptime_seconds": round(uptime, 1),
        "episodic_memories": get_episodic_memory().count(),
        "knowledge_chunks": get_knowledge_base().count(),
        "skills": len(get_skill_memory().list_skills()),
    }

    # Verificar SQLite
    try:
        profile = get_profile_memory()
        entries = await profile.get_all()
        components["profile_entries"] = len(entries)
        components["sqlite"] = "ok"
    except Exception as e:
        components["sqlite"] = f"error: {e}"

    components["chromadb"] = "ok"

    return HealthResponse(
        status="ok",
        version="1.0.0",
        service="Jarvis V1",
        components=components,
    )
