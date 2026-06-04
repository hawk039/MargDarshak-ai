"""Approve clean Upanishad training examples for finetune export."""

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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Approve clean Upanishad training examples.")
    parser.add_argument("--source-document-id", type=int, default=3)
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(TrainingExample, WisdomEntry)
            .join(WisdomEntry, TrainingExample.wisdom_entry_id == WisdomEntry.id)
            .where(WisdomEntry.source_document_id == args.source_document_id)
            .order_by(TrainingExample.id.asc())
        )
        rows = list(result.all())
        approved = 0
        skipped = 0
        for training_example, wisdom_entry in rows:
            if (
                training_example.dataset_status == "approved"
                and (training_example.dataset_quality_score or 0.0) >= 85.0
                and not training_example.dataset_audit_issues
                and wisdom_entry.principle_status == "approved"
            ):
                training_example.approved_for_finetune = True
                approved += 1
            else:
                training_example.approved_for_finetune = False
                skipped += 1
        await db.commit()
        print(f"approved={approved}")
        print(f"skipped={skipped}")


if __name__ == "__main__":
    asyncio.run(main())
