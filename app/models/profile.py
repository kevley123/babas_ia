"""
Jarvis V1 - Modelo de dominio: Perfil del usuario.

Representa entradas de información permanente/semipermanente
sobre el usuario (nombre, objetivos, proyectos, intereses, etc.)
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ProfileEntry:
    """Una entrada individual del perfil del usuario."""

    id: int | None = None
    category: str = ""          # nombre, objetivo, proyecto, interés, hábito, tecnología, otro
    key: str = ""               # Identificador corto (ej: "nombre", "carrera")
    value: str = ""             # Valor de la entrada
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "category": self.category,
            "key": self.key,
            "value": self.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_row(cls, row: tuple) -> "ProfileEntry":
        """Crea un ProfileEntry desde una fila de SQLite."""
        return cls(
            id=row[0],
            category=row[1],
            key=row[2],
            value=row[3],
            created_at=row[4],
            updated_at=row[5],
        )
