"""Pydantic schemas for structured document chunk APIs."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentChunkRead(BaseModel):
    """Schema returned by document chunk endpoints."""

    id: int
    source_document_id: int
    chunk_index: int = Field(..., ge=1)
    chapter: str | None = None
    section_title: str | None = None
    verse_number: str | None = None
    content: str
    content_type: str
    page_reference: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
