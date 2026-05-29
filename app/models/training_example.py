"""ORM model for curated training examples derived from wisdom entries."""

from sqlalchemy import Boolean, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TrainingExample(Base):
    """Store user-problem and assistant-response pairs for future fine-tuning."""

    __tablename__ = "training_examples"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    wisdom_entry_id: Mapped[int] = mapped_column(
        ForeignKey("wisdom_entries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_problem: Mapped[str] = mapped_column(Text, nullable=False)
    assistant_response: Mapped[str] = mapped_column(Text, nullable=False)
    tone: Mapped[str | None] = mapped_column(String(100), nullable=True)
    safety_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_references: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    approved_for_finetune: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    dataset_quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    dataset_status: Mapped[str] = mapped_column(String(50), nullable=False, default="needs_review")
    dataset_audit_issues: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    wisdom_entry = relationship("WisdomEntry", back_populates="training_examples")
