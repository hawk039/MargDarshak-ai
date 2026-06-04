"""Inspect Upanishad pilot canonical passage extraction output."""

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
from app.models.canonical_passage import CanonicalPassage
from app.models.source_document import SourceDocument


def parse_args() -> argparse.Namespace:
    """Parse command line arguments for the passage inspector."""

    parser = argparse.ArgumentParser(description="Inspect Upanishad pilot canonical passages.")
    parser.add_argument(
        "--source-document-id",
        type=int,
        default=None,
        help="Optional source document ID. Defaults to the most recent source document.",
    )
    return parser.parse_args()


async def inspect_upanishad_passages(args: argparse.Namespace) -> None:
    """Print a summary of stored Upanishad pilot passage extraction."""

    async with AsyncSessionLocal() as db:
        source_document = await _resolve_source_document(db, args.source_document_id)
        if source_document is None:
            raise ValueError("No source documents found to inspect.")

        result = await db.execute(
            select(CanonicalPassage)
            .where(CanonicalPassage.source_document_id == source_document.id)
            .order_by(
                CanonicalPassage.upanishad_name.asc(),
                CanonicalPassage.chapter.asc(),
                CanonicalPassage.passage_number.asc(),
            )
        )
        passages = list(result.scalars().all())
        if not passages:
            raise ValueError(
                f"No Upanishad passages found for source_document_id={source_document.id}."
            )

        print(f"inspecting source_document_id={source_document.id} title={source_document.title}")
        print(f"total passages: {len(passages)}")

        print("\npassages per Upanishad:")
        per_upanishad = Counter(passage.upanishad_name for passage in passages)
        for upanishad_name in sorted(per_upanishad):
            print(f"- {upanishad_name}: {per_upanishad[upanishad_name]}")

        valid_passages = [passage for passage in passages if passage.is_valid]
        invalid_passages = [passage for passage in passages if not passage.is_valid]
        print(f"\nvalid passages: {len(valid_passages)}")
        print(f"invalid passages: {len(invalid_passages)}")

        rng = random.Random(42)
        sample = passages if len(passages) <= 10 else rng.sample(passages, 10)
        print("\nsample passages:")
        for passage in sample:
            print(
                f"- id={passage.id} upanishad={passage.upanishad_name} "
                f"passage={passage.passage_number} section={passage.section} "
                f"valid={passage.is_valid} page={passage.page_reference} "
                f"text={passage.english_translation[:180]}"
            )


async def _resolve_source_document(db, source_document_id: int | None) -> SourceDocument | None:
    """Resolve the requested source document or fall back to the most recent one."""

    if source_document_id is not None:
        return await db.get(SourceDocument, source_document_id)

    result = await db.execute(select(SourceDocument).order_by(SourceDocument.created_at.desc()))
    return result.scalars().first()


def main() -> None:
    """Entrypoint for passage inspection."""

    args = parse_args()
    asyncio.run(inspect_upanishad_passages(args))


if __name__ == "__main__":
    main()
