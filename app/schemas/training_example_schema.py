"""Pydantic schemas for training example APIs."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TrainingExampleBase(BaseModel):
    """Shared fields for training example payloads."""

    wisdom_entry_id: int
    user_problem: str
    assistant_response: str
    tone: str | None = Field(default=None, max_length=100)
    safety_category: str | None = Field(default=None, max_length=100)
    source_references: list[dict[str, str | None] | str] = Field(default_factory=list)
    approved_for_finetune: bool = False
    dataset_quality_score: float | None = Field(default=None, ge=0.0, le=100.0)
    dataset_status: str = Field(default="needs_review", max_length=50)
    dataset_audit_issues: list[str] = Field(default_factory=list)


class TrainingExampleCreate(TrainingExampleBase):
    """Schema for creating a training example."""


class TrainingExampleApprove(BaseModel):
    """Schema for approving a training example for fine-tuning export."""

    approved_for_finetune: bool = True


class TrainingExampleRead(TrainingExampleBase):
    """Schema returned by training example endpoints."""

    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
