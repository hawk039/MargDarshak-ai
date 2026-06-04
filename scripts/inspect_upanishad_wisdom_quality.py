"""Inspect Upanishad distilled wisdom quality refinement output."""

from __future__ import annotations

import argparse
import asyncio
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

from sqlalchemy import select


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import AsyncSessionLocal
from app.models.source_document import SourceDocument
from app.models.wisdom_entry import WisdomEntry
from app.services.upanishad_wisdom_quality_service import UpanishadWisdomQualityService


def parse_args() -> argparse.Namespace:
    """Parse command line arguments for Upanishad wisdom quality inspection."""

    parser = argparse.ArgumentParser(description="Inspect Upanishad distilled wisdom quality.")
    parser.add_argument(
        "--source-document-id",
        type=int,
        default=None,
        help="Optional source document ID. Defaults to the most recent source document.",
    )
    return parser.parse_args()


async def inspect_upanishad_wisdom_quality(args: argparse.Namespace) -> None:
    """Print a summary of Upanishad distilled wisdom quality review."""

    async with AsyncSessionLocal() as db:
        source_document = await _resolve_source_document(db, args.source_document_id)
        if source_document is None:
            raise ValueError("No source documents found to inspect.")

        result = await db.execute(
            select(WisdomEntry)
            .where(WisdomEntry.source_document_id == source_document.id)
            .order_by(WisdomEntry.book_title.asc(), WisdomEntry.id.asc())
        )
        wisdom_entries = list(result.scalars().all())
        if not wisdom_entries:
            raise ValueError(f"No wisdom entries found for source_document_id={source_document.id}.")

        quality_service = UpanishadWisdomQualityService()
        evaluated = [(entry, quality_service.evaluate_entry(entry)) for entry in wisdom_entries]

        print(f"inspecting source_document_id={source_document.id} title={source_document.title}")
        print(f"total entries: {len(wisdom_entries)}")

        status_counts = Counter(result.principle_status for _, result in evaluated)
        print(f"approved: {status_counts.get('approved', 0)}")
        print(f"needs_review: {status_counts.get('needs_review', 0)}")
        print(f"rejected: {status_counts.get('rejected', 0)}")

        print("\ncounts by Upanishad:")
        grouped_counts: dict[str, Counter[str]] = defaultdict(Counter)
        for entry, result in evaluated:
            grouped_counts[entry.book_title or "unknown"][result.principle_status] += 1
        for book_title in sorted(grouped_counts):
            counts = grouped_counts[book_title]
            print(
                f"- {book_title}: approved={counts.get('approved', 0)} "
                f"needs_review={counts.get('needs_review', 0)} rejected={counts.get('rejected', 0)}"
            )

        print("\ntop rejection reasons:")
        for reason, count in quality_service.top_reason_counts(
            [result for _, result in evaluated], "rejected"
        )[:10]:
            print(f"- {reason}: {count}")

        print("\ntop review reasons:")
        for reason, count in quality_service.top_reason_counts(
            [result for _, result in evaluated], "needs_review"
        )[:10]:
            print(f"- {reason}: {count}")

        rng = random.Random(42)
        approved_entries = [item for item in evaluated if item[1].principle_status == "approved"]
        review_entries = [item for item in evaluated if item[1].principle_status == "needs_review"]
        rejected_entries = [item for item in evaluated if item[1].principle_status == "rejected"]

        print("\n20 approved samples:")
        _print_samples(rng, approved_entries, 20)

        print("\n20 needs_review samples:")
        _print_samples(rng, review_entries, 20)

        print("\nrejected samples:")
        _print_samples(rng, rejected_entries, 20)


def _print_samples(
    rng: random.Random,
    items: list[tuple[WisdomEntry, object]],
    limit: int,
) -> None:
    """Print sampled wisdom-entry quality results."""

    if not items:
        print("none")
        return

    sample = items if len(items) <= limit else rng.sample(items, limit)
    for entry, result in sample:
        print(
            f"- id={entry.id} book={entry.book_title} passage={entry.verse_number} "
            f"score={result.principle_quality_score} status={result.principle_status} "
            f"distilled={entry.distilled_wisdom or '(blank)'} reasons={result.reasons}"
        )


async def _resolve_source_document(db, source_document_id: int | None) -> SourceDocument | None:
    """Resolve the requested source document or fall back to the most recent one."""

    if source_document_id is not None:
        return await db.get(SourceDocument, source_document_id)

    result = await db.execute(select(SourceDocument).order_by(SourceDocument.created_at.desc()))
    return result.scalars().first()


def main() -> None:
    """Entrypoint for Upanishad wisdom quality inspection."""

    args = parse_args()
    asyncio.run(inspect_upanishad_wisdom_quality(args))


if __name__ == "__main__":
    main()
