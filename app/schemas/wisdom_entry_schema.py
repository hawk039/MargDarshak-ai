"""Pydantic schemas for wisdom entry APIs."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WisdomEntryBase(BaseModel):
    """Shared fields for wisdom entry payloads."""

    source_document_id: int
    book_title: str | None = Field(default=None, max_length=255)
    chapter: str | None = Field(default=None, max_length=100)
    section: str | None = Field(default=None, max_length=100)
    verse_number: str | None = Field(default=None, max_length=50)
    original_text: str
    transliteration: str | None = None
    translation: str | None = None
    commentary: str | None = None
    extracted_principle: str | None = None
    emotional_tags: list[str] = Field(default_factory=list)
    philosophical_tags: list[str] = Field(default_factory=list)
    use_cases: list[str] = Field(default_factory=list)
    confidence_score: float | None = Field(default=None, ge=0.0, le=100.0)
    principle_quality_score: float | None = Field(default=None, ge=0.0, le=100.0)
    principle_status: str = Field(default="needs_review", max_length=50)


class WisdomEntryCreate(WisdomEntryBase):
    """Schema for creating a wisdom entry."""


class WisdomEntryRead(WisdomEntryBase):
    """Schema returned by wisdom entry endpoints."""

    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
