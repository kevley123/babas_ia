"""
Jarvis V1 - Base de Conocimiento (ChromaDB + archivos).

RAG documental: permite subir documentos de texto, los divide en chunks,
genera embeddings, y permite búsqueda semántica sobre ellos.
"""

import logging
import uuid
from datetime import datetime

import chromadb

logger = logging.getLogger(__name__)

# Tamaño de chunk y overlap en caracteres
CHUNK_SIZE = 1500       # ~375 tokens aprox
CHUNK_OVERLAP = 200     # ~50 tokens overlap


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Divide un texto en chunks con overlap.

    Args:
        text: Texto completo a dividir.
        chunk_size: Tamaño máximo de cada chunk en caracteres.
        overlap: Caracteres de overlap entre chunks consecutivos.

    Returns:
        Lista de chunks de texto.
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size

        # Intentar cortar en un salto de línea o punto
        if end < len(text):
            # Buscar el último salto de línea o punto en el rango
            last_break = text.rfind("\n", start + chunk_size // 2, end)
            if last_break == -1:
                last_break = text.rfind(". ", start + chunk_size // 2, end)
            if last_break != -1:
                end = last_break + 1

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - overlap

    return chunks


class KnowledgeBase:
    """Gestiona la base de conocimiento con RAG documental."""

    COLLECTION_NAME = "knowledge_base"

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
            "KnowledgeBase inicializada: %s (%d chunks)",
            chroma_path,
            self._collection.count(),
        )

    def ingest_text(self, title: str, content: str) -> dict:
        """
        Ingesta un documento de texto: lo divide en chunks y genera embeddings.

        Args:
            title: Título del documento.
            content: Contenido completo del documento.

        Returns:
            Diccionario con info del documento creado.
        """
        doc_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        chunks = _chunk_text(content)

        chunk_ids = []
        documents = []
        metadatas = []

        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_chunk_{i}"
            chunk_ids.append(chunk_id)
            documents.append(chunk)
            metadatas.append({
                "doc_id": doc_id,
                "title": title,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "created_at": now,
            })

        self._collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=chunk_ids,
        )

        logger.info(
            "Documento ingestado: '%s' (%d chunks, id=%s)",
            title,
            len(chunks),
            doc_id,
        )

        return {
            "id": doc_id,
            "title": title,
            "chunks_created": len(chunks),
            "created_at": now,
        }

    def search(self, query: str, n_results: int = 5) -> list[dict]:
        """
        Búsqueda semántica en los documentos de conocimiento.

        Args:
            query: Texto de búsqueda.
            n_results: Número máximo de resultados.

        Returns:
            Lista de chunks relevantes con scores.
        """
        if self._collection.count() == 0:
            return []

        results = self._collection.query(
            query_texts=[query],
            n_results=min(n_results, self._collection.count()),
        )

        items = []
        if results and results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                meta = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 0.0
                items.append({
                    "content": doc,
                    "document_title": meta.get("title", ""),
                    "doc_id": meta.get("doc_id", ""),
                    "chunk_index": meta.get("chunk_index", 0),
                    "relevance_score": round(1.0 - distance, 4),
                })

        return items

    def list_documents(self) -> list[dict]:
        """Lista todos los documentos indexados (agrupados por doc_id)."""
        if self._collection.count() == 0:
            return []

        all_data = self._collection.get(include=["metadatas"])
        if not all_data or not all_data["metadatas"]:
            return []

        # Agrupar por doc_id
        docs: dict[str, dict] = {}
        for meta in all_data["metadatas"]:
            doc_id = meta.get("doc_id", "")
            if doc_id not in docs:
                docs[doc_id] = {
                    "id": doc_id,
                    "title": meta.get("title", "Sin título"),
                    "chunk_count": 0,
                    "created_at": meta.get("created_at", ""),
                }
            docs[doc_id]["chunk_count"] += 1

        return list(docs.values())

    def delete_document(self, doc_id: str) -> bool:
        """Elimina todos los chunks de un documento."""
        try:
            # Encontrar todos los chunks del documento
            all_data = self._collection.get(
                where={"doc_id": doc_id},
                include=["metadatas"],
            )

            if all_data and all_data["ids"]:
                self._collection.delete(ids=all_data["ids"])
                logger.info(
                    "Documento eliminado: %s (%d chunks)",
                    doc_id,
                    len(all_data["ids"]),
                )
                return True

            return False
        except Exception as e:
            logger.error("Error al eliminar documento %s: %s", doc_id, e)
            return False

    def count(self) -> int:
        """Retorna el número total de chunks indexados."""
        return self._collection.count()

    def get_context_summary(self, query: str, n_results: int = 3) -> str:
        """
        Genera un resumen de conocimiento relevante para inyectar como contexto.
        """
        if self._collection.count() == 0:
            return ""

        results = self.search(query, n_results=n_results)
        if not results:
            return ""

        lines = ["**Conocimiento relevante:**"]
        for res in results:
            title = res.get("document_title", "")
            content = res["content"][:500]  # Limitar tamaño
            lines.append(f"- (De: {title}) {content}")

        return "\n".join(lines)
