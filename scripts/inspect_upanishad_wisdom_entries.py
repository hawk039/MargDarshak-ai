"""Inspect Upanishad wisdom entry output for a source document."""

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


SUSPICIOUS_PRINCIPLE_PATTERN = re.compile(
    r"^(om\b|translated by\b|published by\b|here ends\b)|[{}@ïÌœ]|H¥|�",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments for the Upanishad wisdom inspector."""

    parser = argparse.ArgumentParser(description="Inspect Upanishad wisdom entries.")
    parser.add_argument(
        "--source-document-id",
        type=int,
        default=None,
        help="Optional source document ID. Defaults to the most recent source document.",
    )
    return parser.parse_args()


async def inspect_upanishad_wisdom_entries(args: argparse.Namespace) -> None:
    """Print a summary of Upanishad wisdom entries for a source document."""

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

        print(f"inspecting source_document_id={source_document.id} title={source_document.title}")
        print(f"total wisdom entries generated: {len(wisdom_entries)}")

        print("\nentries per Upanishad:")
        per_upanishad = Counter(entry.book_title or "unknown" for entry in wisdom_entries)
        for book_title in sorted(per_upanishad):
            print(f"- {book_title}: {per_upanishad[book_title]}")

        print("\ntag distribution:")
        emotional_distribution = Counter(tag for entry in wisdom_entries for tag in entry.emotional_tags)
        philosophical_distribution = Counter(tag for entry in wisdom_entries for tag in entry.philosophical_tags)
        print("emotional:")
        for tag, count in emotional_distribution.most_common():
            print(f"- {tag}: {count}")
        print("philosophical:")
        for tag, count in philosophical_distribution.most_common():
            print(f"- {tag}: {count}")

        rng = random.Random(42)
        sample = wisdom_entries if len(wisdom_entries) <= 20 else rng.sample(wisdom_entries, 20)
        print("\n20 sample entries:")
        for entry in sample:
            print(
                f"- id={entry.id} book={entry.book_title} passage={entry.verse_number} "
                f"principle={entry.extracted_principle} tags={entry.emotional_tags}/{entry.philosophical_tags}"
            )

        missing_tag_entries = [
            entry
            for entry in wisdom_entries
            if not entry.emotional_tags or not entry.philosophical_tags
        ]
        print("\nentries with missing tags:")
        if missing_tag_entries:
            for entry in missing_tag_entries[:20]:
                print(
                    f"- id={entry.id} book={entry.book_title} passage={entry.verse_number} "
                    f"emotional={entry.emotional_tags} philosophical={entry.philosophical_tags}"
                )
        else:
            print("none")

        suspicious_entries = [
            entry
            for entry in wisdom_entries
            if _is_suspicious_principle(entry.extracted_principle)
        ]
        print("\nsuspicious principles:")
        if suspicious_entries:
            for entry in suspicious_entries[:20]:
                print(
                    f"- id={entry.id} book={entry.book_title} passage={entry.verse_number} "
                    f"principle={entry.extracted_principle}"
                )
        else:
            print("none")


async def _resolve_source_document(db, source_document_id: int | None) -> SourceDocument | None:
    """Resolve the requested source document or fall back to the most recent one."""

    if source_document_id is not None:
        return await db.get(SourceDocument, source_document_id)

    result = await db.execute(select(SourceDocument).order_by(SourceDocument.created_at.desc()))
    return result.scalars().first()


def _is_suspicious_principle(text: str | None) -> bool:
    """Return True when a generated principle still looks suspicious."""

    if not text:
        return True
    if len(text.split()) < 5:
        return True
    return bool(SUSPICIOUS_PRINCIPLE_PATTERN.search(text))


def main() -> None:
    """Entrypoint for Upanishad wisdom entry inspection."""

    args = parse_args()
    asyncio.run(inspect_upanishad_wisdom_entries(args))


if __name__ == "__main__":
    main()
