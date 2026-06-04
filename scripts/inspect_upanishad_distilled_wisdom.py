"""Inspect Upanishad distilled wisdom output for a source document."""

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


SUSPICIOUS_PATTERN = re.compile(
    r"(these gods|thus he said|therefore these|taking hold of the bow|om\b|translated by|published by|[{}@ïÌœ]|H¥|�)",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments for Upanishad distilled wisdom inspection."""

    parser = argparse.ArgumentParser(description="Inspect Upanishad distilled wisdom.")
    parser.add_argument(
        "--source-document-id",
        type=int,
        default=None,
        help="Optional source document ID. Defaults to the most recent source document.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=12,
        help="Number of sampled records to print per Upanishad group.",
    )
    return parser.parse_args()


async def inspect_upanishad_distilled_wisdom(args: argparse.Namespace) -> None:
    """Print a summary of Upanishad distilled wisdom for a source document."""

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
        print(f"total entries: {len(wisdom_entries)}")

        with_distilled = [entry for entry in wisdom_entries if entry.distilled_wisdom]
        blank_distilled = [entry for entry in wisdom_entries if not entry.distilled_wisdom]
        print(f"entries with distilled_wisdom: {len(with_distilled)}")
        print(f"blank distilled_wisdom count: {len(blank_distilled)}")

        repeated = Counter(entry.distilled_wisdom for entry in with_distilled if entry.distilled_wisdom)
        print("\ntop repeated distilled_wisdom values:")
        repeated_items = [(text, count) for text, count in repeated.most_common(15) if count > 1]
        if repeated_items:
            for text, count in repeated_items:
                print(f"- {count}x {text}")
        else:
            print("none")

        print("\nrepeated above threshold (>2):")
        above_threshold = [(text, count) for text, count in repeated.most_common() if count > 2]
        if above_threshold:
            for text, count in above_threshold[:20]:
                print(f"- {count}x {text}")
        else:
            print("none")

        approved_count = sum(1 for entry in wisdom_entries if entry.principle_status == "approved")
        print(f"\napproved count after quality refinement: {approved_count}")

        print("\nsamples by Upanishad:")
        rng = random.Random(42)
        grouped: dict[str, list[WisdomEntry]] = {}
        for entry in wisdom_entries:
            grouped.setdefault(entry.book_title or "unknown", []).append(entry)

        for book_title in sorted(grouped):
            print(f"\n{book_title}:")
            entries = grouped[book_title]
            sample = entries if len(entries) <= args.limit else rng.sample(entries, args.limit)
            for entry in sample[: min(6, len(sample))]:
                print(
                    f"- passage={entry.verse_number} principle={entry.extracted_principle} "
                    f"distilled={entry.distilled_wisdom or '(blank)'}"
                )

        print("\nentries still blank:")
        if blank_distilled:
            for entry in blank_distilled[:20]:
                print(
                    f"- id={entry.id} book={entry.book_title} passage={entry.verse_number} "
                    f"principle={entry.extracted_principle}"
                )
        else:
            print("none")

        print("\nexamples by tag category:")
        tag_buckets = {
            "fear_death": [
                entry for entry in wisdom_entries
                if _has_tags(entry, emotional={"fear"}, philosophical={"death", "immortality"})
            ],
            "identity_confusion": [
                entry for entry in wisdom_entries
                if _has_tags(entry, emotional={"confusion", "ego"}, philosophical={"self_knowledge", "consciousness", "atman", "non_duality"})
            ],
            "desire_attachment": [
                entry for entry in wisdom_entries
                if _has_tags(entry, emotional={"desire", "attachment"})
            ],
            "teacher_student": [
                entry for entry in wisdom_entries
                if _has_tags(entry, philosophical={"teacher_student"})
            ],
            "restless_mind": [
                entry for entry in wisdom_entries
                if _has_tags(entry, emotional={"restlessness", "discipline", "self-control"}, philosophical={"meditation"})
            ],
        }
        for name, entries in tag_buckets.items():
            print(f"- {name}:")
            if not entries:
                print("  none")
                continue
            for entry in entries[:4]:
                print(
                    f"  id={entry.id} book={entry.book_title} passage={entry.verse_number} "
                    f"distilled={entry.distilled_wisdom or '(blank)'}"
                )

        print("\nexamples of varied replacements:")
        replacement_groups = [
            entries
            for entries in tag_buckets.values()
            if entries
        ]
        printed_any = False
        for entries in replacement_groups:
            unique_distilled: list[str] = []
            sample_entries: list[WisdomEntry] = []
            for entry in entries:
                if entry.distilled_wisdom and entry.distilled_wisdom not in unique_distilled:
                    unique_distilled.append(entry.distilled_wisdom)
                    sample_entries.append(entry)
                if len(sample_entries) >= 3:
                    break
            if len(sample_entries) >= 2:
                printed_any = True
                print(f"- category sample:")
                for entry in sample_entries:
                    print(
                        f"  id={entry.id} book={entry.book_title} passage={entry.verse_number} "
                        f"distilled={entry.distilled_wisdom}"
                    )
        if not printed_any:
            print("none")

        suspicious = [
            entry
            for entry in wisdom_entries
            if entry.distilled_wisdom and _is_suspicious(entry.distilled_wisdom)
        ]
        print("\nsuspicious distilled wisdom:")
        if suspicious:
            for entry in suspicious[:20]:
                print(
                    f"- id={entry.id} book={entry.book_title} passage={entry.verse_number} "
                    f"distilled={entry.distilled_wisdom}"
                )
        else:
            print("none")

        generic_outputs = [
            entry
            for entry in wisdom_entries
            if entry.distilled_wisdom and _is_generic(entry.distilled_wisdom)
        ]
        print("\nsuspicious generic outputs:")
        if generic_outputs:
            for entry in generic_outputs[:20]:
                print(
                    f"- id={entry.id} book={entry.book_title} passage={entry.verse_number} "
                    f"distilled={entry.distilled_wisdom}"
                )
        else:
            print("none")

        missing_tags = [
            entry
            for entry in wisdom_entries
            if not entry.emotional_tags or not entry.philosophical_tags
        ]
        print("\nentries missing emotional/philosophical tags:")
        if missing_tags:
            for entry in missing_tags[:20]:
                print(
                    f"- id={entry.id} book={entry.book_title} passage={entry.verse_number} "
                    f"emotional={entry.emotional_tags} philosophical={entry.philosophical_tags}"
                )
        else:
            print("none")


async def _resolve_source_document(db, source_document_id: int | None) -> SourceDocument | None:
    """Resolve the requested source document or fall back to the most recent one."""

    if source_document_id is not None:
        return await db.get(SourceDocument, source_document_id)

    result = await db.execute(select(SourceDocument).order_by(SourceDocument.created_at.desc()))
    return result.scalars().first()


def _is_suspicious(text: str) -> bool:
    """Return True when distilled wisdom still contains suspicious residue."""

    if len(text.split()) < 8 or len(text.split()) > 30:
        return True
    return bool(SUSPICIOUS_PATTERN.search(text))


def _is_generic(text: str) -> bool:
    """Return True when distilled wisdom still feels broad or repetitive."""

    lowered = text.lower()
    generic_prefixes = (
        "real learning",
        "truth becomes",
        "peace grows",
        "freedom deepens",
        "fear softens",
        "a restless mind",
    )
    return lowered.startswith(generic_prefixes)


def _has_tags(
    entry: WisdomEntry,
    emotional: set[str] | None = None,
    philosophical: set[str] | None = None,
) -> bool:
    """Return True when an entry matches any requested emotional or philosophical tag."""

    emotional_tags = {str(tag).strip().lower() for tag in (entry.emotional_tags or [])}
    philosophical_tags = {str(tag).strip().lower() for tag in (entry.philosophical_tags or [])}

    emotional_match = True if not emotional else bool(emotional_tags.intersection(emotional))
    philosophical_match = True if not philosophical else bool(philosophical_tags.intersection(philosophical))
    return emotional_match and philosophical_match


def main() -> None:
    """Entrypoint for Upanishad distilled wisdom inspection."""

    args = parse_args()
    asyncio.run(inspect_upanishad_distilled_wisdom(args))


if __name__ == "__main__":
    main()
