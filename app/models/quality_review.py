"""ORM model for quality validation of generated wisdom entries."""

from sqlalchemy import ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class QualityReview(Base):
    """Store the current quality review result for a wisdom entry."""

    __tablename__ = "quality_reviews"
    __table_args__ = (
        UniqueConstraint("wisdom_entry_id", name="uq_quality_reviews_wisdom_entry_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    wisdom_entry_id: Mapped[int] = mapped_column(
        ForeignKey("wisdom_entries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    quality_score: Mapped[int] = mapped_column(Integer, nullable=False)
    validation_status: Mapped[str] = mapped_column(String(50), nullable=False)
    issues: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    wisdom_entry = relationship("WisdomEntry", back_populates="quality_review")
