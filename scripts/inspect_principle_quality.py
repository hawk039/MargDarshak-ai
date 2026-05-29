"""Inspect principle quality status for a source document."""

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
from app.services.principle_quality_service import PrincipleQualityService


def parse_args() -> argparse.Namespace:
    """Parse command line arguments for principle quality inspection."""

    parser = argparse.ArgumentParser(description="Inspect principle quality status.")
    parser.add_argument(
        "--source-document-id",
        type=int,
        default=None,
        help="Optional source document ID. Defaults to the most recent source document.",
    )
    return parser.parse_args()


async def inspect_principle_quality(args: argparse.Namespace) -> None:
    """Print principle quality summaries for a source document."""

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

        quality_service = PrincipleQualityService()
        quality_results = [quality_service.evaluate_entry(entry) for entry in wisdom_entries]

        approved_entries = [
            entry for entry in wisdom_entries if (entry.principle_status or "needs_review") == "approved"
        ]
        needs_review_entries = [
            entry for entry in wisdom_entries if (entry.principle_status or "needs_review") == "needs_review"
        ]
        rejected_entries = [
            entry for entry in wisdom_entries if (entry.principle_status or "needs_review") == "rejected"
        ]

        print(f"inspecting source_document_id={source_document.id} title={source_document.title}")
        print(f"total principles: {len(wisdom_entries)}")
        print(f"approved count: {len(approved_entries)}")
        print(f"needs_review count: {len(needs_review_entries)}")
        print(f"rejected count: {len(rejected_entries)}")

        print("\ntop rejection reasons:")
        rejection_reasons = quality_service.top_rejection_reasons(quality_results)
        if rejection_reasons:
            for reason, count in rejection_reasons[:10]:
                print(f"- {reason}: {count}")
        else:
            print("none")

        rng = random.Random(42)
        approved_sample = approved_entries if len(approved_entries) <= 20 else rng.sample(approved_entries, 20)
        rejected_sample = rejected_entries if len(rejected_entries) <= 20 else rng.sample(rejected_entries, 20)

        print("\n20 approved examples:")
        if approved_sample:
            for entry in approved_sample:
                print(
                    f"- id={entry.id} verse={entry.verse_number} score={entry.principle_quality_score} "
                    f"confidence={entry.confidence_score} principle={entry.extracted_principle}"
                )
        else:
            print("none")

        print("\n20 rejected examples:")
        if rejected_sample:
            for entry in rejected_sample:
                print(
                    f"- id={entry.id} verse={entry.verse_number} score={entry.principle_quality_score} "
                    f"confidence={entry.confidence_score} principle={entry.extracted_principle}"
                )
        else:
            print("none")


async def _resolve_source_document(db, source_document_id: int | None) -> SourceDocument | None:
    """Resolve the requested source document or the most recent one."""

    if source_document_id is not None:
        return await db.get(SourceDocument, source_document_id)

    result = await db.execute(select(SourceDocument).order_by(SourceDocument.created_at.desc()))
    return result.scalars().first()


def main() -> None:
    """Entrypoint for principle quality inspection."""

    args = parse_args()
    asyncio.run(inspect_principle_quality(args))


if __name__ == "__main__":
    main()
