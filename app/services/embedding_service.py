"""
Jarvis V1 - Servicio de Embeddings.

Wrapper sobre sentence-transformers que proporciona la función de embedding
compatible con ChromaDB. Carga el modelo una sola vez (singleton).
"""

import logging

from chromadb.utils import embedding_functions

logger = logging.getLogger(__name__)

# Singleton global para la función de embedding
_embedding_fn = None


def get_embedding_function(model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
    """
    Retorna una función de embedding compatible con ChromaDB.

    El modelo se carga solo una vez (singleton) para ahorrar RAM
    en la tablet.

    Args:
        model_name: Nombre del modelo de sentence-transformers.

    Returns:
        SentenceTransformerEmbeddingFunction compatible con ChromaDB.
    """
    global _embedding_fn

    if _embedding_fn is None:
        logger.info("Cargando modelo de embeddings: %s ...", model_name)
        _embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=model_name,
            device="cpu",  # La tablet no tiene GPU
        )
        logger.info("Modelo de embeddings cargado exitosamente")

    return _embedding_fn
