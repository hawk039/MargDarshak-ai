"""Routes for managing training examples and dataset exports."""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db_session
from app.models.training_example import TrainingExample
from app.models.wisdom_entry import WisdomEntry
from app.pipelines.generate_training_dataset_pipeline import GenerateTrainingDatasetPipeline
from app.schemas.training_example_schema import (
    TrainingExampleApprove,
    TrainingExampleCreate,
    TrainingExampleRead,
)
from app.utils.file_utils import ensure_directory

training_dataset_router = APIRouter(tags=["Training Dataset"])
settings = get_settings()


@training_dataset_router.post(
    "/training-examples",
    response_model=TrainingExampleRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_training_example(
    payload: TrainingExampleCreate,
    db: AsyncSession = Depends(get_db_session),
) -> TrainingExample:
    """Create a training example linked to a wisdom entry."""

    wisdom_entry = await db.get(WisdomEntry, payload.wisdom_entry_id)
    if wisdom_entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Wisdom entry with id={payload.wisdom_entry_id} was not found.",
        )

    training_example = TrainingExample(**payload.model_dump())
    db.add(training_example)
    try:
        await db.commit()
        await db.refresh(training_example)
    except SQLAlchemyError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create training example.",
        ) from exc
    return training_example


@training_dataset_router.get("/training-examples", response_model=list[TrainingExampleRead])
async def list_training_examples(
    db: AsyncSession = Depends(get_db_session),
) -> list[TrainingExample]:
    """Return all training examples ordered by newest first."""

    result = await db.execute(select(TrainingExample).order_by(TrainingExample.created_at.desc()))
    return list(result.scalars().all())


@training_dataset_router.get("/training-examples/{training_example_id}", response_model=TrainingExampleRead)
async def get_training_example(
    training_example_id: int,
    db: AsyncSession = Depends(get_db_session),
) -> TrainingExample:
    """Return a single training example by ID."""

    result = await db.execute(
        select(TrainingExample).where(TrainingExample.id == training_example_id)
    )
    training_example = result.scalar_one_or_none()
    if training_example is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Training example with id={training_example_id} was not found.",
        )
    return training_example


@training_dataset_router.patch(
    "/training-examples/{training_example_id}/approve",
    response_model=TrainingExampleRead,
)
async def approve_training_example(
    training_example_id: int,
    payload: TrainingExampleApprove,
    db: AsyncSession = Depends(get_db_session),
) -> TrainingExample:
    """Approve or unapprove a training example for later fine-tuning export."""

    training_example = await db.get(TrainingExample, training_example_id)
    if training_example is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Training example with id={training_example_id} was not found.",
        )

    training_example.approved_for_finetune = payload.approved_for_finetune
    try:
        await db.commit()
        await db.refresh(training_example)
    except SQLAlchemyError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update training example approval status.",
        ) from exc
    return training_example


@training_dataset_router.get(
    "/training-dataset/export-jsonl",
    response_class=PlainTextResponse,
)
async def export_training_dataset_jsonl(
    approved_only: bool = Query(
        default=True,
        description="When true, export only approved training examples.",
    ),
    db: AsyncSession = Depends(get_db_session),
) -> PlainTextResponse:
    """Export approved training examples as JSONL content."""

    query = (
        select(TrainingExample)
        .join(WisdomEntry, TrainingExample.wisdom_entry_id == WisdomEntry.id)
        .where(
            TrainingExample.approved_for_finetune.is_(True),
            WisdomEntry.principle_status == "approved",
            TrainingExample.dataset_status == "approved",
        )
        .order_by(TrainingExample.created_at.asc())
    )

    result = await db.execute(query)
    training_examples = list(result.scalars().all())
    if not training_examples:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "No approved high-quality training examples found for export."
                if approved_only
                else "No high-quality training examples found for export."
            ),
        )

    pipeline = GenerateTrainingDatasetPipeline()
    jsonl_lines = pipeline.run(training_examples)

    export_dir = ensure_directory(settings.export_directory)
    export_path = Path(export_dir) / "training_dataset.jsonl"
    export_path.write_text("\n".join(jsonl_lines), encoding="utf-8")

    return PlainTextResponse(content="\n".join(jsonl_lines), media_type="application/jsonl")
