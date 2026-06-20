"""
Jarvis V1 - Dependency Injection centralizado.

Define funciones get_*() que FastAPI inyecta via Depends().
Usa singletons para componentes que deben tener una sola instancia.
"""

import logging
from functools import lru_cache

from app.config import get_settings
from app.services.embedding_service import get_embedding_function
from app.services.llm_service import LLMService
from app.memory.profile_memory import ProfileMemory
from app.memory.episodic_memory import EpisodicMemoryStore
from app.memory.knowledge_base import KnowledgeBase
from app.memory.skill_memory import SkillMemory
from app.brain.context_builder import ContextBuilder
from app.brain.memory_extractor import MemoryExtractor
from app.brain.reasoning import ReasoningEngine
from app.core.scheduler import SchedulerEngine

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
# Servicios base (singletons)
# ═══════════════════════════════════════════════════════════════════

@lru_cache(maxsize=1)
def get_scheduler_engine() -> SchedulerEngine:
    """Retorna el motor de automatizaciones (singleton)."""
    return SchedulerEngine()

@lru_cache(maxsize=1)
def get_llm_service() -> LLMService:
    """Retorna el servicio LLM (singleton)."""
    settings = get_settings()
    return LLMService(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        model=settings.deepseek_model,
    )


# ═══════════════════════════════════════════════════════════════════
# Memorias (singletons)
# ═══════════════════════════════════════════════════════════════════

@lru_cache(maxsize=1)
def get_profile_memory() -> ProfileMemory:
    """Retorna la memoria de perfil (singleton)."""
    settings = get_settings()
    return ProfileMemory(db_path=settings.db_path)


@lru_cache(maxsize=1)
def get_episodic_memory() -> EpisodicMemoryStore:
    """Retorna la memoria episódica (singleton)."""
    settings = get_settings()
    embedding_fn = get_embedding_function(settings.embedding_model)
    return EpisodicMemoryStore(
        chroma_path=str(settings.episodic_path),
        embedding_function=embedding_fn,
    )


@lru_cache(maxsize=1)
def get_knowledge_base() -> KnowledgeBase:
    """Retorna la base de conocimiento (singleton)."""
    settings = get_settings()
    embedding_fn = get_embedding_function(settings.embedding_model)
    return KnowledgeBase(
        chroma_path=str(settings.knowledge_vector_path),
        embedding_function=embedding_fn,
    )


@lru_cache(maxsize=1)
def get_skill_memory() -> SkillMemory:
    """Retorna la memoria de skills (singleton)."""
    settings = get_settings()
    return SkillMemory(skills_dir=settings.skills_dir)


# ═══════════════════════════════════════════════════════════════════
# Cerebro (singleton)
# ═══════════════════════════════════════════════════════════════════

@lru_cache(maxsize=1)
def get_context_builder() -> ContextBuilder:
    """Retorna el constructor de contexto (singleton)."""
    settings = get_settings()
    return ContextBuilder(
        profile_memory=get_profile_memory(),
        episodic_memory=get_episodic_memory(),
        knowledge_base=get_knowledge_base(),
        skill_memory=get_skill_memory(),
        max_memories=settings.context_max_memories,
        max_documents=settings.context_max_documents,
    )


@lru_cache(maxsize=1)
def get_memory_extractor() -> MemoryExtractor:
    """Retorna el extractor de memoria (singleton)."""
    return MemoryExtractor(
        llm_service=get_llm_service(),
        profile_memory=get_profile_memory(),
        episodic_memory=get_episodic_memory(),
    )


@lru_cache(maxsize=1)
def get_reasoning_engine() -> ReasoningEngine:
    """Retorna el motor de razonamiento (singleton)."""
    settings = get_settings()
    return ReasoningEngine(
        llm_service=get_llm_service(),
        context_builder=get_context_builder(),
        memory_extractor=get_memory_extractor(),
        max_session_history=settings.max_session_history,
    )
