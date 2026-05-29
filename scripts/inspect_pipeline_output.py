"""Inspect local pipeline output for a source document."""

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
from app.models.document_chunk import DocumentChunk
from app.models.source_document import SourceDocument
from app.models.training_example import TrainingExample
from app.models.wisdom_entry import WisdomEntry


def parse_args() -> argparse.Namespace:
    """Parse command line arguments for the pipeline inspection script."""

    parser = argparse.ArgumentParser(
        description="Inspect generated chunks, wisdom entries, and training examples."
    )
    parser.add_argument(
        "--source-document-id",
        type=int,
        default=None,
        help="Optional source document ID. Defaults to the most recent source document.",
    )
    return parser.parse_args()


async def inspect_output(args: argparse.Namespace) -> None:
    """Print counts and representative records for a source document."""

    async with AsyncSessionLocal() as db:
        source_document = await _resolve_source_document(db, args.source_document_id)
        if source_document is None:
            raise ValueError("No source documents found to inspect.")

        chunks = await _fetch_chunks(db, source_document.id)
        wisdom_entries = await _fetch_wisdom_entries(db, source_document.id)
        training_examples = await _fetch_training_examples(db, source_document.id)

        print(
            f"inspecting source_document_id={source_document.id} title={source_document.title}"
        )
        print(f"total chunks: {len(chunks)}")
        print(f"total wisdom entries: {len(wisdom_entries)}")
        print(f"total training examples: {len(training_examples)}")

        rng = random.Random(42)
        sampled_training_examples = _sample_items(training_examples, 5, rng)
        print("\n5 random training examples:")
        _print_training_examples(sampled_training_examples)

        examples_with_emotional_tags = [
            training_example
            for training_example in training_examples
            if training_example.wisdom_entry and training_example.wisdom_entry.emotional_tags
        ][:5]
        print("\n5 examples with emotional tags:")
        _print_training_examples(examples_with_emotional_tags)

        entries_with_missing_verse_numbers = [
            wisdom_entry for wisdom_entry in wisdom_entries if not wisdom_entry.verse_number
        ][:5]
        print("\n5 entries with missing verse numbers:")
        _print_wisdom_entries(entries_with_missing_verse_numbers)


async def _resolve_source_document(db, source_document_id: int | None) -> SourceDocument | None:
    """Resolve the requested source document or fall back to the most recent one."""

    if source_document_id is not None:
        return await db.get(SourceDocument, source_document_id)

    result = await db.execute(
        select(SourceDocument).order_by(SourceDocument.created_at.desc())
    )
    return result.scalars().first()


async def _fetch_chunks(db, source_document_id: int) -> list[DocumentChunk]:
    """Fetch document chunks for a source document."""

    result = await db.execute(
        select(DocumentChunk)
        .where(DocumentChunk.source_document_id == source_document_id)
        .order_by(DocumentChunk.chunk_index.asc())
    )
    return list(result.scalars().all())


async def _fetch_wisdom_entries(db, source_document_id: int) -> list[WisdomEntry]:
    """Fetch wisdom entries for a source document."""

    result = await db.execute(
        select(WisdomEntry)
        .where(WisdomEntry.source_document_id == source_document_id)
        .order_by(WisdomEntry.created_at.asc())
    )
    return list(result.scalars().all())


async def _fetch_training_examples(db, source_document_id: int) -> list[TrainingExample]:
    """Fetch training examples associated with a source document."""

    result = await db.execute(
        select(TrainingExample)
        .join(WisdomEntry, TrainingExample.wisdom_entry_id == WisdomEntry.id)
        .where(WisdomEntry.source_document_id == source_document_id)
        .order_by(TrainingExample.created_at.asc())
    )
    training_examples = list(result.scalars().all())

    wisdom_entry_lookup = {
        wisdom_entry.id: wisdom_entry
        for wisdom_entry in await _fetch_wisdom_entries(db, source_document_id)
    }
    for training_example in training_examples:
        training_example.wisdom_entry = wisdom_entry_lookup.get(training_example.wisdom_entry_id)
    return training_examples


def _sample_items(items: list, count: int, rng: random.Random) -> list:
    """Return a stable pseudo-random sample up to the requested count."""

    if len(items) <= count:
        return items
    return rng.sample(items, count)


def _print_training_examples(training_examples: list[TrainingExample]) -> None:
    """Print a compact view of training examples."""

    if not training_examples:
        print("none")
        return

    for training_example in training_examples:
        emotional_tags = (
            training_example.wisdom_entry.emotional_tags
            if training_example.wisdom_entry is not None
            else []
        )
        print(
            f"- id={training_example.id} wisdom_entry_id={training_example.wisdom_entry_id} "
            f"tags={emotional_tags} user_problem={training_example.user_problem}"
        )


def _print_wisdom_entries(wisdom_entries: list[WisdomEntry]) -> None:
    """Print a compact view of wisdom entries."""

    if not wisdom_entries:
        print("none")
        return

    for wisdom_entry in wisdom_entries:
        print(
            f"- id={wisdom_entry.id} chapter={wisdom_entry.chapter} "
            f"section={wisdom_entry.section} verse_number={wisdom_entry.verse_number} "
            f"principle={wisdom_entry.extracted_principle}"
        )


def main() -> None:
    """Entrypoint for the inspection script."""

    args = parse_args()
    asyncio.run(inspect_output(args))


if __name__ == "__main__":
    main()
