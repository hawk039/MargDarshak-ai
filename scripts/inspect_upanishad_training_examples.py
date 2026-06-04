"""Inspect Upanishad-specific training examples for a source document."""

from __future__ import annotations

import argparse
import asyncio
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from sqlalchemy import select


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import AsyncSessionLocal
from app.models.source_document import SourceDocument
from app.models.training_example import TrainingExample
from app.models.wisdom_entry import WisdomEntry


FORBIDDEN_PATTERN = re.compile(
    r"\b(kena|katha|mundaka|upanishad|chapter|passage|verse|brahman said|these gods|taking hold of the bow)\b",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect Upanishad training examples.")
    parser.add_argument("--source-document-id", type=int, default=3)
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    async with AsyncSessionLocal() as db:
        source_document = await db.get(SourceDocument, args.source_document_id)
        if source_document is None:
            raise ValueError(f"Source document id={args.source_document_id} not found.")

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
        by_book: dict[str, int] = defaultdict(int)
        user_problem_counts = Counter()
        opening_counts = Counter()
        forbidden_examples: list[tuple[TrainingExample, WisdomEntry]] = []

        for example, wisdom_entry in rows:
            by_book[wisdom_entry.book_title or "unknown"] += 1
            user_problem_counts[example.user_problem] += 1
            opening_counts[_opening_key(example.assistant_response)] += 1
            if FORBIDDEN_PATTERN.search(example.assistant_response):
                forbidden_examples.append((example, wisdom_entry))

        print(f"inspecting source_document_id={args.source_document_id} title={source_document.title}")
        print(f"total generated: {len(examples)}")

        print("\nexamples per Upanishad:")
        for book_title in sorted(by_book):
            print(f"- {book_title}: {by_book[book_title]}")

        duplicates = [(text, count) for text, count in user_problem_counts.most_common() if count > 1]
        print("\nduplicate user problems:")
        if duplicates:
            for text, count in duplicates[:20]:
                print(f"- {count}x {text}")
        else:
            print("none")

        repeated_openings = [(text, count) for text, count in opening_counts.most_common() if count > 1]
        print("\nrepeated openings:")
        if repeated_openings:
            for text, count in repeated_openings[:20]:
                print(f"- {count}x {text}")
        else:
            print("none")

        rng = random.Random(42)
        sample_rows = rows if len(rows) <= 12 else rng.sample(rows, 12)
        print("\nsample examples:")
        for example, wisdom_entry in sample_rows:
            print(
                f"- id={example.id} book={wisdom_entry.book_title} passage={wisdom_entry.verse_number}\n"
                f"  problem={example.user_problem}\n"
                f"  response={example.assistant_response}\n"
            )

        print("\nexamples with forbidden phrases:")
        if forbidden_examples:
            for example, wisdom_entry in forbidden_examples[:20]:
                print(
                    f"- id={example.id} book={wisdom_entry.book_title} passage={wisdom_entry.verse_number} "
                    f"response={example.assistant_response}"
                )
        else:
            print("none")


def _opening_key(response: str) -> str:
    words = response.split()
    return " ".join(words[:10]).lower()


if __name__ == "__main__":
    asyncio.run(main())
