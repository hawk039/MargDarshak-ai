#!/usr/bin/env python3
"""Inspect the expanded Marg Darshak dataset v1 generation outputs."""

from __future__ import annotations

import argparse
import asyncio
import json
import re
from collections import Counter
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.database import AsyncSessionLocal
from app.services.dataset_generation_v2_service import DatasetGenerationV2Service

DATASET_PATH = ROOT_DIR / "datasets" / "merged" / "marg_darshak_expanded_v1.jsonl"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect the expanded_v1 dataset.")
    parser.add_argument("--sample-count", type=int, default=12, help="Number of sample examples to print.")
    return parser.parse_args()


def normalize_key(text: str) -> str:
    lowered = re.sub(r"\s+", " ", text.strip().lower())
    lowered = re.sub(r"[^\w\s]", "", lowered)
    return lowered.strip()


def first_sentence(text: str) -> str:
    return re.split(r"(?<=[.!?])\s+", text.strip(), maxsplit=1)[0].strip()


def last_sentence(text: str) -> str:
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text.strip()) if part.strip()]
    return sentences[-1] if sentences else ""


async def main() -> None:
    args = parse_args()
    service = DatasetGenerationV2Service()
    async with AsyncSessionLocal() as db:
        result = await service.generate_dataset(db)

    records = [json.loads(line) for line in DATASET_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    prompt_counter = Counter()
    response_counter = Counter()
    opening_counter = result.opening_counts
    action_counter = result.action_counts

    for record in records:
        user = next(message["content"] for message in record["messages"] if message["role"] == "user")
        assistant = next(message["content"] for message in record["messages"] if message["role"] == "assistant")
        prompt_counter[normalize_key(user)] += 1
        response_counter[normalize_key(assistant)] += 1

    print(f"total examples: {len(records)}")
    print(f"examples per scenario family: {dict(result.scenario_counts)}")
    print(f"examples per response structure: {dict(result.structure_counts)}")
    print("repeated openings:")
    for opening, count in opening_counter.most_common(10):
        if count > 1:
            print(f"  {count}x {opening}")
    print("repeated actions:")
    for action, count in action_counter.most_common(10):
        if count > 1:
            print(f"  {count}x {action}")
    duplicate_prompts = sum(count - 1 for count in prompt_counter.values() if count > 1)
    duplicate_responses = sum(count - 1 for count in response_counter.values() if count > 1)
    print(f"duplicate prompts: {duplicate_prompts}")
    print(f"duplicate responses: {duplicate_responses}")
    print("sample examples:")
    for example in result.examples[: args.sample_count]:
        print(f"- scenario_family: {example.scenario_family}")
        print(f"  response_structure: {example.response_structure}")
        print(f"  user: {example.user_prompt}")
        print(f"  assistant: {example.assistant_response}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
