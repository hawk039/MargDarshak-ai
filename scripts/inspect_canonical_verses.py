"""Inspect canonical verse output for a source document."""

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
from app.models.canonical_verse import CanonicalVerse
from app.models.source_document import SourceDocument


SUSPICIOUS_PATTERN = (
    "{",
    "}",
    "@",
    "ï",
    "Ì",
    "œ",
    "H¥",
    "Chapter ",
    "The Bhagavad Gita",
)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments for the canonical verse inspector."""

    parser = argparse.ArgumentParser(description="Inspect canonical verse records.")
    parser.add_argument(
        "--source-document-id",
        type=int,
        default=None,
        help="Optional source document ID. Defaults to the most recent source document.",
    )
    return parser.parse_args()


async def inspect_canonical_verses(args: argparse.Namespace) -> None:
    """Print a summary of canonical verse extraction quality."""

    async with AsyncSessionLocal() as db:
        source_document = await _resolve_source_document(db, args.source_document_id)
        if source_document is None:
            raise ValueError("No source documents found to inspect.")

        result = await db.execute(
            select(CanonicalVerse)
            .where(CanonicalVerse.source_document_id == source_document.id)
            .order_by(CanonicalVerse.chapter_number.asc(), CanonicalVerse.verse_number.asc())
        )
        canonical_verses = list(result.scalars().all())
        if not canonical_verses:
            raise ValueError(
                f"No canonical verses found for source_document_id={source_document.id}."
            )

        print(
            f"inspecting source_document_id={source_document.id} title={source_document.title}"
        )
        print(f"total canonical verses: {len(canonical_verses)}")

        print("\nverses per chapter:")
        chapter_counts = Counter(verse.chapter_number for verse in canonical_verses)
        for chapter_number in sorted(chapter_counts):
            print(f"- chapter {chapter_number}: {chapter_counts[chapter_number]}")

        missing_verse_numbers = [
            verse for verse in canonical_verses if not verse.verse_number.strip()
        ]
        print("\nmissing verse numbers:")
        if missing_verse_numbers:
            for verse in missing_verse_numbers[:10]:
                print(f"- id={verse.id} chapter={verse.chapter_number}")
        else:
            print("none")

        rng = random.Random(42)
        sample = canonical_verses if len(canonical_verses) <= 10 else rng.sample(canonical_verses, 10)
        print("\n10 random clean verse records:")
        for verse in sample:
            print(
                f"- id={verse.id} {verse.verse_number} speaker={verse.speaker} "
                f"valid={verse.is_valid} translation={verse.english_translation[:160]}"
            )

        suspicious_records = [
            verse
            for verse in canonical_verses
            if not verse.is_valid or _has_suspicious_text(verse)
        ]
        print("\nrecords with suspicious text:")
        if suspicious_records:
            for verse in suspicious_records[:10]:
                print(
                    f"- id={verse.id} {verse.verse_number} valid={verse.is_valid} "
                    f"text={(verse.english_translation or '')[:160]}"
                )
        else:
            print("none")


async def _resolve_source_document(db, source_document_id: int | None) -> SourceDocument | None:
    """Resolve the requested source document or fall back to the most recent one."""

    if source_document_id is not None:
        return await db.get(SourceDocument, source_document_id)

    result = await db.execute(select(SourceDocument).order_by(SourceDocument.created_at.desc()))
    return result.scalars().first()


def _has_suspicious_text(canonical_verse: CanonicalVerse) -> bool:
    """Return True when a canonical verse still contains suspicious text."""

    combined_text = " ".join(
        value
        for value in [
            canonical_verse.sanskrit_text or "",
            canonical_verse.transliteration or "",
            canonical_verse.english_translation or "",
            canonical_verse.commentary or "",
        ]
        if value
    )
    return any(token in combined_text for token in SUSPICIOUS_PATTERN)


def main() -> None:
    """Entrypoint for canonical verse inspection."""

    args = parse_args()
    asyncio.run(inspect_canonical_verses(args))


if __name__ == "__main__":
    main()
