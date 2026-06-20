"""
Jarvis V1 - Endpoint: Knowledge Base.

Upload, búsqueda semántica, y gestión de documentos de conocimiento.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form

from app.api.dependencies import get_knowledge_base
from app.memory.knowledge_base import KnowledgeBase
from app.schemas.memory import (
    KnowledgeUploadResponse,
    KnowledgeSearchResponse,
    KnowledgeSearchResult,
    KnowledgeDocumentResponse,
    KnowledgeListResponse,
)
from app.schemas.common import SuccessResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload", response_model=KnowledgeUploadResponse)
async def upload_document(
    title: str = Form(..., description="Título del documento"),
    file: UploadFile = File(..., description="Archivo de texto (.txt)"),
    kb: KnowledgeBase = Depends(get_knowledge_base),
):
    """
    Sube un documento de texto para indexar en la base de conocimiento.

    El documento se divide en chunks, se generan embeddings,
    y queda disponible para búsqueda semántica.

    Formatos soportados: .txt (más formatos en el futuro).
    """
    # Validar tipo de archivo
    if file.filename and not file.filename.endswith(".txt"):
        raise HTTPException(
            status_code=400,
            detail="Solo se soportan archivos .txt por ahora",
        )

    # Leer contenido
    content = await file.read()
    text = content.decode("utf-8")

    if not text.strip():
        raise HTTPException(status_code=400, detail="El archivo está vacío")

    # Ingestar documento
    result = kb.ingest_text(title=title, content=text)

    logger.info(
        "POST /knowledge/upload — '%s' (%d chunks)",
        title,
        result["chunks_created"],
    )

    return KnowledgeUploadResponse(
        id=result["id"],
        title=result["title"],
        chunks_created=result["chunks_created"],
        message=f"Documento '{title}' indexado exitosamente con {result['chunks_created']} chunks",
    )


@router.get("/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(
    q: str,
    n: int = 5,
    kb: KnowledgeBase = Depends(get_knowledge_base),
):
    """Búsqueda semántica en la base de conocimiento."""
    results = kb.search(query=q, n_results=n)
    return KnowledgeSearchResponse(
        results=[
            KnowledgeSearchResult(
                content=r["content"],
                document_title=r.get("document_title", ""),
                relevance_score=r.get("relevance_score", 0.0),
            )
            for r in results
        ],
        query=q,
        total=len(results),
    )


@router.get("", response_model=KnowledgeListResponse)
async def list_documents(
    kb: KnowledgeBase = Depends(get_knowledge_base),
):
    """Lista todos los documentos indexados."""
    docs = kb.list_documents()
    return KnowledgeListResponse(
        documents=[
            KnowledgeDocumentResponse(
                id=d["id"],
                title=d["title"],
                chunk_count=d["chunk_count"],
                created_at=d.get("created_at", ""),
            )
            for d in docs
        ],
        total=len(docs),
    )


@router.delete("/{doc_id}", response_model=SuccessResponse)
async def delete_document(
    doc_id: str,
    kb: KnowledgeBase = Depends(get_knowledge_base),
):
    """Elimina un documento y todos sus chunks."""
    deleted = kb.delete_document(doc_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    return SuccessResponse(message=f"Documento {doc_id} eliminado")
