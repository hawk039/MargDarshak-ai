#!/usr/bin/env python3
"""Generate the expanded Marg Darshak dataset v1 from approved wisdom entries."""

from __future__ import annotations

import asyncio
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.database import AsyncSessionLocal
from app.services.dataset_generation_v2_service import TARGET_MAX, TARGET_MIN, DatasetGenerationV2Service

DATASET_PATH = ROOT_DIR / "datasets" / "merged" / "marg_darshak_expanded_v1.jsonl"
TRAINING_COPY = ROOT_DIR / "training" / "data" / "train_expanded_v1.jsonl"
REPORT_PATH = ROOT_DIR / "training" / "evaluation" / "expanded_v1_generation_report.md"


async def main() -> None:
    service = DatasetGenerationV2Service()
    async with AsyncSessionLocal() as db:
        result = await service.generate_dataset(db)

    service.build_jsonl(result, DATASET_PATH)
    service.build_jsonl(result, TRAINING_COPY)
    service.build_report(result, REPORT_PATH)

    print(f"total generated: {len(result.examples)}")
    print(f"scenario families: {dict(result.scenario_counts)}")
    print(f"response structures: {dict(result.structure_counts)}")
    print(f"duplicate prompts blocked: {result.duplicate_prompts}")
    print(f"duplicate responses blocked: {result.duplicate_responses}")
    print(f"skipped source entries: {result.skipped_entries}")
    print(f"dataset path: {DATASET_PATH}")
    print(f"training copy: {TRAINING_COPY}")
    print(f"report path: {REPORT_PATH}")

    if len(result.examples) < TARGET_MIN or len(result.examples) > TARGET_MAX:
        print(
            f"warning: generated dataset count {len(result.examples)} is outside target range {TARGET_MIN}-{TARGET_MAX}"
        )


if __name__ == "__main__":
    asyncio.run(main())
