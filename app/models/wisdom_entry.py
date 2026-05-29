"""ORM model for verse or section-level wisdom entries."""

from sqlalchemy import Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class WisdomEntry(Base):
    """Store a single wisdom-bearing excerpt and its extracted meaning."""

    __tablename__ = "wisdom_entries"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    source_document_id: Mapped[int] = mapped_column(
        ForeignKey("source_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    book_title: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    chapter: Mapped[str | None] = mapped_column(String(100), nullable=True)
    section: Mapped[str | None] = mapped_column(String(100), nullable=True)
    verse_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    transliteration: Mapped[str | None] = mapped_column(Text, nullable=True)
    translation: Mapped[str | None] = mapped_column(Text, nullable=True)
    commentary: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_principle: Mapped[str | None] = mapped_column(Text, nullable=True)
    emotional_tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    philosophical_tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    use_cases: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    principle_quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    principle_status: Mapped[str] = mapped_column(String(50), nullable=False, default="needs_review")

    source_document = relationship("SourceDocument", back_populates="wisdom_entries")
    training_examples = relationship(
        "TrainingExample",
        back_populates="wisdom_entry",
        cascade="all, delete-orphan",
    )
    quality_review = relationship(
        "QualityReview",
        back_populates="wisdom_entry",
        cascade="all, delete-orphan",
        uselist=False,
    )
