#!/usr/bin/env python3
"""Validate the Marg Darshak training dataset before LoRA fine-tuning."""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path


EXPECTED_ROLES = {"system", "user", "assistant"}


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(description="Validate a JSONL chat dataset for MLX-LM fine-tuning.")
    parser.add_argument(
        "--dataset",
        default="training/data/train.jsonl",
        help="Path to the JSONL dataset file.",
    )
    parser.add_argument(
        "--sample-count",
        type=int,
        default=3,
        help="Number of random valid examples to print.",
    )
    return parser.parse_args()


def validate_record(record: object, line_number: int) -> tuple[bool, str | None]:
    """Validate one JSONL record."""

    if not isinstance(record, dict):
        return False, f"line {line_number}: top-level JSON value must be an object"

    messages = record.get("messages")
    if not isinstance(messages, list) or not messages:
        return False, f"line {line_number}: missing or invalid 'messages' list"

    seen_roles: set[str] = set()
    for message_index, message in enumerate(messages, start=1):
        if not isinstance(message, dict):
            return False, f"line {line_number}: message {message_index} must be an object"

        role = message.get("role")
        content = message.get("content")

        if role not in EXPECTED_ROLES:
            return False, f"line {line_number}: message {message_index} has invalid role {role!r}"
        if not isinstance(content, str) or not content.strip():
            return False, f"line {line_number}: message {message_index} has empty content"

        seen_roles.add(role)

    if seen_roles != EXPECTED_ROLES:
        return False, (
            f"line {line_number}: roles must include exactly system, user, assistant; "
            f"found {sorted(seen_roles)!r}"
        )

    return True, None


def main() -> int:
    """Run dataset validation."""

    args = parse_args()
    dataset_path = Path(args.dataset)

    if not dataset_path.exists():
        print(f"dataset not found: {dataset_path}", file=sys.stderr)
        return 1

    total_examples = 0
    valid_examples = 0
    invalid_examples = 0
    invalid_messages: list[str] = []
    valid_records: list[dict[str, object]] = []

    with dataset_path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                invalid_examples += 1
                invalid_messages.append(f"line {line_number}: empty line")
                continue

            total_examples += 1

            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                invalid_examples += 1
                invalid_messages.append(f"line {line_number}: invalid JSON ({exc.msg})")
                continue

            is_valid, error_message = validate_record(record, line_number)
            if not is_valid:
                invalid_examples += 1
                invalid_messages.append(error_message or f"line {line_number}: invalid record")
                continue

            valid_examples += 1
            valid_records.append(record)

    print(f"dataset: {dataset_path}")
    print(f"total examples: {total_examples}")
    print(f"total valid examples: {valid_examples}")
    print(f"total invalid examples: {invalid_examples}")

    sample_count = min(args.sample_count, len(valid_records))
    if sample_count:
        print("\nrandom valid examples:")
        for index, record in enumerate(random.sample(valid_records, sample_count), start=1):
            print(f"\nexample {index}:")
            print(json.dumps(record, ensure_ascii=False, indent=2))

    if invalid_messages:
        print("\nvalidation errors:", file=sys.stderr)
        for message in invalid_messages[:20]:
            print(f"- {message}", file=sys.stderr)
        if len(invalid_messages) > 20:
            print(f"- ... and {len(invalid_messages) - 20} more", file=sys.stderr)

    if invalid_examples > 0 or valid_examples == 0:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
