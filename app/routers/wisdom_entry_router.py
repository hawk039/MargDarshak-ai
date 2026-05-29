"""Routes for managing wisdom entries."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.models.source_document import SourceDocument
from app.models.wisdom_entry import WisdomEntry
from app.schemas.wisdom_entry_schema import WisdomEntryCreate, WisdomEntryRead

wisdom_entry_router = APIRouter(prefix="/wisdom-entries", tags=["Wisdom Entries"])


@wisdom_entry_router.post(
    "",
    response_model=WisdomEntryRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_wisdom_entry(
    payload: WisdomEntryCreate,
    db: AsyncSession = Depends(get_db_session),
) -> WisdomEntry:
    """Create a wisdom entry for an existing source document."""

    source_document = await db.get(SourceDocument, payload.source_document_id)
    if source_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source document with id={payload.source_document_id} was not found.",
        )

    wisdom_entry = WisdomEntry(**payload.model_dump())
    db.add(wisdom_entry)
    try:
        await db.commit()
        await db.refresh(wisdom_entry)
    except SQLAlchemyError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create wisdom entry.",
        ) from exc
    return wisdom_entry


@wisdom_entry_router.get("", response_model=list[WisdomEntryRead])
async def list_wisdom_entries(
    db: AsyncSession = Depends(get_db_session),
) -> list[WisdomEntry]:
    """Return all wisdom entries ordered by newest first."""

    result = await db.execute(select(WisdomEntry).order_by(WisdomEntry.created_at.desc()))
    return list(result.scalars().all())


@wisdom_entry_router.get("/search", response_model=list[WisdomEntryRead])
async def search_wisdom_entries(
    tag: str = Query(..., min_length=1, description="Tag to match across stored tag lists."),
    db: AsyncSession = Depends(get_db_session),
) -> list[WisdomEntry]:
    """Search wisdom entries by emotional or philosophical tag."""

    result = await db.execute(select(WisdomEntry).order_by(WisdomEntry.created_at.desc()))
    entries = list(result.scalars().all())
    return [
        entry
        for entry in entries
        if any(tag.lower() in value.lower() for value in entry.emotional_tags + entry.philosophical_tags + entry.use_cases)
    ]


@wisdom_entry_router.get("/{wisdom_entry_id}", response_model=WisdomEntryRead)
async def get_wisdom_entry(
    wisdom_entry_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> WisdomEntry:
    """Return a single wisdom entry by ID."""

    result = await db.execute(select(WisdomEntry).where(WisdomEntry.id == wisdom_entry_id))
    wisdom_entry = result.scalar_one_or_none()
    if wisdom_entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Wisdom entry with id={wisdom_entry_id} was not found.",
        )
    return wisdom_entry
