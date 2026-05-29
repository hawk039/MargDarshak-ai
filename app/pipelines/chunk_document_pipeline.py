"""Pipeline that orchestrates structured chunk generation for extracted text."""

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document_chunk import DocumentChunk
from app.models.extracted_document_text import ExtractedDocumentText
from app.models.source_document import SourceDocument
from app.services.document_chunking_service import DocumentChunkingService


class ChunkDocumentPipeline:
    """Generate structured document chunks from extracted raw text."""

    def __init__(self, chunking_service: DocumentChunkingService | None = None) -> None:
        self.chunking_service = chunking_service or DocumentChunkingService()

    async def run(
        self,
        source_document: SourceDocument,
        extracted_text: ExtractedDocumentText,
        db: AsyncSession,
    ) -> list[DocumentChunk]:
        """Replace stored chunks for a document with a newly parsed set."""

        parsed_chunks = self.chunking_service.parse_raw_text(extracted_text.raw_text)

        await db.execute(
            delete(DocumentChunk).where(DocumentChunk.source_document_id == source_document.id)
        )

        document_chunks = [
            DocumentChunk(
                source_document_id=source_document.id,
                chunk_index=parsed_chunk.chunk_index,
                chapter=parsed_chunk.chapter,
                section_title=parsed_chunk.section_title,
                verse_number=parsed_chunk.verse_number,
                content=parsed_chunk.content,
                content_type=parsed_chunk.content_type,
                page_reference=parsed_chunk.page_reference,
            )
            for parsed_chunk in parsed_chunks
        ]
        db.add_all(document_chunks)
        await db.commit()

        for document_chunk in document_chunks:
            await db.refresh(document_chunk)

        return document_chunks
