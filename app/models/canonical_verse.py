"""ORM model for canonical verse-level records extracted from source texts."""

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CanonicalVerse(Base):
    """Store cleaned verse-level records before wisdom extraction."""

    __tablename__ = "canonical_verses"
    __table_args__ = (
        UniqueConstraint(
            "source_document_id",
            "verse_number",
            name="uq_canonical_verses_source_document_verse",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    source_document_id: Mapped[int] = mapped_column(
        ForeignKey("source_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chapter_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    verse_number: Mapped[str] = mapped_column(String(50), nullable=False)
    speaker: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sanskrit_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    transliteration: Mapped[str | None] = mapped_column(Text, nullable=True)
    english_translation: Mapped[str] = mapped_column(Text, nullable=False)
    commentary: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_valid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    source_document = relationship("SourceDocument", back_populates="canonical_verses")
