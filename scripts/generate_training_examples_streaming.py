"""Generate training examples one wisdom entry at a time."""

from __future__ import annotations

import argparse
import asyncio
import sys
from collections import Counter
from pathlib import Path

from sqlalchemy import select

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import AsyncSessionLocal
from app.models.training_example import TrainingExample
from app.models.wisdom_entry import WisdomEntry
from app.services.training_data_generation_service import TrainingDataGenerationService


async def generate_training_examples_streaming(
    source_document_id: int,
    limit: int | None,
) -> None:
    """Generate training examples with immediate commits and minimal memory usage."""

    service = TrainingDataGenerationService()
    opening_counts: Counter[str] = Counter()
    sentence_counts: Counter[str] = Counter()
    normalized_responses: list[str] = []

    async with AsyncSessionLocal() as db:
        existing_result = await db.execute(
            select(TrainingExample.assistant_response)
            .join(WisdomEntry, TrainingExample.wisdom_entry_id == WisdomEntry.id)
            .where(WisdomEntry.source_document_id == source_document_id)
        )
        existing_responses = list(existing_result.scalars().all())
        for response in existing_responses:
            opening_counts[service._opening_key(response)] += 1
            normalized_responses.append(service._normalize_response(response))

    total_generated = 0
    total_skipped = 0

    async with AsyncSessionLocal() as db:
        query = (
            select(WisdomEntry)
            .where(WisdomEntry.source_document_id == source_document_id)
            .where(WisdomEntry.principle_status == "approved")
            .where(WisdomEntry.confidence_score >= 80)
            .order_by(WisdomEntry.created_at.asc())
        )
        if limit is not None:
            query = query.limit(limit)

        result = await db.execute(query)
        wisdom_entries = list(result.scalars().all())

    for index, wisdom_entry in enumerate(wisdom_entries, start=1):
        if not service.is_training_eligible(wisdom_entry):
            total_skipped += 1
            print(f"entry={index} wisdom_entry_id={wisdom_entry.id} skipped=ineligible")
            continue

        async with AsyncSessionLocal() as db:
            existing_result = await db.execute(
                select(TrainingExample.id).where(TrainingExample.wisdom_entry_id == wisdom_entry.id)
            )
            existing_training_example_id = existing_result.scalar_one_or_none()
            if existing_training_example_id is not None:
                total_skipped += 1
                print(f"entry={index} wisdom_entry_id={wisdom_entry.id} skipped=already_exists")
                continue

            generated_examples = service._generate_examples_for_wisdom_entry(
                wisdom_entry=wisdom_entry,
                example_index=index - 1,
                opening_counts=opening_counts,
                sentence_counts=sentence_counts,
                normalized_responses=normalized_responses,
            )
            for example in generated_examples:
                db.add(
                    TrainingExample(
                        wisdom_entry_id=example.wisdom_entry_id,
                        user_problem=example.user_problem,
                        assistant_response=example.assistant_response,
                        tone=example.tone,
                        safety_category=example.safety_category,
                        source_references=example.source_references,
                        approved_for_finetune=example.approved_for_finetune,
                    )
                )
                await db.commit()
                total_generated += 1

        print(
            f"entry={index} wisdom_entry_id={wisdom_entry.id} generated={len(generated_examples)} "
            f"skipped={total_skipped} total_so_far={total_generated}"
        )

    print(f"done total_generated={total_generated} total_skipped={total_skipped}")


def parse_args() -> argparse.Namespace:
    """Parse CLI args."""

    parser = argparse.ArgumentParser(description="Generate training examples in streaming mode.")
    parser.add_argument("--source-document-id", type=int, required=True)
    parser.add_argument("--limit", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    """CLI entrypoint."""

    args = parse_args()
    asyncio.run(
        generate_training_examples_streaming(
            source_document_id=args.source_document_id,
            limit=args.limit,
        )
    )


if __name__ == "__main__":
    main()
