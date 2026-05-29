"""Inspect training dataset audit results for one source document."""

from __future__ import annotations

import argparse
import asyncio
from collections import Counter
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.source_document import SourceDocument
from app.models.training_example import TrainingExample
from app.models.wisdom_entry import WisdomEntry
from app.services.training_dataset_audit_service import TrainingDatasetAuditService


async def inspect_dataset_audit(source_document_id: int) -> None:
    """Print dataset audit summaries for one source document."""

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
        result_by_id = {audit_result.training_example_id: audit_result for audit_result in audit_results}

        approved_examples = [
            example
            for example in training_examples
            if (example.dataset_status or "needs_review") == "approved"
        ]
        review_examples = [
            example
            for example in training_examples
            if (example.dataset_status or "needs_review") == "needs_review"
        ]
        rejected_examples = [
            example
            for example in training_examples
            if (example.dataset_status or "needs_review") == "rejected"
        ]

        issue_counter: Counter[str] = Counter()
        for audit_result in audit_results:
            if audit_result.dataset_status != "approved":
                issue_counter.update(audit_result.issues)

        print(f"inspecting source_document_id={source_document_id} title={source_document.title}")
        print(f"total examples: {len(training_examples)}")
        print(f"approved: {len(approved_examples)}")
        print(f"needs_review: {len(review_examples)}")
        print(f"rejected: {len(rejected_examples)}")

        print("\ntop rejection reasons:")
        if issue_counter:
            for issue, count in issue_counter.most_common(10):
                print(f"- {issue}: {count}")
        else:
            print("- none")

        print("\n20 approved examples:")
        if approved_examples:
            for example in approved_examples[:20]:
                print(
                    f"- id={example.id} score={example.dataset_quality_score} "
                    f"status={example.dataset_status} response={example.assistant_response}"
                )
        else:
            print("- none")

        print("\n20 needs_review examples:")
        if review_examples:
            for example in review_examples[:20]:
                audit_result = result_by_id[example.id]
                print(
                    f"- id={example.id} score={example.dataset_quality_score} "
                    f"issues={','.join(audit_result.issues) or 'none'} "
                    f"response={example.assistant_response}"
                )
        else:
            print("- none")

        print("\nduplicate opening phrases:")
        opening_distribution = audit_service.opening_phrase_distribution(training_examples)
        duplicates = [(opening, count) for opening, count in opening_distribution if count > 1]
        if duplicates:
            for opening, count in duplicates[:20]:
                print(f"- {count}x {opening}")
        else:
            print("- none")


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(description="Inspect training dataset audit results.")
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
    asyncio.run(inspect_dataset_audit(args.source_document_id))


if __name__ == "__main__":
    main()
