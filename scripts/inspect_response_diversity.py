"""Inspect response diversity for generated training examples."""

from __future__ import annotations

import argparse
import asyncio
import random
import sys
from pathlib import Path

from difflib import SequenceMatcher
from sqlalchemy import select

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import AsyncSessionLocal
from app.models.source_document import SourceDocument
from app.models.training_example import TrainingExample
from app.models.wisdom_entry import WisdomEntry
from app.services.training_dataset_audit_service import TrainingDatasetAuditService


SIMILARITY_WARNING_THRESHOLD = 0.92


async def inspect_response_diversity(source_document_id: int) -> None:
    """Print diversity diagnostics for one source document's training examples."""

    async with AsyncSessionLocal() as db:
        source_document = await db.get(SourceDocument, source_document_id)
        if source_document is None:
            print(f"source document {source_document_id} not found")
            return

        result = await db.execute(
            select(TrainingExample)
            .join(WisdomEntry, TrainingExample.wisdom_entry_id == WisdomEntry.id)
            .where(WisdomEntry.source_document_id == source_document_id)
            .order_by(TrainingExample.created_at.asc())
        )
        training_examples = list(result.scalars().all())
        if not training_examples:
            print(f"no training examples found for source_document_id={source_document_id}")
            return

        audit_service = TrainingDatasetAuditService()
        opening_distribution = audit_service.opening_phrase_distribution(training_examples)
        average_length = sum(len(example.assistant_response.split()) for example in training_examples) / len(
            training_examples
        )
        duplicate_warnings = _find_similar_pairs(training_examples)

        print(f"inspecting source_document_id={source_document_id} title={source_document.title}")
        print("\ntop 20 opening phrases:")
        for opening, count in opening_distribution[:20]:
            print(f"- {count}x {opening}")

        print("\nrepeated opening counts (>5):")
        repeated_openings = [(opening, count) for opening, count in opening_distribution if count > 5]
        if repeated_openings:
            for opening, count in repeated_openings[:20]:
                print(f"- {count}x {opening}")
        else:
            print("- none")

        print(f"\naverage response length: {average_length:.2f} words")

        print("\nduplicate/similar response warnings:")
        if duplicate_warnings:
            for left_id, right_id, similarity in duplicate_warnings[:20]:
                print(f"- ids={left_id}/{right_id} similarity={similarity:.3f}")
        else:
            print("- none")

        print("\n20 random examples:")
        sample = random.Random(source_document_id).sample(
            training_examples,
            min(20, len(training_examples)),
        )
        for example in sample:
            print(f"- id={example.id} response={example.assistant_response}")


def _find_similar_pairs(training_examples: list[TrainingExample]) -> list[tuple[int, int, float]]:
    """Return a short list of similarity warnings."""

    warnings: list[tuple[int, int, float]] = []
    normalized = [
        (example.id, _normalize_text(example.assistant_response))
        for example in training_examples
    ]
    for index, (left_id, left_text) in enumerate(normalized):
        for right_id, right_text in normalized[index + 1 :]:
            similarity = SequenceMatcher(None, left_text, right_text).ratio()
            if similarity >= SIMILARITY_WARNING_THRESHOLD:
                warnings.append((left_id, right_id, similarity))
    return warnings


def _normalize_text(text: str) -> str:
    """Return normalized response text for similarity comparison."""

    lowered = text.lower()
    lowered = " ".join(lowered.split())
    return lowered


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(description="Inspect response diversity.")
    parser.add_argument(
        "--source-document-id",
        type=int,
        required=True,
        help="Source document ID to inspect.",
    )
    return parser.parse_args()


def main() -> None:
    """CLI entrypoint."""

    args = parse_args()
    asyncio.run(inspect_response_diversity(args.source_document_id))


if __name__ == "__main__":
    main()
