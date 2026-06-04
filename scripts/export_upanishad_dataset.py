"""Export approved Upanishad training examples as a JSONL dataset."""

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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export Upanishad pilot dataset.")
    parser.add_argument("--source-document-id", type=int, default=3)
    parser.add_argument(
        "--output",
        default="datasets/upanishads/upanishads_pilot_v1.jsonl",
        help="Output JSONL path.",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    output_path = PROJECT_ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(TrainingExample)
            .join(WisdomEntry, TrainingExample.wisdom_entry_id == WisdomEntry.id)
            .where(WisdomEntry.source_document_id == args.source_document_id)
            .where(TrainingExample.approved_for_finetune.is_(True))
            .where(TrainingExample.dataset_status == "approved")
            .where(WisdomEntry.principle_status == "approved")
            .order_by(TrainingExample.id.asc())
        )
        training_examples = list(result.scalars().all())
        if not training_examples:
            raise ValueError("No approved Upanishad training examples found for export.")

    pipeline = GenerateTrainingDatasetPipeline()
    jsonl_lines = pipeline.run(training_examples)
    output_path.write_text("\n".join(jsonl_lines), encoding="utf-8")

    print(f"exported_examples={len(training_examples)}")
    print(f"output={output_path}")


if __name__ == "__main__":
    asyncio.run(main())
