"""Inspect wisdom entries for a source document."""

from __future__ import annotations

import argparse
import asyncio
import random
import re
import sys
from collections import Counter
from pathlib import Path

from sqlalchemy import select


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import AsyncSessionLocal
from app.models.source_document import SourceDocument
from app.models.wisdom_entry import WisdomEntry


SUSPICIOUS_PATTERN = re.compile(r"[{}@ïÌœ]|H¥|jkhh|vijkhh|iijkhh|viiijkhh|�|Chapter\s+\d+", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments for wisdom entry inspection."""

    parser = argparse.ArgumentParser(description="Inspect wisdom entries for a source document.")
    parser.add_argument(
        "--source-document-id",
        type=int,
        default=None,
        help="Optional source document ID. Defaults to the most recent source document.",
    )
    return parser.parse_args()


async def inspect_wisdom_entries(args: argparse.Namespace) -> None:
    """Print a summary of wisdom entries for a source document."""

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

        print("\nentries per chapter:")
        chapter_counts = Counter(entry.chapter or "unknown" for entry in wisdom_entries)
        for chapter, count in sorted(chapter_counts.items(), key=lambda item: item[0]):
            print(f"- chapter {chapter}: {count}")

        rng = random.Random(42)
        sample = wisdom_entries if len(wisdom_entries) <= 10 else rng.sample(wisdom_entries, 10)
        print("\n10 random wisdom entries:")
        for entry in sample:
            print(
                f"- id={entry.id} chapter={entry.chapter} verse={entry.verse_number} "
                f"confidence={entry.confidence_score} principle={entry.extracted_principle}"
            )

        low_confidence_entries = sorted(
            wisdom_entries,
            key=lambda entry: entry.confidence_score if entry.confidence_score is not None else 9999,
        )[:10]
        print("\n10 low-confidence entries:")
        for entry in low_confidence_entries:
            print(
                f"- id={entry.id} chapter={entry.chapter} verse={entry.verse_number} "
                f"confidence={entry.confidence_score} translation={entry.translation}"
            )

        suspicious_entries = [
            entry
            for entry in wisdom_entries
            if _has_suspicious_text(entry.translation) or _has_suspicious_text(entry.commentary)
        ][:10]
        print("\nentries with suspicious translation/commentary:")
        if suspicious_entries:
            for entry in suspicious_entries:
                print(
                    f"- id={entry.id} chapter={entry.chapter} verse={entry.verse_number} "
                    f"translation={entry.translation}"
                )
        else:
            print("none")


async def _resolve_source_document(db, source_document_id: int | None) -> SourceDocument | None:
    """Resolve the requested source document or fall back to the most recent one."""

    if source_document_id is not None:
        return await db.get(SourceDocument, source_document_id)

    result = await db.execute(select(SourceDocument).order_by(SourceDocument.created_at.desc()))
    return result.scalars().first()


def _has_suspicious_text(text: str | None) -> bool:
    """Return True when text contains suspicious parser residue."""

    if not text:
        return False
    return bool(SUSPICIOUS_PATTERN.search(text))


def main() -> None:
    """Entrypoint for wisdom entry inspection."""

    args = parse_args()
    asyncio.run(inspect_wisdom_entries(args))


if __name__ == "__main__":
    main()
