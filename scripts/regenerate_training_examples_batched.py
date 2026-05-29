"""Regenerate training examples in SQLite-safe batches."""

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
from app.models.wisdom_entry import WisdomEntry
from app.pipelines.generate_training_examples_pipeline import GenerateTrainingExamplesPipeline


async def regenerate_batched(
    source_document_id: int,
    batch_size: int,
    replace_existing: bool,
) -> None:
    """Generate training examples in batches for one source document."""

    pipeline = GenerateTrainingExamplesPipeline()
    total_generated = 0
    total_skipped = 0
    offset = 0
    batch_number = 0

    while True:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(WisdomEntry)
                .where(WisdomEntry.source_document_id == source_document_id)
                .where(WisdomEntry.principle_status == "approved")
                .where(WisdomEntry.confidence_score >= 80)
                .order_by(WisdomEntry.created_at.asc())
                .offset(offset)
                .limit(batch_size)
            )
            wisdom_entries = list(result.scalars().all())
            if not wisdom_entries:
                break

            eligible_entries = [
                wisdom_entry
                for wisdom_entry in wisdom_entries
                if pipeline.training_data_generation_service.is_training_eligible(wisdom_entry)
            ]
            batch_result = await pipeline.run_batched(
                wisdom_entries=eligible_entries,
                db=db,
                replace_existing=replace_existing,
                commit_every_examples=10,
            )

        batch_number += 1
        batch_skipped = batch_result.skipped_count + (len(wisdom_entries) - len(eligible_entries))
        total_generated += batch_result.generated_count
        total_skipped += batch_skipped
        print(
            f"batch={batch_number} offset={offset} "
            f"generated={batch_result.generated_count} skipped={batch_skipped} total_so_far={total_generated}"
        )
        offset += batch_size

    print(f"done total_generated={total_generated} total_skipped={total_skipped}")


def parse_args() -> argparse.Namespace:
    """Parse CLI args."""

    parser = argparse.ArgumentParser(description="Regenerate training examples in batches.")
    parser.add_argument("--source-document-id", type=int, required=True)
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--replace-existing", action="store_true")
    return parser.parse_args()


def main() -> None:
    """CLI entrypoint."""

    args = parse_args()
    asyncio.run(
        regenerate_batched(
            source_document_id=args.source_document_id,
            batch_size=args.batch_size,
            replace_existing=args.replace_existing,
        )
    )


if __name__ == "__main__":
    main()
