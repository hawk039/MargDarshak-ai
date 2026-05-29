"""Pydantic schemas for canonical verse APIs."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CanonicalVerseRead(BaseModel):
    """Schema returned by canonical verse endpoints."""

    id: int
    source_document_id: int
    chapter_number: int
    verse_number: str
    speaker: str | None = None
    sanskrit_text: str | None = None
    transliteration: str | None = None
    english_translation: str
    commentary: str | None = None
    page_reference: str | None = None
    is_valid: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
