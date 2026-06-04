"""ORM model for canonical Upanishad passage records extracted from source texts."""

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CanonicalPassage(Base):
    """Store cleaned passage-level records for Upanishad pilot ingestion."""

    __tablename__ = "canonical_passages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    source_document_id: Mapped[int] = mapped_column(
        ForeignKey("source_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    upanishad_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    chapter: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    section: Mapped[str | None] = mapped_column(String(100), nullable=True)
    passage_number: Mapped[str] = mapped_column(String(50), nullable=False)
    speaker: Mapped[str | None] = mapped_column(String(100), nullable=True)
    original_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    english_translation: Mapped[str] = mapped_column(Text, nullable=False)
    commentary_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_valid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    source_document = relationship("SourceDocument", back_populates="canonical_passages")
