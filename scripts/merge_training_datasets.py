"""Merge validated Marg Darshak training datasets into a versioned JSONL file."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_PROMPT = (
    "You are Marg Darshak, a calm philosophical guide inspired by Indian wisdom "
    "traditions. You help users with inner battles using gentle reflection, clarity, "
    "and practical action. You are not a therapist, doctor, or religious authority."
)
EXPECTED_ROLES = {"system", "user", "assistant"}


@dataclass(slots=True)
class DatasetLoadResult:
    """Validated dataset load result."""

    path: Path
    records: list[dict]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge Marg Darshak training datasets.")
    parser.add_argument(
        "--gita",
        default="datasets/gita/marg_darshak_gita_v4.jsonl",
        help="Path to the Gita JSONL dataset.",
    )
    parser.add_argument(
        "--upanishads",
        default="datasets/upanishads/upanishads_pilot_v1.jsonl",
        help="Path to the Upanishads JSONL dataset.",
    )
    parser.add_argument(
        "--merged-output",
        default="datasets/merged/marg_darshak_merged_v1.jsonl",
        help="Path to the merged dataset JSONL output.",
    )
    parser.add_argument(
        "--train-output",
        default="training/data/train_merged_v1.jsonl",
        help="Path to the training data copy.",
    )
    parser.add_argument(
        "--metadata-output",
        default="datasets/metadata/merged_v1.md",
        help="Path to the metadata markdown output.",
    )
    return parser.parse_args()


def load_dataset(path: Path) -> DatasetLoadResult:
    """Load and validate a JSONL dataset."""

    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    records: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number} contains invalid JSON: {exc.msg}") from exc

            validate_record(record, path, line_number)
            records.append(record)

    if not records:
        raise ValueError(f"{path} contains no valid records.")
    return DatasetLoadResult(path=path, records=records)


def validate_record(record: object, path: Path, line_number: int) -> None:
    """Validate one chat-format JSONL record."""

    if not isinstance(record, dict):
        raise ValueError(f"{path}:{line_number} must be a JSON object.")

    messages = record.get("messages")
    if not isinstance(messages, list) or not messages:
        raise ValueError(f"{path}:{line_number} must contain a non-empty 'messages' list.")

    roles = []
    for index, message in enumerate(messages, start=1):
        if not isinstance(message, dict):
            raise ValueError(f"{path}:{line_number} message {index} must be an object.")
        role = message.get("role")
        content = message.get("content")
        if role not in EXPECTED_ROLES:
            raise ValueError(f"{path}:{line_number} message {index} has invalid role {role!r}.")
        if not isinstance(content, str) or not content.strip():
            raise ValueError(f"{path}:{line_number} message {index} has empty content.")
        roles.append(role)

    if set(roles) != EXPECTED_ROLES:
        raise ValueError(
            f"{path}:{line_number} must include system, user, and assistant messages exactly once each."
        )

    if messages[0].get("role") != "system":
        raise ValueError(f"{path}:{line_number} must begin with a system message.")


def canonical_record(record: dict) -> str:
    """Return a canonical serialized record for exact duplicate detection."""

    return json.dumps(record, ensure_ascii=False, sort_keys=True)


def build_metadata(
    gita_result: DatasetLoadResult,
    upanishad_result: DatasetLoadResult,
    merged_records: list[dict],
    duplicate_count: int,
    duplicate_prompt_count: int,
    duplicate_response_count: int,
) -> str:
    """Build merged dataset metadata markdown."""

    return "\n".join(
        [
            "Dataset: Marg Darshak Merged v1",
            f"Date: {date.today().isoformat()}",
            "Purpose: Marg Darshak LoRA v2",
            "",
            "Source datasets:",
            f"- {gita_result.path.as_posix()}",
            f"- {upanishad_result.path.as_posix()}",
            "",
            "Counts:",
            f"- Gita count: {len(gita_result.records)}",
            f"- Upanishads count: {len(upanishad_result.records)}",
            f"- Merged count: {len(merged_records)}",
            f"- Exact duplicate count removed: {duplicate_count}",
            f"- Duplicate user prompt groups detected: {duplicate_prompt_count}",
            f"- Duplicate assistant response groups detected: {duplicate_response_count}",
            "",
            "System prompt:",
            f"- {SYSTEM_PROMPT}",
        ]
    ) + "\n"


def main() -> int:
    args = parse_args()

    gita_path = PROJECT_ROOT / args.gita
    upanishad_path = PROJECT_ROOT / args.upanishads
    merged_output = PROJECT_ROOT / args.merged_output
    train_output = PROJECT_ROOT / args.train_output
    metadata_output = PROJECT_ROOT / args.metadata_output

    gita_result = load_dataset(gita_path)
    upanishad_result = load_dataset(upanishad_path)

    seen: set[str] = set()
    merged_records: list[dict] = []
    duplicate_count = 0

    for record in [*gita_result.records, *upanishad_result.records]:
        canonical = canonical_record(record)
        if canonical in seen:
            duplicate_count += 1
            continue
        seen.add(canonical)
        merged_records.append(record)

    prompt_counts = Counter(record["messages"][1]["content"] for record in merged_records)
    response_counts = Counter(record["messages"][2]["content"] for record in merged_records)
    duplicate_prompt_count = sum(1 for count in prompt_counts.values() if count > 1)
    duplicate_response_count = sum(1 for count in response_counts.values() if count > 1)

    merged_output.parent.mkdir(parents=True, exist_ok=True)
    train_output.parent.mkdir(parents=True, exist_ok=True)
    metadata_output.parent.mkdir(parents=True, exist_ok=True)

    jsonl_content = "\n".join(json.dumps(record, ensure_ascii=False) for record in merged_records)
    merged_output.write_text(jsonl_content, encoding="utf-8")
    train_output.write_text(jsonl_content, encoding="utf-8")
    metadata_output.write_text(
        build_metadata(
            gita_result=gita_result,
            upanishad_result=upanishad_result,
            merged_records=merged_records,
            duplicate_count=duplicate_count,
            duplicate_prompt_count=duplicate_prompt_count,
            duplicate_response_count=duplicate_response_count,
        ),
        encoding="utf-8",
    )

    print(f"Gita count: {len(gita_result.records)}")
    print(f"Upanishads count: {len(upanishad_result.records)}")
    print(f"Merged count: {len(merged_records)}")
    print(f"Duplicate count: {duplicate_count}")
    print(f"Duplicate user prompt groups: {duplicate_prompt_count}")
    print(f"Duplicate assistant response groups: {duplicate_response_count}")
    print(f"Merged output: {merged_output}")
    print(f"Training copy: {train_output}")
    print(f"Metadata: {metadata_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
