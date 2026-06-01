"""Export approved training examples for one source document as JSONL."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from sqlalchemy import select

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import AsyncSessionLocal
from app.models.training_example import TrainingExample
from app.models.wisdom_entry import WisdomEntry
from app.pipelines.generate_training_dataset_pipeline import GenerateTrainingDatasetPipeline
from app.utils.file_utils import ensure_directory


async def export_training_dataset(source_document_id: int, output: str) -> None:
    """Export strict approved examples for one source document."""

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(TrainingExample)
            .join(WisdomEntry, TrainingExample.wisdom_entry_id == WisdomEntry.id)
            .where(WisdomEntry.source_document_id == source_document_id)
            .where(WisdomEntry.principle_status == "approved")
            .where(TrainingExample.dataset_status == "approved")
            .where(TrainingExample.approved_for_finetune.is_(True))
            .order_by(TrainingExample.created_at.asc())
        )
        training_examples = list(result.scalars().all())

    if not training_examples:
        raise ValueError("No approved high-quality training examples found for export.")

    pipeline = GenerateTrainingDatasetPipeline()
    jsonl_lines = pipeline.run(training_examples)

    output_path = Path(output)
    ensure_directory(str(output_path.parent))
    output_path.write_text("\n".join(jsonl_lines), encoding="utf-8")

    print(f"source_document_id={source_document_id}")
    print(f"exported_examples={len(training_examples)}")
    print(f"output={output_path}")


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(description="Export approved training dataset JSONL.")
    parser.add_argument("--source-document-id", type=int, required=True)
    parser.add_argument("--output", type=str, required=True)
    return parser.parse_args()


def main() -> None:
    """CLI entrypoint."""

    args = parse_args()
    asyncio.run(
        export_training_dataset(
            source_document_id=args.source_document_id,
            output=args.output,
        )
    )


if __name__ == "__main__":
    main()
