"""Inspect corpus-level repetition signals for one source document."""

from __future__ import annotations

import argparse
import asyncio
from collections import Counter, defaultdict
from pathlib import Path
import sys

from sqlalchemy import select

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import AsyncSessionLocal
from app.models.source_document import SourceDocument
from app.models.training_example import TrainingExample
from app.models.wisdom_entry import WisdomEntry
from app.services.training_dataset_audit_service import (
    REPEATED_OPENING_THRESHOLD,
    TrainingDatasetAuditService,
)


async def inspect_corpus_repetition(source_document_id: int) -> None:
    """Print corpus-level repetition summaries for one source document."""

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
        audit_results = audit_service.audit_examples(training_examples)
        audit_result_by_id = {audit_result.training_example_id: audit_result for audit_result in audit_results}
        corpus_stats = audit_service.build_corpus_stats(training_examples)

        top_openings = audit_service.opening_phrase_distribution(training_examples)[:20]
        repeated_openings = [
            (opening, count)
            for opening, count in audit_service.opening_phrase_distribution(training_examples)
            if count > REPEATED_OPENING_THRESHOLD
        ]

        fingerprint_groups: defaultdict[str, list[int]] = defaultdict(list)
        for training_example in training_examples:
            fingerprint = audit_service.response_fingerprint(training_example.assistant_response)
            if fingerprint:
                fingerprint_groups[fingerprint].append(training_example.id)
        duplicate_fingerprint_groups = [
            (fingerprint, ids)
            for fingerprint, ids in fingerprint_groups.items()
            if len(ids) > 2
        ]
        duplicate_fingerprint_groups.sort(key=lambda item: len(item[1]), reverse=True)

        affected_examples = [
            training_example
            for training_example in training_examples
            if any(
                issue in {"repeated_opening_phrase", "near_duplicate_response", "repeated_sentence_pattern"}
                for issue in audit_result_by_id[training_example.id].issues
            )
        ]

        status_counts = Counter((training_example.dataset_status or "needs_review") for training_example in training_examples)

        print(f"inspecting source_document_id={source_document_id} title={source_document.title}")
        print(f"total examples: {len(training_examples)}")
        print(f"approved: {status_counts.get('approved', 0)}")
        print(f"needs_review: {status_counts.get('needs_review', 0)}")
        print(f"rejected: {status_counts.get('rejected', 0)}")

        print("\ntop 20 openings:")
        for opening, count in top_openings:
            print(f"- {count}x {opening}")

        print("\nopenings above threshold:")
        if repeated_openings:
            for opening, count in repeated_openings[:20]:
                print(f"- {count}x {opening}")
        else:
            print("- none")

        print("\nduplicate fingerprint groups:")
        if duplicate_fingerprint_groups:
            for fingerprint, ids in duplicate_fingerprint_groups[:20]:
                print(f"- {len(ids)} examples | ids={ids[:10]} | fingerprint={fingerprint}")
        else:
            print("- none")

        print("\nexamples affected by repetition issues:")
        if affected_examples:
            for training_example in affected_examples[:20]:
                audit_result = audit_result_by_id[training_example.id]
                print(
                    f"- id={training_example.id} status={training_example.dataset_status} "
                    f"issues={','.join(audit_result.issues)} opening={audit_result.opening_phrase}"
                )
        else:
            print("- none")

        print("\ncorpus counts:")
        print(f"- unique openings: {len(corpus_stats.opening_counts)}")
        print(f"- repeated sentence patterns: {sum(1 for count in corpus_stats.repeated_sentence_counts.values() if count > 8)}")
        print(
            f"- duplicate fingerprints above threshold: "
            f"{sum(1 for count in corpus_stats.response_fingerprint_counts.values() if count > 2)}"
        )


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(description="Inspect corpus repetition signals.")
    parser.add_argument("--source-document-id", type=int, required=True)
    return parser.parse_args()


def main() -> None:
    """CLI entrypoint."""

    args = parse_args()
    asyncio.run(inspect_corpus_repetition(args.source_document_id))


if __name__ == "__main__":
    main()
