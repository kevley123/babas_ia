"""
Jarvis V1 - Extractor de Memoria.

Analiza cada mensaje del usuario para detectar información personal
relevante que vale la pena recordar. Usa el LLM para clasificar
y extraer datos, luego los almacena en la memoria correspondiente.

Pipeline:
    Mensaje → LLM (análisis) → Clasificación → Almacenamiento
"""

import logging

from app.brain.prompts import MEMORY_EXTRACTION_PROMPT
from app.memory.profile_memory import ProfileMemory
from app.memory.episodic_memory import EpisodicMemoryStore
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class MemoryExtractor:
    """Extrae y almacena memorias automáticamente de los mensajes del usuario."""

    def __init__(
        self,
        llm_service: LLMService,
        profile_memory: ProfileMemory,
        episodic_memory: EpisodicMemoryStore,
    ):
        self._llm = llm_service
        self._profile = profile_memory
        self._episodic = episodic_memory

    async def extract_and_store(self, user_message: str) -> list[str]:
        """
        Analiza un mensaje del usuario y almacena información relevante.

        Args:
            user_message: Mensaje del usuario.

        Returns:
            Lista de descripciones de memorias creadas.
        """
        try:
            # Pedir al LLM que analice el mensaje
            prompt = MEMORY_EXTRACTION_PROMPT.format(user_message=user_message)
            messages = [
                {"role": "system", "content": "Eres un analizador de información personal. Responde SOLO con JSON válido."},
                {"role": "user", "content": prompt},
            ]

            result = self._llm.chat_json(messages=messages, temperature=0.2)

            if result.get("error"):
                logger.warning("Error en extracción de memoria: %s", result.get("error"))
                return []

            if not result.get("should_store", False):
                logger.debug("No se detectó información relevante en el mensaje")
                return []

            # Procesar extracciones
            extractions = result.get("extractions", [])
            memories_created = []

            for extraction in extractions:
                memory_type = extraction.get("memory_type", "")
                category = extraction.get("category", "otro")
                key = extraction.get("key", "")
                value = extraction.get("value", "")
                reasoning = extraction.get("reasoning", "")

                if not value:
                    continue

                if memory_type == "profile" and key:
                    # Almacenar en perfil (SQLite)
                    await self._profile.upsert(
                        category=category,
                        key=key,
                        value=value,
                    )
                    desc = f"Perfil actualizado: [{category}] {key} = {value}"
                    memories_created.append(desc)
                    logger.info("Memoria extraída (perfil): %s — %s", desc, reasoning)

                elif memory_type == "episodic":
                    # Almacenar en memoria episódica (ChromaDB)
                    self._episodic.add(
                        content=value,
                        category=category,
                    )
                    desc = f"Memoria episódica: [{category}] {value}"
                    memories_created.append(desc)
                    logger.info("Memoria extraída (episódica): %s — %s", desc, reasoning)

            if memories_created:
                logger.info(
                    "Total memorias extraídas: %d de mensaje: '%s'",
                    len(memories_created),
                    user_message[:80],
                )

            return memories_created

        except Exception as e:
            logger.error("Error en extracción de memoria: %s", e, exc_info=True)
            return []
