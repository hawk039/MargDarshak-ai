"""ORM model for structured chunks derived from extracted document text."""

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DocumentChunk(Base):
    """Store parsed document chunks for later wisdom extraction workflows."""

    __tablename__ = "document_chunks"
    __table_args__ = (
        UniqueConstraint("source_document_id", "chunk_index", name="uq_document_chunks_source_chunk"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    source_document_id: Mapped[int] = mapped_column(
        ForeignKey("source_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chapter: Mapped[str | None] = mapped_column(String(100), nullable=True)
    section_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    verse_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False, default="unknown")
    page_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)

    source_document = relationship("SourceDocument", back_populates="document_chunks")
