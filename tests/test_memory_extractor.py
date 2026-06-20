"""
Jarvis V1 - Tests: Memory Extractor.

Tests del extractor de memoria con respuestas LLM mockeadas.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from app.brain.memory_extractor import MemoryExtractor
from app.memory.profile_memory import ProfileMemory
from app.memory.episodic_memory import EpisodicMemoryStore


class MockLLMService:
    """Mock del servicio LLM para testing."""

    def __init__(self, response: dict):
        self._response = response

    def chat_json(self, **kwargs) -> dict:
        return self._response


def _mock_embedding_fn():
    """Crea una función de embedding mock para ChromaDB."""
    class MockEmbedding:
        def __call__(self, input):
            # Retorna embeddings falsos de 384 dimensiones
            return [[0.1] * 384 for _ in input]

        def name(self):
            return "default"
    return MockEmbedding()


@pytest.fixture
async def extractor_with_profile_response():
    """Extractor configurado con respuesta LLM que extrae perfil."""
    llm_response = {
        "should_store": True,
        "extractions": [
            {
                "memory_type": "profile",
                "category": "nombre",
                "key": "nombre_completo",
                "value": "Rodrigo",
                "reasoning": "El usuario mencionó su nombre",
            }
        ],
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        profile = ProfileMemory(db_path=db_path)
        await profile.init_db()

        chroma_path = Path(tmpdir) / "chroma"
        episodic = EpisodicMemoryStore(
            chroma_path=str(chroma_path),
            embedding_function=_mock_embedding_fn(),
        )

        extractor = MemoryExtractor(
            llm_service=MockLLMService(llm_response),
            profile_memory=profile,
            episodic_memory=episodic,
        )

        yield extractor, profile


@pytest.fixture
async def extractor_with_no_store_response():
    """Extractor configurado con respuesta LLM que no almacena nada."""
    llm_response = {
        "should_store": False,
        "extractions": [],
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        profile = ProfileMemory(db_path=db_path)
        await profile.init_db()

        chroma_path = Path(tmpdir) / "chroma"
        episodic = EpisodicMemoryStore(
            chroma_path=str(chroma_path),
            embedding_function=_mock_embedding_fn(),
        )

        extractor = MemoryExtractor(
            llm_service=MockLLMService(llm_response),
            profile_memory=profile,
            episodic_memory=episodic,
        )

        yield extractor


@pytest.mark.asyncio
async def test_extract_profile_info(extractor_with_profile_response):
    """Debe extraer y almacenar información de perfil."""
    extractor, profile = extractor_with_profile_response

    memories = await extractor.extract_and_store("Me llamo Rodrigo")
    assert len(memories) == 1
    assert "Perfil actualizado" in memories[0]

    # Verificar que se guardó en SQLite
    entries = await profile.get_all()
    assert len(entries) == 1
    assert entries[0].value == "Rodrigo"


@pytest.mark.asyncio
async def test_no_store_trivial_message(extractor_with_no_store_response):
    """No debe almacenar nada para mensajes triviales."""
    extractor = extractor_with_no_store_response

    memories = await extractor.extract_and_store("Hola, ¿cómo estás?")
    assert len(memories) == 0
