"""
Jarvis V1 - Tests: Profile Memory.

Tests unitarios para la memoria de perfil (SQLite).
"""

import pytest
import tempfile
from pathlib import Path

from app.memory.profile_memory import ProfileMemory


@pytest.fixture
async def profile_memory():
    """Crea una instancia de ProfileMemory con DB temporal."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        memory = ProfileMemory(db_path=db_path)
        await memory.init_db()
        yield memory


@pytest.mark.asyncio
async def test_upsert_creates_entry(profile_memory):
    """upsert debe crear una nueva entrada."""
    entry = await profile_memory.upsert(
        category="nombre",
        key="nombre_completo",
        value="Rodrigo",
    )
    assert entry.category == "nombre"
    assert entry.key == "nombre_completo"
    assert entry.value == "Rodrigo"
    assert entry.id is not None


@pytest.mark.asyncio
async def test_upsert_updates_existing(profile_memory):
    """upsert debe actualizar una entrada existente con la misma key."""
    await profile_memory.upsert("nombre", "nombre_completo", "Rodrigo")
    updated = await profile_memory.upsert("nombre", "nombre_completo", "Rodrigo G.")

    assert updated.value == "Rodrigo G."

    # Debe haber solo una entrada
    entries = await profile_memory.get_all()
    assert len(entries) == 1


@pytest.mark.asyncio
async def test_get_all(profile_memory):
    """get_all debe retornar todas las entradas."""
    await profile_memory.upsert("nombre", "nombre", "Rodrigo")
    await profile_memory.upsert("interés", "tecnología", "Python")
    await profile_memory.upsert("objetivo", "carrera", "Ing. Sistemas")

    entries = await profile_memory.get_all()
    assert len(entries) == 3


@pytest.mark.asyncio
async def test_get_by_category(profile_memory):
    """get_by_category debe filtrar correctamente."""
    await profile_memory.upsert("interés", "tech1", "Python")
    await profile_memory.upsert("interés", "tech2", "FastAPI")
    await profile_memory.upsert("nombre", "nombre", "Rodrigo")

    interests = await profile_memory.get_by_category("interés")
    assert len(interests) == 2

    names = await profile_memory.get_by_category("nombre")
    assert len(names) == 1


@pytest.mark.asyncio
async def test_delete(profile_memory):
    """delete debe eliminar la entrada correcta."""
    entry = await profile_memory.upsert("nombre", "nombre", "Rodrigo")
    assert entry.id is not None

    deleted = await profile_memory.delete(entry.id)
    assert deleted is True

    entries = await profile_memory.get_all()
    assert len(entries) == 0


@pytest.mark.asyncio
async def test_delete_nonexistent(profile_memory):
    """delete de un ID inexistente debe retornar False."""
    deleted = await profile_memory.delete(9999)
    assert deleted is False


@pytest.mark.asyncio
async def test_search(profile_memory):
    """search debe encontrar entradas por texto."""
    await profile_memory.upsert("interés", "lenguaje", "Python")
    await profile_memory.upsert("interés", "framework", "FastAPI")
    await profile_memory.upsert("nombre", "nombre", "Rodrigo")

    results = await profile_memory.search("Python")
    assert len(results) == 1
    assert results[0].value == "Python"


@pytest.mark.asyncio
async def test_context_summary(profile_memory):
    """get_context_summary debe generar un resumen legible."""
    await profile_memory.upsert("nombre", "nombre", "Rodrigo")
    await profile_memory.upsert("interés", "lenguaje", "Python")

    summary = await profile_memory.get_context_summary()
    assert "Rodrigo" in summary
    assert "Python" in summary


@pytest.mark.asyncio
async def test_context_summary_empty(profile_memory):
    """get_context_summary sin datos debe indicarlo."""
    summary = await profile_memory.get_context_summary()
    assert "No hay información" in summary
