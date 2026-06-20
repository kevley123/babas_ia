"""
Jarvis V1 - Modelo de dominio: Memorias.

Representa memorias episódicas (experiencias, eventos)
almacenadas en ChromaDB.
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class EpisodicMemory:
    """Una memoria episódica (experiencia/evento)."""

    id: str = ""
    content: str = ""
    category: str = ""          # trabajo, estudio, personal, proyecto, otro
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "category": self.category,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


@dataclass
class KnowledgeDocument:
    """Un documento de la base de conocimiento."""

    id: str = ""
    title: str = ""
    content: str = ""
    chunk_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "chunk_count": self.chunk_count,
            "created_at": self.created_at,
        }
