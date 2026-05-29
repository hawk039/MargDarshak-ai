"""ORM model for ingested source documents."""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SourceDocument(Base):
    """Store metadata about a spiritual or philosophical source file."""

    __tablename__ = "source_documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    tradition: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    document_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    language: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    author_or_translator: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")

    wisdom_entries = relationship(
        "WisdomEntry",
        back_populates="source_document",
        cascade="all, delete-orphan",
    )
    extracted_text = relationship(
        "ExtractedDocumentText",
        back_populates="source_document",
        cascade="all, delete-orphan",
        uselist=False,
    )
    document_chunks = relationship(
        "DocumentChunk",
        back_populates="source_document",
        cascade="all, delete-orphan",
    )
    canonical_verses = relationship(
        "CanonicalVerse",
        back_populates="source_document",
        cascade="all, delete-orphan",
    )
