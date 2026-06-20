"""
Jarvis V1 - Schemas de Memoria.

DTOs para los endpoints de memoria episódica y conocimiento.
"""

from pydantic import BaseModel, Field


class MemoryEntryResponse(BaseModel):
    """Una memoria episódica."""
    id: str
    content: str
    category: str
    timestamp: str
    metadata: dict = Field(default_factory=dict)


class MemoryListResponse(BaseModel):
    """Lista de memorias episódicas."""
    memories: list[MemoryEntryResponse]
    total: int


class MemorySearchResponse(BaseModel):
    """Resultado de búsqueda semántica en memorias."""
    results: list[MemoryEntryResponse]
    query: str
    total: int


class KnowledgeUploadResponse(BaseModel):
    """Respuesta tras subir un documento."""
    id: str
    title: str
    chunks_created: int
    message: str


class KnowledgeSearchResult(BaseModel):
    """Un resultado de búsqueda en la base de conocimiento."""
    content: str
    document_title: str
    relevance_score: float


class KnowledgeSearchResponse(BaseModel):
    """Resultados de búsqueda en conocimiento."""
    results: list[KnowledgeSearchResult]
    query: str
    total: int


class KnowledgeDocumentResponse(BaseModel):
    """Info de un documento indexado."""
    id: str
    title: str
    chunk_count: int
    created_at: str


class KnowledgeListResponse(BaseModel):
    """Lista de documentos indexados."""
    documents: list[KnowledgeDocumentResponse]
    total: int
