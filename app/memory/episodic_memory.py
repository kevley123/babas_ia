"""
Jarvis V1 - Memoria Episódica (ChromaDB).

Almacena experiencias y eventos del usuario con embeddings
para búsqueda semántica.

Ejemplos de memorias episódicas:
- "Terminó el módulo GPS"
- "Trabajó 3 horas en Python"
- "Resolvió un problema con su novia"
"""

import logging
import uuid
from datetime import datetime

import chromadb

logger = logging.getLogger(__name__)


class EpisodicMemoryStore:
    """Gestiona memorias episódicas en ChromaDB con búsqueda semántica."""

    COLLECTION_NAME = "episodic_memories"

    def __init__(self, chroma_path: str, embedding_function):
        """
        Args:
            chroma_path: Ruta al directorio de persistencia de ChromaDB.
            embedding_function: Función de embedding compatible con ChromaDB.
        """
        self._client = chromadb.PersistentClient(path=str(chroma_path))
        self._collection = self._client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            embedding_function=embedding_function,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            "EpisodicMemoryStore inicializado: %s (%d memorias)",
            chroma_path,
            self._collection.count(),
        )

    def add(
        self,
        content: str,
        category: str = "general",
        metadata: dict | None = None,
    ) -> str:
        """
        Agrega una nueva memoria episódica.

        Args:
            content: Texto de la memoria.
            category: Categoría (trabajo, estudio, personal, proyecto, otro).
            metadata: Metadatos adicionales opcionales.

        Returns:
            ID de la memoria creada.
        """
        memory_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        meta = {
            "category": category,
            "timestamp": now,
            **(metadata or {}),
        }

        self._collection.add(
            documents=[content],
            metadatas=[meta],
            ids=[memory_id],
        )

        logger.info(
            "Memoria episódica creada: [%s] %s (id=%s)",
            category,
            content[:80],
            memory_id,
        )
        return memory_id

    def search(
        self,
        query: str,
        n_results: int = 5,
        category_filter: str | None = None,
    ) -> list[dict]:
        """
        Búsqueda semántica de memorias.

        Args:
            query: Texto de búsqueda.
            n_results: Número máximo de resultados.
            category_filter: Filtrar por categoría (opcional).

        Returns:
            Lista de memorias relevantes con scores.
        """
        where_filter = None
        if category_filter:
            where_filter = {"category": category_filter}

        results = self._collection.query(
            query_texts=[query],
            n_results=min(n_results, self._collection.count() or 1),
            where=where_filter if where_filter and self._collection.count() > 0 else None,
        )

        memories = []
        if results and results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                meta = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 0.0
                memories.append({
                    "id": results["ids"][0][i],
                    "content": doc,
                    "category": meta.get("category", ""),
                    "timestamp": meta.get("timestamp", ""),
                    "metadata": meta,
                    "relevance_score": round(1.0 - distance, 4),  # Cosine: menor distancia = más relevante
                })

        return memories

    def get_recent(self, limit: int = 20) -> list[dict]:
        """Retorna las memorias más recientes."""
        total = self._collection.count()
        if total == 0:
            return []

        results = self._collection.get(
            limit=min(limit, total),
            include=["documents", "metadatas"],
        )

        memories = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"]):
                meta = results["metadatas"][i] if results["metadatas"] else {}
                memories.append({
                    "id": results["ids"][i],
                    "content": doc,
                    "category": meta.get("category", ""),
                    "timestamp": meta.get("timestamp", ""),
                    "metadata": meta,
                })

        # Ordenar por timestamp descendente
        memories.sort(key=lambda m: m.get("timestamp", ""), reverse=True)
        return memories

    def delete(self, memory_id: str) -> bool:
        """Elimina una memoria por ID."""
        try:
            self._collection.delete(ids=[memory_id])
            logger.info("Memoria episódica eliminada: %s", memory_id)
            return True
        except Exception as e:
            logger.error("Error al eliminar memoria %s: %s", memory_id, e)
            return False

    def count(self) -> int:
        """Retorna el número total de memorias."""
        return self._collection.count()

    def get_context_summary(self, query: str, n_results: int = 5) -> str:
        """
        Genera un resumen de memorias relevantes para inyectar como contexto.
        """
        if self._collection.count() == 0:
            return "No hay memorias episódicas registradas."

        memories = self.search(query, n_results=n_results)
        if not memories:
            return "No se encontraron memorias relevantes."

        lines = ["**Memorias relevantes:**"]
        for mem in memories:
            timestamp = mem.get("timestamp", "")[:10]  # Solo fecha
            category = mem.get("category", "")
            lines.append(f"- [{timestamp}] ({category}) {mem['content']}")

        return "\n".join(lines)
