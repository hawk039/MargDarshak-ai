"""Routes for reading individual structured document chunks."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.models.document_chunk import DocumentChunk
from app.schemas.document_chunk_schema import DocumentChunkRead

document_chunk_router = APIRouter(prefix="/document-chunks", tags=["Document Chunks"])


@document_chunk_router.get("/{chunk_id}", response_model=DocumentChunkRead)
async def get_document_chunk(
    chunk_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> DocumentChunk:
    """Return a single structured document chunk by ID."""

    document_chunk = await db.get(DocumentChunk, chunk_id)
    if document_chunk is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document chunk with id={chunk_id} was not found.",
        )
    return document_chunk
