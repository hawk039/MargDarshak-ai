"""ORM model for storing raw text extracted from ingested documents."""

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ExtractedDocumentText(Base):
    """Store raw extracted text for a processed source document."""

    __tablename__ = "extracted_document_texts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    source_document_id: Mapped[int] = mapped_column(
        ForeignKey("source_documents.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, nullable=False)
    extraction_status: Mapped[str] = mapped_column(String(50), nullable=False, default="processed")

    source_document = relationship("SourceDocument", back_populates="extracted_text")
