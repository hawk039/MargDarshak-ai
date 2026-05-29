"""Pydantic schemas for source document APIs."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SourceDocumentBase(BaseModel):
    """Shared fields for source document payloads."""

    title: str = Field(..., max_length=255)
    tradition: str | None = Field(default=None, max_length=100)
    document_type: str | None = Field(default=None, max_length=100)
    language: str | None = Field(default=None, max_length=50)
    author_or_translator: str | None = Field(default=None, max_length=255)
    source_name: str | None = Field(default=None, max_length=255)
    file_path: str
    status: str = Field(default="pending", max_length=50)


class SourceDocumentCreate(SourceDocumentBase):
    """Schema for creating a new source document."""


class SourceDocumentRead(SourceDocumentBase):
    """Schema returned by source document endpoints."""

    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExtractedDocumentTextRead(BaseModel):
    """Schema returned for extracted raw document text."""

    id: int
    source_document_id: int
    raw_text: str
    page_count: int
    extraction_status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
