"""Approve high-confidence audited training examples for export."""

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


async def approve_candidates(source_document_id: int, batch_size: int) -> None:
    """Approve only clean dataset candidates for export."""

    batch_number = 0
    total_approved = 0

    while True:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(TrainingExample)
                .join(WisdomEntry, TrainingExample.wisdom_entry_id == WisdomEntry.id)
                .where(WisdomEntry.source_document_id == source_document_id)
                .where(WisdomEntry.principle_status == "approved")
                .where(TrainingExample.dataset_status == "approved")
                .where(TrainingExample.dataset_quality_score >= 85)
                .where(TrainingExample.approved_for_finetune.is_(False))
                .order_by(TrainingExample.created_at.asc())
                .limit(batch_size)
            )
            training_examples = list(result.scalars().all())
            if not training_examples:
                break

            approved_in_batch = 0
            for training_example in training_examples:
                if training_example.dataset_audit_issues:
                    continue
                training_example.approved_for_finetune = True
                approved_in_batch += 1

            await db.commit()

        batch_number += 1
        total_approved += approved_in_batch
        print(f"batch={batch_number} approved={approved_in_batch} total_so_far={total_approved}")

    print(f"done total_approved={total_approved}")


def parse_args() -> argparse.Namespace:
    """Parse CLI args."""

    parser = argparse.ArgumentParser(description="Approve strict dataset candidates.")
    parser.add_argument("--source-document-id", type=int, required=True)
    parser.add_argument("--batch-size", type=int, default=50)
    return parser.parse_args()


def main() -> None:
    """CLI entrypoint."""

    args = parse_args()
    asyncio.run(approve_candidates(source_document_id=args.source_document_id, batch_size=args.batch_size))


if __name__ == "__main__":
    main()
