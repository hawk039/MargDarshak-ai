"""Audit training examples in SQLite-safe batches."""

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


async def audit_batched(source_document_id: int, batch_size: int) -> None:
    """Audit examples in batches while keeping transactions short."""

    audit_service = TrainingDatasetAuditService()

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(TrainingExample)
            .join(WisdomEntry, TrainingExample.wisdom_entry_id == WisdomEntry.id)
            .where(WisdomEntry.source_document_id == source_document_id)
            .order_by(TrainingExample.created_at.asc())
        )
        all_examples = list(result.scalars().all())

    if not all_examples:
        print("no training examples found")
        return

    audit_results = audit_service.audit_examples(all_examples)
    results_by_id = {audit_result.training_example_id: audit_result for audit_result in audit_results}

    total_processed = 0
    batch_number = 0
    for offset in range(0, len(all_examples), batch_size):
        batch = all_examples[offset : offset + batch_size]
        async with AsyncSessionLocal() as db:
            ids = [example.id for example in batch]
            refresh_result = await db.execute(
                select(TrainingExample).where(TrainingExample.id.in_(ids)).order_by(TrainingExample.id.asc())
            )
            persisted_examples = list(refresh_result.scalars().all())
            for training_example in persisted_examples:
                audit_result = results_by_id[training_example.id]
                training_example.dataset_quality_score = audit_result.dataset_quality_score
                training_example.dataset_status = audit_result.dataset_status
                training_example.dataset_audit_issues = audit_result.issues
            await db.commit()

        batch_number += 1
        total_processed += len(batch)
        print(f"batch={batch_number} offset={offset} audited={len(batch)} total_so_far={total_processed}")

    print(f"done total_audited={total_processed}")


def parse_args() -> argparse.Namespace:
    """Parse CLI args."""

    parser = argparse.ArgumentParser(description="Audit training examples in batches.")
    parser.add_argument("--source-document-id", type=int, required=True)
    parser.add_argument("--batch-size", type=int, default=50)
    return parser.parse_args()


def main() -> None:
    """CLI entrypoint."""

    args = parse_args()
    asyncio.run(audit_batched(source_document_id=args.source_document_id, batch_size=args.batch_size))


if __name__ == "__main__":
    main()
