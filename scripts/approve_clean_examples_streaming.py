"""Approve clean audited examples one row at a time."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from sqlalchemy import select

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import AsyncSessionLocal
from app.models.training_example import TrainingExample
from app.models.wisdom_entry import WisdomEntry


async def approve_clean_examples_streaming(source_document_id: int) -> None:
    """Approve export-safe examples with immediate commits."""

    total_approved = 0
    total_skipped = 0

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(TrainingExample.id)
            .join(WisdomEntry, TrainingExample.wisdom_entry_id == WisdomEntry.id)
            .where(WisdomEntry.source_document_id == source_document_id)
            .where(WisdomEntry.principle_status == "approved")
            .where(TrainingExample.dataset_status == "approved")
            .where(TrainingExample.dataset_quality_score >= 85)
            .order_by(TrainingExample.created_at.asc())
        )
        training_example_ids = list(result.scalars().all())

    for training_example_id in training_example_ids:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(TrainingExample)
                .join(WisdomEntry, TrainingExample.wisdom_entry_id == WisdomEntry.id)
                .where(TrainingExample.id == training_example_id)
                .where(WisdomEntry.principle_status == "approved")
            )
            training_example = result.scalar_one_or_none()
            if training_example is None:
                total_skipped += 1
                continue
            if training_example.dataset_audit_issues:
                total_skipped += 1
                continue
            if training_example.approved_for_finetune:
                total_skipped += 1
                continue

            training_example.approved_for_finetune = True
            await db.commit()
            total_approved += 1

    print(f"done total_approved={total_approved} total_skipped={total_skipped}")


def parse_args() -> argparse.Namespace:
    """Parse CLI args."""

    parser = argparse.ArgumentParser(description="Approve clean examples in streaming mode.")
    parser.add_argument("--source-document-id", type=int, required=True)
    return parser.parse_args()


def main() -> None:
    """CLI entrypoint."""

    args = parse_args()
    asyncio.run(approve_clean_examples_streaming(source_document_id=args.source_document_id))


if __name__ == "__main__":
    main()
