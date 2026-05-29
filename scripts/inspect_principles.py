"""Inspect extracted wisdom principles for a source document."""

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


GENERIC_PATTERN = re.compile(
    r"^(o [a-z-]+!?|arjuna said|sanjaya said|krishna said|dhrutarashtra said)\b",
    re.IGNORECASE,
)
SUSPICIOUS_PATTERN = re.compile(r"[{}@ïÌœ]|H¥|jkhh|vijkhh|iijkhh|viiijkhh|�|chapter\s+\d+", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments for principle inspection."""

    parser = argparse.ArgumentParser(description="Inspect extracted wisdom principles.")
    parser.add_argument(
        "--source-document-id",
        type=int,
        default=None,
        help="Optional source document ID. Defaults to the most recent source document.",
    )
    return parser.parse_args()


async def inspect_principles(args: argparse.Namespace) -> None:
    """Print principle summaries for a source document."""

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
        print(f"total entries: {len(wisdom_entries)}")

        tag_distribution = Counter()
        for entry in wisdom_entries:
            tag_distribution.update(entry.emotional_tags)
            tag_distribution.update(entry.philosophical_tags)
        print("\ntag distribution:")
        for tag, count in tag_distribution.most_common():
            print(f"- {tag}: {count}")

        rng = random.Random(42)
        sample = wisdom_entries if len(wisdom_entries) <= 20 else rng.sample(wisdom_entries, 20)
        print("\n20 random principles:")
        for entry in sample:
            print(f"- id={entry.id} verse={entry.verse_number} principle={entry.extracted_principle}")

        missing_tag_entries = [
            entry for entry in wisdom_entries if not entry.emotional_tags and not entry.philosophical_tags
        ][:10]
        print("\n10 entries with missing tags:")
        if missing_tag_entries:
            for entry in missing_tag_entries:
                print(f"- id={entry.id} verse={entry.verse_number} principle={entry.extracted_principle}")
        else:
            print("none")

        suspicious_entries = [
            entry
            for entry in wisdom_entries
            if _is_suspicious_principle(entry.extracted_principle)
        ][:10]
        print("\n10 suspicious/generic principles:")
        if suspicious_entries:
            for entry in suspicious_entries:
                print(f"- id={entry.id} verse={entry.verse_number} principle={entry.extracted_principle}")
        else:
            print("none")


async def _resolve_source_document(db, source_document_id: int | None) -> SourceDocument | None:
    """Resolve the requested source document or the most recent one."""

    if source_document_id is not None:
        return await db.get(SourceDocument, source_document_id)

    result = await db.execute(select(SourceDocument).order_by(SourceDocument.created_at.desc()))
    return result.scalars().first()


def _is_suspicious_principle(principle: str | None) -> bool:
    """Return True when a principle looks generic or suspicious."""

    if not principle:
        return True
    normalized = principle.strip()
    if len(normalized.split()) < 10:
        return True
    if GENERIC_PATTERN.match(normalized):
        return True
    if SUSPICIOUS_PATTERN.search(normalized):
        return True
    return False


def main() -> None:
    """Entrypoint for principle inspection."""

    args = parse_args()
    asyncio.run(inspect_principles(args))


if __name__ == "__main__":
    main()
