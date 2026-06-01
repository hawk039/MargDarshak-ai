"""Routes for creating, uploading, and reading source documents."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.models.canonical_verse import CanonicalVerse
from app.models.document_chunk import DocumentChunk
from app.models.extracted_document_text import ExtractedDocumentText
from app.models.quality_review import QualityReview
from app.models.source_document import SourceDocument
from app.models.training_example import TrainingExample
from app.models.wisdom_entry import WisdomEntry
from app.pipelines.chunk_document_pipeline import ChunkDocumentPipeline
from app.pipelines.extract_wisdom_pipeline import ExtractWisdomPipeline
from app.pipelines.generate_training_examples_pipeline import GenerateTrainingExamplesPipeline
from app.pipelines.ingest_document_pipeline import IngestDocumentPipeline
from app.schemas.canonical_verse_schema import CanonicalVerseRead
from app.schemas.document_chunk_schema import DocumentChunkRead
from app.schemas.quality_review_schema import (
    QualityReviewRead,
    SourceDocumentQualityReportRead,
)
from app.schemas.source_document_schema import (
    ExtractedDocumentTextRead,
    SourceDocumentCreate,
    SourceDocumentRead,
)
from app.schemas.training_example_schema import TrainingExampleRead
from app.schemas.wisdom_entry_schema import WisdomEntryRead
from app.services.document_ingestion_service import (
    DocumentExtractionError,
    InvalidDocumentTypeError,
)
from app.services.ai_principle_extraction_service import AIPrincipleExtractionService
from app.services.quality_service import QualityService
from app.services.parsers.gita_parser_service import GitaParserService
from app.services.principle_quality_service import PrincipleQualityService
from app.services.training_dataset_audit_service import TrainingDatasetAuditService
from app.services.wisdom_distillation_service import WisdomDistillationService

source_document_router = APIRouter(prefix="/source-documents", tags=["Source Documents"])


@source_document_router.post(
    "",
    response_model=SourceDocumentRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_source_document(
    payload: SourceDocumentCreate,
    db: AsyncSession = Depends(get_db_session),
) -> SourceDocument:
    """Create a source document record."""

    source_document = SourceDocument(**payload.model_dump())
    db.add(source_document)
    try:
        await db.commit()
        await db.refresh(source_document)
    except SQLAlchemyError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create source document.",
        ) from exc
    return source_document


@source_document_router.post(
    "/upload",
    response_model=SourceDocumentRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_source_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    tradition: str | None = Form(default=None),
    document_type: str | None = Form(default=None),
    language: str | None = Form(default=None),
    author_or_translator: str | None = Form(default=None),
    source_name: str | None = Form(default=None),
    db: AsyncSession = Depends(get_db_session),
) -> SourceDocument:
    """Upload a PDF, extract raw text, and save both metadata and extraction output."""

    payload = SourceDocumentCreate(
        title=title,
        tradition=tradition,
        document_type=document_type,
        language=language,
        author_or_translator=author_or_translator,
        source_name=source_name,
        file_path="pending-upload",
        status="pending",
    )
    pipeline = IngestDocumentPipeline()
    try:
        source_document, _ = await pipeline.run(upload_file=file, payload=payload, db=db)
    except InvalidDocumentTypeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except DocumentExtractionError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except SQLAlchemyError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to persist uploaded source document.",
        ) from exc
    return source_document


@source_document_router.get("", response_model=list[SourceDocumentRead])
async def list_source_documents(
    db: AsyncSession = Depends(get_db_session),
) -> list[SourceDocument]:
    """Return all source document records ordered by newest first."""

    result = await db.execute(select(SourceDocument).order_by(SourceDocument.created_at.desc()))
    return list(result.scalars().all())


@source_document_router.get("/{document_id}", response_model=SourceDocumentRead)
async def get_source_document(
    document_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> SourceDocument:
    """Return a single source document by ID."""

    result = await db.execute(select(SourceDocument).where(SourceDocument.id == document_id))
    document = result.scalar_one_or_none()
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source document with id={document_id} was not found.",
        )
    return document


@source_document_router.get("/{document_id}/text", response_model=ExtractedDocumentTextRead)
async def get_source_document_text(
    document_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> ExtractedDocumentText:
    """Return the extracted raw text for a source document."""

    source_document = await db.get(SourceDocument, document_id)
    if source_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source document with id={document_id} was not found.",
        )

    result = await db.execute(
        select(ExtractedDocumentText).where(
            ExtractedDocumentText.source_document_id == document_id
        )
    )
    extracted_text = result.scalar_one_or_none()
    if extracted_text is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Extracted text for source document id={document_id} was not found.",
        )
    return extracted_text


@source_document_router.post(
    "/{document_id}/canonical-verses/generate",
    response_model=list[CanonicalVerseRead],
)
async def generate_canonical_verses(
    document_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> list[CanonicalVerse]:
    """Generate canonical verse-level records for a source document."""

    source_document = await db.get(SourceDocument, document_id)
    if source_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source document with id={document_id} was not found.",
        )

    result = await db.execute(
        select(ExtractedDocumentText).where(
            ExtractedDocumentText.source_document_id == document_id
        )
    )
    extracted_text = result.scalar_one_or_none()
    if extracted_text is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Extracted text for source document id={document_id} was not found.",
        )

    parser_service = GitaParserService()
    parsed_verses = parser_service.parse_canonical_verses(extracted_text.raw_text)
    if not parsed_verses:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No canonical verses could be parsed from the source document.",
        )

    source_document.title = parser_service.clean_source_title(source_document.title)

    await db.execute(delete(CanonicalVerse).where(CanonicalVerse.source_document_id == document_id))

    canonical_verses = [
        CanonicalVerse(
            source_document_id=document_id,
            chapter_number=parsed_verse.chapter_number,
            verse_number=parsed_verse.verse_number,
            speaker=parsed_verse.speaker,
            sanskrit_text=parsed_verse.sanskrit_text,
            transliteration=parsed_verse.transliteration,
            english_translation=parsed_verse.english_translation,
            commentary=parsed_verse.commentary,
            page_reference=parsed_verse.page_reference,
            is_valid=parsed_verse.is_valid,
        )
        for parsed_verse in parsed_verses
    ]
    db.add_all(canonical_verses)
    try:
        await db.commit()
    except SQLAlchemyError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to persist canonical verses.",
        ) from exc

    result = await db.execute(
        select(CanonicalVerse)
        .where(CanonicalVerse.source_document_id == document_id)
        .order_by(CanonicalVerse.chapter_number.asc(), CanonicalVerse.id.asc())
    )
    return list(result.scalars().all())


@source_document_router.get(
    "/{document_id}/canonical-verses",
    response_model=list[CanonicalVerseRead],
)
async def list_canonical_verses(
    document_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> list[CanonicalVerse]:
    """Return canonical verses for a source document ordered by chapter and verse."""

    source_document = await db.get(SourceDocument, document_id)
    if source_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source document with id={document_id} was not found.",
        )

    result = await db.execute(
        select(CanonicalVerse)
        .where(CanonicalVerse.source_document_id == document_id)
        .order_by(CanonicalVerse.chapter_number.asc(), CanonicalVerse.id.asc())
    )
    return list(result.scalars().all())


@source_document_router.post(
    "/{document_id}/chunks/generate",
    response_model=list[DocumentChunkRead],
)
async def generate_document_chunks(
    document_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> list[DocumentChunk]:
    """Generate structured chunks from the extracted raw text for a document."""

    source_document = await db.get(SourceDocument, document_id)
    if source_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source document with id={document_id} was not found.",
        )

    result = await db.execute(
        select(ExtractedDocumentText).where(
            ExtractedDocumentText.source_document_id == document_id
        )
    )
    extracted_text = result.scalar_one_or_none()
    if extracted_text is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Extracted text for source document id={document_id} was not found.",
        )

    pipeline = ChunkDocumentPipeline()
    try:
        return await pipeline.run(
            source_document=source_document,
            extracted_text=extracted_text,
            db=db,
        )
    except SQLAlchemyError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate document chunks.",
        ) from exc


@source_document_router.get("/{document_id}/chunks", response_model=list[DocumentChunkRead])
async def list_document_chunks(
    document_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> list[DocumentChunk]:
    """Return all structured chunks for a source document ordered by chunk index."""

    source_document = await db.get(SourceDocument, document_id)
    if source_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source document with id={document_id} was not found.",
        )

    result = await db.execute(
        select(DocumentChunk)
        .where(DocumentChunk.source_document_id == document_id)
        .order_by(DocumentChunk.chunk_index.asc())
    )
    return list(result.scalars().all())


@source_document_router.post(
    "/{document_id}/wisdom-entries/generate",
    response_model=list[WisdomEntryRead],
)
async def generate_wisdom_entries(
    document_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> list[WisdomEntry]:
    """Generate wisdom entries from canonical verses."""

    source_document = await db.get(SourceDocument, document_id)
    if source_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source document with id={document_id} was not found.",
        )

    result = await db.execute(
        select(CanonicalVerse)
        .where(CanonicalVerse.source_document_id == document_id)
        .where(CanonicalVerse.is_valid.is_(True))
        .order_by(CanonicalVerse.chapter_number.asc(), CanonicalVerse.id.asc())
    )
    canonical_verses = list(result.scalars().all())
    if not canonical_verses:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Canonical verses for source document id={document_id} were not found.",
        )

    pipeline = ExtractWisdomPipeline()
    try:
        return await pipeline.run(
            source_document=source_document,
            canonical_verses=canonical_verses,
            db=db,
        )
    except SQLAlchemyError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate wisdom entries.",
        ) from exc


@source_document_router.post(
    "/{document_id}/wisdom-entries/generate-from-canonical",
    response_model=list[WisdomEntryRead],
)
async def generate_wisdom_entries_from_canonical(
    document_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> list[WisdomEntry]:
    """Generate wisdom entries from valid canonical verses only."""

    return await generate_wisdom_entries(document_id=document_id, db=db)


@source_document_router.get(
    "/{document_id}/wisdom-entries",
    response_model=list[WisdomEntryRead],
)
async def list_source_document_wisdom_entries(
    document_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> list[WisdomEntry]:
    """Return wisdom entries for a source document ordered by newest first."""

    source_document = await db.get(SourceDocument, document_id)
    if source_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source document with id={document_id} was not found.",
        )

    result = await db.execute(
        select(WisdomEntry)
        .where(WisdomEntry.source_document_id == document_id)
        .order_by(WisdomEntry.created_at.desc())
    )
    return list(result.scalars().all())


@source_document_router.post(
    "/{document_id}/wisdom-entries/extract-principles",
    response_model=list[WisdomEntryRead],
)
async def extract_wisdom_principles(
    document_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> list[WisdomEntry]:
    """Refine stored wisdom principles and tags using the mock AI service."""

    source_document = await db.get(SourceDocument, document_id)
    if source_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source document with id={document_id} was not found.",
        )

    result = await db.execute(
        select(WisdomEntry)
        .where(WisdomEntry.source_document_id == document_id)
        .order_by(WisdomEntry.created_at.asc())
    )
    wisdom_entries = list(result.scalars().all())
    if not wisdom_entries:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Wisdom entries for source document id={document_id} were not found.",
        )

    principle_service = AIPrincipleExtractionService()
    for wisdom_entry in wisdom_entries:
        refined_result = principle_service.refine_entry(wisdom_entry)
        if refined_result.extracted_principle is None:
            continue
        wisdom_entry.extracted_principle = refined_result.extracted_principle
        wisdom_entry.emotional_tags = refined_result.emotional_tags
        wisdom_entry.philosophical_tags = refined_result.philosophical_tags
        wisdom_entry.use_cases = refined_result.use_cases
        wisdom_entry.confidence_score = refined_result.confidence_score

    try:
        await db.commit()
    except SQLAlchemyError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to refine wisdom principles.",
        ) from exc

    refreshed_result = await db.execute(
        select(WisdomEntry)
        .where(WisdomEntry.source_document_id == document_id)
        .order_by(WisdomEntry.created_at.desc())
    )
    return list(refreshed_result.scalars().all())


@source_document_router.post(
    "/{document_id}/wisdom-entries/distill",
    response_model=list[WisdomEntryRead],
)
async def distill_wisdom_entries(
    document_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> list[WisdomEntry]:
    """Generate universal distilled wisdom for each stored wisdom entry."""

    source_document = await db.get(SourceDocument, document_id)
    if source_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source document with id={document_id} was not found.",
        )

    result = await db.execute(
        select(WisdomEntry)
        .where(WisdomEntry.source_document_id == document_id)
        .order_by(WisdomEntry.created_at.asc())
    )
    wisdom_entries = list(result.scalars().all())
    if not wisdom_entries:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Wisdom entries for source document id={document_id} were not found.",
        )

    distillation_service = WisdomDistillationService()
    for wisdom_entry in wisdom_entries:
        wisdom_entry.distilled_wisdom = distillation_service.distill_entry(wisdom_entry)

    try:
        await db.commit()
    except SQLAlchemyError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to distill wisdom entries.",
        ) from exc

    refreshed_result = await db.execute(
        select(WisdomEntry)
        .where(WisdomEntry.source_document_id == document_id)
        .order_by(WisdomEntry.created_at.desc())
    )
    return list(refreshed_result.scalars().all())


@source_document_router.post(
    "/{document_id}/principles/quality-refine",
    response_model=list[WisdomEntryRead],
)
async def quality_refine_principles(
    document_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> list[WisdomEntry]:
    """Evaluate and persist principle quality status for a source document."""

    source_document = await db.get(SourceDocument, document_id)
    if source_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source document with id={document_id} was not found.",
        )

    result = await db.execute(
        select(WisdomEntry)
        .where(WisdomEntry.source_document_id == document_id)
        .order_by(WisdomEntry.created_at.asc())
    )
    wisdom_entries = list(result.scalars().all())
    if not wisdom_entries:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Wisdom entries for source document id={document_id} were not found.",
        )

    quality_service = PrincipleQualityService()
    for wisdom_entry in wisdom_entries:
        quality_result = quality_service.evaluate_entry(wisdom_entry)
        wisdom_entry.principle_quality_score = quality_result.principle_quality_score
        wisdom_entry.principle_status = quality_result.principle_status
        wisdom_entry.confidence_score = quality_result.confidence_score

    try:
        await db.commit()
    except SQLAlchemyError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to refine principle quality.",
        ) from exc

    refreshed_result = await db.execute(
        select(WisdomEntry)
        .where(WisdomEntry.source_document_id == document_id)
        .order_by(WisdomEntry.created_at.desc())
    )
    return list(refreshed_result.scalars().all())


@source_document_router.post(
    "/{document_id}/training-examples/generate",
    response_model=list[TrainingExampleRead],
)
async def generate_training_examples(
    document_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> list[TrainingExample]:
    """Generate training examples from approved high-confidence wisdom entries only."""

    source_document = await db.get(SourceDocument, document_id)
    if source_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source document with id={document_id} was not found.",
        )

    training_service = GenerateTrainingExamplesPipeline().training_data_generation_service

    result = await db.execute(
        select(WisdomEntry)
        .where(WisdomEntry.source_document_id == document_id)
        .where(WisdomEntry.principle_status == "approved")
        .where(WisdomEntry.confidence_score >= 80)
        .order_by(WisdomEntry.created_at.asc())
    )
    wisdom_entries = list(result.scalars().all())
    if not wisdom_entries:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "No approved high-confidence wisdom entries were found for training example generation."
            ),
        )

    eligible_wisdom_entries = [
        wisdom_entry
        for wisdom_entry in wisdom_entries
        if training_service.is_training_eligible(wisdom_entry)
    ]
    if not eligible_wisdom_entries:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Approved wisdom entries exist, but none passed training-example eligibility checks."
            ),
        )

    pipeline = GenerateTrainingExamplesPipeline(training_data_generation_service=training_service)
    try:
        return await pipeline.run(wisdom_entries=eligible_wisdom_entries, db=db)
    except SQLAlchemyError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate training examples.",
        ) from exc


@source_document_router.post(
    "/{document_id}/training-examples/generate-from-approved-principles",
    response_model=list[TrainingExampleRead],
)
async def generate_training_examples_from_approved_principles(
    document_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    replace_existing: bool = Query(default=False),
    db: AsyncSession = Depends(get_db_session),
) -> list[TrainingExample]:
    """Generate training examples in SQLite-safe batches from approved principles."""

    source_document = await db.get(SourceDocument, document_id)
    if source_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source document with id={document_id} was not found.",
        )

    training_service = GenerateTrainingExamplesPipeline().training_data_generation_service
    result = await db.execute(
        select(WisdomEntry)
        .where(WisdomEntry.source_document_id == document_id)
        .where(WisdomEntry.principle_status == "approved")
        .where(WisdomEntry.confidence_score >= 80)
        .order_by(WisdomEntry.created_at.asc())
        .offset(offset)
        .limit(limit)
    )
    wisdom_entries = list(result.scalars().all())
    if not wisdom_entries:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No approved wisdom entries were found for the requested batch.",
        )

    eligible_wisdom_entries = [
        wisdom_entry
        for wisdom_entry in wisdom_entries
        if training_service.is_training_eligible(wisdom_entry)
    ]
    if not eligible_wisdom_entries and replace_existing:
        return []

    pipeline = GenerateTrainingExamplesPipeline(training_data_generation_service=training_service)
    try:
        batch_result = await pipeline.run_batched(
            wisdom_entries=eligible_wisdom_entries,
            db=db,
            replace_existing=replace_existing,
            commit_every_examples=10,
        )
    except SQLAlchemyError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate training examples for the requested batch.",
        ) from exc
    return batch_result.generated_examples


@source_document_router.get(
    "/{document_id}/training-examples",
    response_model=list[TrainingExampleRead],
)
async def list_source_document_training_examples(
    document_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> list[TrainingExample]:
    """Return training examples for a source document ordered by newest first."""

    source_document = await db.get(SourceDocument, document_id)
    if source_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source document with id={document_id} was not found.",
        )

    result = await db.execute(
        select(TrainingExample)
        .join(WisdomEntry, TrainingExample.wisdom_entry_id == WisdomEntry.id)
        .where(WisdomEntry.source_document_id == document_id)
        .order_by(TrainingExample.created_at.desc())
    )
    return list(result.scalars().all())


@source_document_router.post(
    "/{document_id}/training-dataset/audit",
    response_model=list[TrainingExampleRead],
)
async def audit_source_document_training_dataset(
    document_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> list[TrainingExample]:
    """Audit training examples for a source document before export."""

    source_document = await db.get(SourceDocument, document_id)
    if source_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source document with id={document_id} was not found.",
        )

    result = await db.execute(
        select(TrainingExample)
        .join(WisdomEntry, TrainingExample.wisdom_entry_id == WisdomEntry.id)
        .where(WisdomEntry.source_document_id == document_id)
        .order_by(TrainingExample.created_at.asc())
    )
    training_examples = list(result.scalars().all())
    if not training_examples:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Training examples for source document id={document_id} were not found.",
        )

    audit_service = TrainingDatasetAuditService()
    audit_results = audit_service.audit_examples(training_examples)
    training_examples_by_id = {training_example.id: training_example for training_example in training_examples}

    for audit_result in audit_results:
        training_example = training_examples_by_id[audit_result.training_example_id]
        training_example.dataset_quality_score = audit_result.dataset_quality_score
        training_example.dataset_status = audit_result.dataset_status
        training_example.dataset_audit_issues = audit_result.issues

    try:
        await db.commit()
    except SQLAlchemyError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to persist training dataset audit results.",
        ) from exc

    refreshed_result = await db.execute(
        select(TrainingExample)
        .join(WisdomEntry, TrainingExample.wisdom_entry_id == WisdomEntry.id)
        .where(WisdomEntry.source_document_id == document_id)
        .order_by(TrainingExample.created_at.desc())
    )
    return list(refreshed_result.scalars().all())


@source_document_router.post(
    "/{document_id}/quality-review",
    response_model=SourceDocumentQualityReportRead,
)
async def run_source_document_quality_review(
    document_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> SourceDocumentQualityReportRead:
    """Run quality review for wisdom entries and training examples from one document."""

    source_document = await db.get(SourceDocument, document_id)
    if source_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source document with id={document_id} was not found.",
        )

    wisdom_result = await db.execute(
        select(WisdomEntry)
        .where(WisdomEntry.source_document_id == document_id)
        .order_by(WisdomEntry.created_at.asc())
    )
    wisdom_entries = list(wisdom_result.scalars().all())
    if not wisdom_entries:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Wisdom entries for source document id={document_id} were not found.",
        )

    training_result = await db.execute(
        select(TrainingExample)
        .join(WisdomEntry, TrainingExample.wisdom_entry_id == WisdomEntry.id)
        .where(WisdomEntry.source_document_id == document_id)
        .order_by(TrainingExample.created_at.asc())
    )
    training_examples = list(training_result.scalars().all())
    if not training_examples:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Training examples for source document id={document_id} were not found.",
        )

    quality_service = QualityService()
    quality_results = quality_service.review_source_document(
        wisdom_entries=wisdom_entries,
        training_examples=training_examples,
    )

    existing_reviews_result = await db.execute(
        select(QualityReview).where(QualityReview.wisdom_entry_id.in_([entry.id for entry in wisdom_entries]))
    )
    existing_reviews = {
        review.wisdom_entry_id: review for review in list(existing_reviews_result.scalars().all())
    }

    persisted_reviews: list[QualityReview] = []
    for quality_result in quality_results:
        quality_review = existing_reviews.get(quality_result.wisdom_entry_id)
        if quality_review is None:
            quality_review = QualityReview(
                wisdom_entry_id=quality_result.wisdom_entry_id,
                quality_score=quality_result.quality_score,
                validation_status=quality_result.validation_status,
                issues=quality_result.issues,
            )
            db.add(quality_review)
        else:
            quality_review.quality_score = quality_result.quality_score
            quality_review.validation_status = quality_result.validation_status
            quality_review.issues = quality_result.issues
        persisted_reviews.append(quality_review)

    try:
        await db.commit()
        for quality_review in persisted_reviews:
            await db.refresh(quality_review)
    except SQLAlchemyError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to persist quality reviews.",
        ) from exc

    return _build_quality_report(document_id=document_id, quality_reviews=persisted_reviews)


@source_document_router.get(
    "/{document_id}/quality-report",
    response_model=SourceDocumentQualityReportRead,
)
async def get_source_document_quality_report(
    document_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> SourceDocumentQualityReportRead:
    """Return the current quality review report for a source document."""

    source_document = await db.get(SourceDocument, document_id)
    if source_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source document with id={document_id} was not found.",
        )

    result = await db.execute(
        select(QualityReview)
        .join(WisdomEntry, QualityReview.wisdom_entry_id == WisdomEntry.id)
        .where(WisdomEntry.source_document_id == document_id)
        .order_by(QualityReview.created_at.desc())
    )
    quality_reviews = list(result.scalars().all())
    if not quality_reviews:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quality reviews for source document id={document_id} were not found.",
        )

    return _build_quality_report(document_id=document_id, quality_reviews=quality_reviews)


def _build_quality_report(
    document_id: int,
    quality_reviews: list[QualityReview],
) -> SourceDocumentQualityReportRead:
    """Return an aggregated report from a list of quality reviews."""

    total_reviews = len(quality_reviews)
    approved_reviews = sum(
        1 for quality_review in quality_reviews if quality_review.validation_status == "approved"
    )
    rejected_reviews = total_reviews - approved_reviews
    average_quality_score = (
        round(sum(quality_review.quality_score for quality_review in quality_reviews) / total_reviews, 2)
        if total_reviews
        else 0.0
    )
    return SourceDocumentQualityReportRead(
        source_document_id=document_id,
        total_reviews=total_reviews,
        approved_reviews=approved_reviews,
        rejected_reviews=rejected_reviews,
        average_quality_score=average_quality_score,
        reviews=[QualityReviewRead.model_validate(review) for review in quality_reviews],
    )
