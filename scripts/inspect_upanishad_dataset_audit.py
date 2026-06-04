"""Inspect Upanishad training-example audit results."""

from __future__ import annotations

import argparse
import asyncio
import random
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect Upanishad dataset audit.")
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
        if not rows:
            raise ValueError("No Upanishad training examples found.")

        examples = [row[0] for row in rows]
        status_counts = Counter(example.dataset_status for example in examples)
        issue_counts = Counter(issue for example in examples for issue in (example.dataset_audit_issues or []))
        opening_counts = Counter(" ".join(example.assistant_response.split()[:10]).lower() for example in examples)
        problem_counts = Counter(example.user_problem for example in examples)
        exportable_count = sum(
            1
            for example, wisdom_entry in rows
            if example.approved_for_finetune
            and example.dataset_status == "approved"
            and wisdom_entry.principle_status == "approved"
        )

        print(f"total examples: {len(examples)}")
        print(f"approved: {status_counts.get('approved', 0)}")
        print(f"needs_review: {status_counts.get('needs_review', 0)}")
        print(f"rejected: {status_counts.get('rejected', 0)}")
        print(f"exportable count: {exportable_count}")

        print("\nrepeated openings:")
        repeated_openings = [(text, count) for text, count in opening_counts.most_common() if count > 1]
        if repeated_openings:
            for text, count in repeated_openings[:20]:
                print(f"- {count}x {text}")
        else:
            print("none")

        print("\nduplicate user problems:")
        duplicates = [(text, count) for text, count in problem_counts.most_common() if count > 1]
        if duplicates:
            for text, count in duplicates[:20]:
                print(f"- {count}x {text}")
        else:
            print("none")

        print("\ntop audit issues:")
        if issue_counts:
            for issue, count in issue_counts.most_common(15):
                print(f"- {issue}: {count}")
        else:
            print("none")

        rng = random.Random(42)
        approved_examples = [row for row in rows if row[0].dataset_status == "approved"]
        review_examples = [row for row in rows if row[0].dataset_status == "needs_review"]

        print("\nsample approved examples:")
        _print_samples(rng, approved_examples, 10)

        print("\nsample needs_review examples:")
        _print_samples(rng, review_examples, 10)


def _print_samples(
    rng: random.Random,
    rows: list[tuple[TrainingExample, WisdomEntry]],
    limit: int,
) -> None:
    if not rows:
        print("none")
        return
    sample = rows if len(rows) <= limit else rng.sample(rows, limit)
    for example, wisdom_entry in sample:
        print(
            f"- id={example.id} book={wisdom_entry.book_title} passage={wisdom_entry.verse_number} "
            f"status={example.dataset_status} score={example.dataset_quality_score}\n"
            f"  problem={example.user_problem}\n"
            f"  issues={example.dataset_audit_issues}\n"
            f"  response={example.assistant_response}\n"
        )


if __name__ == "__main__":
    asyncio.run(main())
