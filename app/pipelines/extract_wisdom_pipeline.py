"""Pipeline that orchestrates wisdom entry generation from canonical verses."""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.canonical_verse import CanonicalVerse
from app.models.source_document import SourceDocument
from app.models.wisdom_entry import WisdomEntry
from app.services.wisdom_extraction_service import WisdomExtractionService


class ExtractWisdomPipeline:
    """Generate wisdom entries from canonical verses."""

    def __init__(self, extraction_service: WisdomExtractionService | None = None) -> None:
        self.extraction_service = extraction_service or WisdomExtractionService()

    async def run(
        self,
        source_document: SourceDocument,
        canonical_verses: list[CanonicalVerse],
        db: AsyncSession,
    ) -> list[WisdomEntry]:
        """Replace stored wisdom entries for a document with a newly extracted set."""

        extracted_entries = self.extraction_service.extract_entries(
            source_document=source_document,
            canonical_verses=canonical_verses,
        )

        await db.execute(delete(WisdomEntry).where(WisdomEntry.source_document_id == source_document.id))

        wisdom_entries = [
            WisdomEntry(
                source_document_id=entry.source_document_id,
                book_title=entry.book_title,
                chapter=entry.chapter,
                section=entry.section,
                verse_number=entry.verse_number,
                original_text=entry.original_text,
                translation=entry.translation,
                commentary=entry.commentary,
                extracted_principle=entry.extracted_principle,
                emotional_tags=entry.emotional_tags,
                philosophical_tags=entry.philosophical_tags,
                use_cases=entry.use_cases,
                confidence_score=entry.confidence_score,
            )
            for entry in extracted_entries
        ]
        db.add_all(wisdom_entries)
        await db.commit()

        result = await db.execute(
            select(WisdomEntry)
            .where(WisdomEntry.source_document_id == source_document.id)
            .order_by(WisdomEntry.created_at.desc())
        )
        return list(result.scalars().all())
