"""
Jarvis V1 - Constructor de Contexto.

Antes de cada consulta al LLM, este módulo recopila información
relevante de todas las memorias y construye un contexto personalizado.

Flujo:
    1. Buscar en perfil (SQLite)
    2. Buscar memorias episódicas relevantes (ChromaDB)
    3. Buscar en base de conocimiento (ChromaDB)
    4. Buscar skills relacionados (YAML)
    5. Consolidar en un bloque de contexto
"""

import logging

from app.brain.prompts import CONTEXT_TEMPLATE
from app.memory.profile_memory import ProfileMemory
from app.memory.episodic_memory import EpisodicMemoryStore
from app.memory.knowledge_base import KnowledgeBase
from app.memory.skill_memory import SkillMemory

logger = logging.getLogger(__name__)


class ContextBuilder:
    """Construye contexto personalizado para el LLM."""

    def __init__(
        self,
        profile_memory: ProfileMemory,
        episodic_memory: EpisodicMemoryStore,
        knowledge_base: KnowledgeBase,
        skill_memory: SkillMemory,
        max_memories: int = 5,
        max_documents: int = 3,
    ):
        self._profile = profile_memory
        self._episodic = episodic_memory
        self._knowledge = knowledge_base
        self._skills = skill_memory
        self._max_memories = max_memories
        self._max_documents = max_documents

    async def build_context(self, user_message: str) -> tuple[str, list[str]]:
        """
        Construye el contexto completo para una consulta.

        Args:
            user_message: Mensaje del usuario para buscar contexto relevante.

        Returns:
            Tupla de (contexto_formateado, lista_de_tipos_de_memoria_usados).
        """
        memory_types_used = []

        # 1. Contexto del perfil (siempre incluir)
        try:
            profile_context = await self._profile.get_context_summary()
            if profile_context and "No hay información" not in profile_context:
                memory_types_used.append("profile")
        except Exception as e:
            logger.error("Error obteniendo contexto de perfil: %s", e)
            profile_context = ""

        # 2. Memorias episódicas relevantes
        try:
            episodic_context = self._episodic.get_context_summary(
                query=user_message,
                n_results=self._max_memories,
            )
            if episodic_context and "No hay memorias" not in episodic_context and "No se encontraron" not in episodic_context:
                memory_types_used.append("episodic")
        except Exception as e:
            logger.error("Error obteniendo contexto episódico: %s", e)
            episodic_context = ""

        # 3. Conocimiento documental
        try:
            knowledge_context = self._knowledge.get_context_summary(
                query=user_message,
                n_results=self._max_documents,
            )
            if knowledge_context:
                memory_types_used.append("knowledge")
        except Exception as e:
            logger.error("Error obteniendo contexto de conocimiento: %s", e)
            knowledge_context = ""

        # 4. Skills relevantes
        try:
            skills_context = self._skills.get_context_summary(query=user_message)
            if skills_context:
                memory_types_used.append("skills")
        except Exception as e:
            logger.error("Error obteniendo contexto de skills: %s", e)
            skills_context = ""

        # Construir contexto consolidado
        context = CONTEXT_TEMPLATE.format(
            profile_context=profile_context or "Sin información de perfil.",
            episodic_context=episodic_context or "",
            knowledge_context=knowledge_context or "",
            skills_context=skills_context or "",
        )

        # Limpiar líneas vacías excesivas
        lines = context.split("\n")
        cleaned = []
        prev_empty = False
        for line in lines:
            if not line.strip():
                if not prev_empty:
                    cleaned.append(line)
                prev_empty = True
            else:
                cleaned.append(line)
                prev_empty = False
        context = "\n".join(cleaned)

        logger.debug(
            "Contexto construido: %d chars, memorias usadas: %s",
            len(context),
            memory_types_used,
        )

        return context, memory_types_used
