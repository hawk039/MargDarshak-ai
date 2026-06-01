"""Audit training examples one row at a time with immediate commits."""

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
from app.services.training_dataset_audit_service import TrainingDatasetAuditService


async def audit_training_examples_streaming(source_document_id: int) -> None:
    """Audit examples with immediate commits and progress logging."""

    audit_service = TrainingDatasetAuditService()

    async with AsyncSessionLocal() as db:
        corpus_result = await db.execute(
            select(TrainingExample.id, TrainingExample.assistant_response)
            .join(WisdomEntry, TrainingExample.wisdom_entry_id == WisdomEntry.id)
            .where(WisdomEntry.source_document_id == source_document_id)
            .order_by(TrainingExample.created_at.asc())
        )
        corpus_rows = list(corpus_result.all())
        corpus_stats = audit_service.build_corpus_stats_from_rows(
            [(training_example_id, assistant_response) for training_example_id, assistant_response in corpus_rows]
        )

        result = await db.execute(
            select(TrainingExample.id)
            .join(WisdomEntry, TrainingExample.wisdom_entry_id == WisdomEntry.id)
            .where(WisdomEntry.source_document_id == source_document_id)
            .order_by(TrainingExample.created_at.asc())
        )
        training_example_ids = list(result.scalars().all())

    total_processed = 0
    for training_example_id in training_example_ids:
        async with AsyncSessionLocal() as db:
            example_result = await db.execute(
                select(TrainingExample)
                .where(TrainingExample.id == training_example_id)
            )
            training_example = example_result.scalar_one_or_none()
            if training_example is None:
                continue

            dataset_result = audit_service.audit_example_with_corpus(
                training_example_id=training_example.id,
                assistant_response=training_example.assistant_response,
                corpus_stats=corpus_stats,
            )
            training_example.dataset_quality_score = dataset_result.dataset_quality_score
            training_example.dataset_status = dataset_result.dataset_status
            training_example.dataset_audit_issues = dataset_result.issues
            await db.commit()

        total_processed += 1
        if total_processed % 25 == 0:
            print(f"audited={total_processed}")

    print(f"done total_audited={total_processed}")


def parse_args() -> argparse.Namespace:
    """Parse CLI args."""

    parser = argparse.ArgumentParser(description="Audit training examples in streaming mode.")
    parser.add_argument("--source-document-id", type=int, required=True)
    return parser.parse_args()


def main() -> None:
    """CLI entrypoint."""

    args = parse_args()
    asyncio.run(audit_training_examples_streaming(source_document_id=args.source_document_id))


if __name__ == "__main__":
    main()
