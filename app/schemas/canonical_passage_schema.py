"""Pydantic schemas for canonical Upanishad passage APIs."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CanonicalPassageRead(BaseModel):
    """Schema returned by canonical passage endpoints."""

    id: int
    source_document_id: int
    upanishad_name: str
    chapter: str | None = None
    section: str | None = None
    passage_number: str
    speaker: str | None = None
    original_text: str | None = None
    english_translation: str
    commentary_text: str | None = None
    page_reference: str | None = None
    is_valid: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
