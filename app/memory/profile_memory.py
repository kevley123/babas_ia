"""
Jarvis V1 - Memoria de Perfil (SQLite).

Almacena información permanente/semipermanente sobre el usuario:
nombre, objetivos, proyectos, intereses, tecnologías, hábitos, etc.

Operaciones CRUD async usando aiosqlite.
"""

import logging
from datetime import datetime
from pathlib import Path

import aiosqlite

from app.models.profile import ProfileEntry

logger = logging.getLogger(__name__)

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS profile_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(category, key)
)
"""

CREATE_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_profile_category ON profile_entries(category)
"""


class ProfileMemory:
    """Gestiona la memoria de perfil del usuario en SQLite."""

    def __init__(self, db_path: Path):
        self._db_path = db_path
        logger.debug("ProfileMemory inicializado: %s", db_path)

    def _connect(self) -> aiosqlite.Connection:
        """Crea una nueva conexión a la base de datos (usar como async context manager)."""
        return aiosqlite.connect(str(self._db_path))

    async def init_db(self) -> None:
        """Crea la tabla de perfil si no existe."""
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            await db.execute(CREATE_TABLE_SQL)
            await db.execute(CREATE_INDEX_SQL)
            await db.commit()
        logger.info("Tabla profile_entries lista")

    async def get_all(self) -> list[ProfileEntry]:
        """Retorna todas las entradas del perfil."""
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT id, category, key, value, created_at, updated_at "
                "FROM profile_entries ORDER BY category, key"
            )
            rows = await cursor.fetchall()
            return [ProfileEntry.from_row(tuple(row)) for row in rows]

    async def get_by_category(self, category: str) -> list[ProfileEntry]:
        """Retorna entradas filtradas por categoría."""
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT id, category, key, value, created_at, updated_at "
                "FROM profile_entries WHERE category = ? ORDER BY key",
                (category,),
            )
            rows = await cursor.fetchall()
            return [ProfileEntry.from_row(tuple(row)) for row in rows]

    async def get_by_id(self, entry_id: int) -> ProfileEntry | None:
        """Retorna una entrada por su ID."""
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT id, category, key, value, created_at, updated_at "
                "FROM profile_entries WHERE id = ?",
                (entry_id,),
            )
            row = await cursor.fetchone()
            if row:
                return ProfileEntry.from_row(tuple(row))
            return None

    async def upsert(self, category: str, key: str, value: str) -> ProfileEntry:
        """
        Inserta o actualiza una entrada de perfil.

        Si ya existe una entrada con la misma categoría y clave,
        actualiza el valor. Si no, crea una nueva.
        """
        now = datetime.now().isoformat()

        async with self._connect() as db:
            db.row_factory = aiosqlite.Row

            # Intentar encontrar existente
            cursor = await db.execute(
                "SELECT id FROM profile_entries WHERE category = ? AND key = ?",
                (category, key),
            )
            existing = await cursor.fetchone()

            if existing:
                # Actualizar
                await db.execute(
                    "UPDATE profile_entries SET value = ?, updated_at = ? "
                    "WHERE category = ? AND key = ?",
                    (value, now, category, key),
                )
                logger.info("Perfil actualizado: [%s] %s = %s", category, key, value)
            else:
                # Insertar
                await db.execute(
                    "INSERT INTO profile_entries (category, key, value, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (category, key, value, now, now),
                )
                logger.info("Perfil creado: [%s] %s = %s", category, key, value)

            await db.commit()

            # Retornar la entrada actualizada/creada
            cursor = await db.execute(
                "SELECT id, category, key, value, created_at, updated_at "
                "FROM profile_entries WHERE category = ? AND key = ?",
                (category, key),
            )
            row = await cursor.fetchone()
            return ProfileEntry.from_row(tuple(row))

    async def delete(self, entry_id: int) -> bool:
        """Elimina una entrada por ID. Retorna True si existía."""
        async with self._connect() as db:
            cursor = await db.execute(
                "DELETE FROM profile_entries WHERE id = ?",
                (entry_id,),
            )
            await db.commit()
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info("Perfil eliminado: id=%d", entry_id)
            return deleted

    async def search(self, query: str) -> list[ProfileEntry]:
        """Búsqueda textual simple en valores del perfil."""
        async with self._connect() as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT id, category, key, value, created_at, updated_at "
                "FROM profile_entries WHERE value LIKE ? OR key LIKE ? "
                "ORDER BY updated_at DESC",
                (f"%{query}%", f"%{query}%"),
            )
            rows = await cursor.fetchall()
            return [ProfileEntry.from_row(tuple(row)) for row in rows]

    async def get_context_summary(self) -> str:
        """
        Genera un resumen del perfil para inyectar como contexto al LLM.
        """
        entries = await self.get_all()
        if not entries:
            return "No hay información de perfil registrada."

        # Agrupar por categoría
        categories: dict[str, list[str]] = {}
        for entry in entries:
            cat = entry.category
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(f"- {entry.key}: {entry.value}")

        lines = []
        for cat, items in categories.items():
            lines.append(f"**{cat.capitalize()}:**")
            lines.extend(items)
            lines.append("")

        return "\n".join(lines)
