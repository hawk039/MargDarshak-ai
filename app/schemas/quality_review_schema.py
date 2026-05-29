"""Pydantic schemas for quality review APIs."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class QualityReviewRead(BaseModel):
    """Schema returned for an individual quality review."""

    id: int
    wisdom_entry_id: int
    quality_score: int
    validation_status: str
    issues: list[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SourceDocumentQualityReportRead(BaseModel):
    """Schema returned for a source document quality report."""

    source_document_id: int
    total_reviews: int
    approved_reviews: int
    rejected_reviews: int
    average_quality_score: float
    reviews: list[QualityReviewRead]
