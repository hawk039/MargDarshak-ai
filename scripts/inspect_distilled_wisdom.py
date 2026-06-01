"""Inspect original verses, extracted principles, and distilled wisdom."""

from __future__ import annotations

import argparse
import asyncio
import random
import sys
from pathlib import Path

from sqlalchemy import select


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import AsyncSessionLocal
from app.models.source_document import SourceDocument
from app.models.wisdom_entry import WisdomEntry


def parse_args() -> argparse.Namespace:
    """Parse command line arguments for distilled wisdom inspection."""

    parser = argparse.ArgumentParser(description="Inspect distilled wisdom for a source document.")
    parser.add_argument(
        "--source-document-id",
        type=int,
        default=None,
        help="Optional source document ID. Defaults to the most recent source document.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of sampled records to print.",
    )
    return parser.parse_args()


async def inspect_distilled_wisdom(args: argparse.Namespace) -> None:
    """Print sampled rows showing original verse, principle, and distillation."""

    async with AsyncSessionLocal() as db:
        source_document = await _resolve_source_document(db, args.source_document_id)
        if source_document is None:
            raise ValueError("No source documents found to inspect.")

        result = await db.execute(
            select(WisdomEntry)
            .where(WisdomEntry.source_document_id == source_document.id)
            .order_by(WisdomEntry.created_at.asc())
        )
        wisdom_entries = list(result.scalars().all())
        if not wisdom_entries:
            raise ValueError(f"No wisdom entries found for source_document_id={source_document.id}.")

        print(f"inspecting source_document_id={source_document.id} title={source_document.title}")
        print(f"total wisdom entries: {len(wisdom_entries)}")

        distilled_count = sum(1 for entry in wisdom_entries if entry.distilled_wisdom)
        print(f"distilled wisdom count: {distilled_count}")

        rng = random.Random(42)
        limit = min(args.limit, len(wisdom_entries))
        sample = wisdom_entries if len(wisdom_entries) <= limit else rng.sample(wisdom_entries, limit)

        print(f"\nshowing {limit} sampled entries:")
        for entry in sample:
            print(f"\n[id={entry.id}] chapter={entry.chapter} verse={entry.verse_number}")
            print(f"original verse: {entry.original_text or '(empty)'}")
            print(f"extracted principle: {entry.extracted_principle or '(empty)'}")
            print(f"distilled wisdom: {entry.distilled_wisdom or '(empty)'}")


async def _resolve_source_document(db, source_document_id: int | None) -> SourceDocument | None:
    """Resolve the requested source document or fall back to the most recent one."""

    if source_document_id is not None:
        return await db.get(SourceDocument, source_document_id)

    result = await db.execute(select(SourceDocument).order_by(SourceDocument.created_at.desc()))
    return result.scalars().first()


def main() -> None:
    """Entrypoint for distilled wisdom inspection."""

    args = parse_args()
    asyncio.run(inspect_distilled_wisdom(args))


if __name__ == "__main__":
    main()
