#!/usr/bin/env python3
"""Create a stricter merged Marg Darshak dataset v2 from Gita and Upanishad exports."""

from __future__ import annotations

import json
import random
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
GITA_DATASET = ROOT_DIR / "datasets" / "gita" / "marg_darshak_gita_v4.jsonl"
UPANISHAD_DATASET = ROOT_DIR / "datasets" / "upanishads" / "upanishads_pilot_v1.jsonl"
ANALYSIS_PATH = ROOT_DIR / "training" / "evaluation" / "merged_v1_analysis.md"

MERGED_V2_DATASET = ROOT_DIR / "datasets" / "merged" / "marg_darshak_merged_v2.jsonl"
TRAINING_COPY = ROOT_DIR / "training" / "data" / "train_merged_v2.jsonl"
METADATA_PATH = ROOT_DIR / "datasets" / "metadata" / "merged_v2.md"
REPORT_PATH = ROOT_DIR / "training" / "evaluation" / "merged_v2_dataset_cleanup_report.md"

SYSTEM_PROMPT = (
    "You are Marg Darshak, a calm philosophical guide inspired by Indian wisdom traditions. "
    "You help users with inner battles using gentle reflection, clarity, and practical action. "
    "You are not a therapist, doctor, or religious authority."
)
EXPECTED_ROLES = {"system", "user", "assistant"}
REPEATED_SCAFFOLDS = [
    "a calmer response is often",
    "that matters because",
    "it turns reflection into something you can live today",
    "that is often the turning point",
    "it helps action grow cleaner",
]
GENERIC_MOTIVATIONAL_PATTERNS = [
    "you are not alone",
    "personal growth is a journey",
    "small steps",
    "stay true to yourself",
    "the bigger picture",
]
SCRIPTURE_LEAK_PATTERNS = [
    "gita",
    "upanishad",
    "chapter ",
    "passage ",
    "verse ",
    "krishna",
    "arjuna",
    "kena",
    "katha",
    "mundaka",
]
CONCRETE_ACTION_MARKERS = [
    "write down",
    "choose one",
    "set a short timer",
    "pause and ask",
    "take ten quiet minutes",
    "pick one small",
    "name one",
    "breathe slowly",
    "reverse that pattern",
    "meet it with one calm deliberate action",
    "remove one obstacle",
    "practice one act",
    "choose one task",
    "interrupt it early",
    "take one step",
    "do the next task wholeheartedly",
    "complete one gentle grounding act",
    "name the fear plainly",
    "practice letting go",
    "take one step that expresses trust",
    "pick one impulse to delay",
    "choose one modest discipline",
    "let go of your preferred ending",
    "do it at a fixed time",
    "reverse that pattern today",
    "return to one honest grounding statement",
    "face the fact",
]


@dataclass
class Record:
    source_name: str
    line_number: int
    record: dict[str, Any]
    system: str
    user: str
    assistant: str
    user_key: str
    user_near_key: str
    assistant_key: str
    prompt_quality_score: int = 0
    response_quality_score: int = 0
    repetition_score: int = 0
    actionability_score: int = 0
    final_score: int = 0
    keep: bool = False
    removal_reasons: list[str] = field(default_factory=list)
    duplicate_group_rank: int = 0


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def normalize_text(text: str) -> str:
    lowered = normalize_space(text).lower()
    lowered = re.sub(r"[^\w\s]", "", lowered)
    return normalize_space(lowered)


def near_prompt_key(text: str) -> str:
    normalized = normalize_text(text)
    normalized = re.sub(r"\b(i feel|i am|i keep|i know|part of me|my mind|how do i|what should i do|i want to)\b", "", normalized)
    normalized = re.sub(r"\b(really|very|just|still|right now|today)\b", "", normalized)
    words = [word for word in normalized.split() if word]
    return " ".join(words[:10])


def sentence_split(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", normalize_space(text))
    return [part.strip() for part in parts if part.strip()]


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w']+\b", text))


def first_n_words(text: str, count: int) -> str:
    words = re.findall(r"\b[\w']+\b", text.lower())
    return " ".join(words[:count])


def load_jsonl(path: Path, source_name: str) -> list[Record]:
    records: list[Record] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            data = json.loads(line)
            messages = data.get("messages")
            if not isinstance(messages, list) or len(messages) < 3:
                raise ValueError(f"{path}:{line_number} has invalid messages")
            roles = {message.get("role") for message in messages if isinstance(message, dict)}
            if roles != EXPECTED_ROLES:
                raise ValueError(f"{path}:{line_number} missing required roles")
            system = next(message["content"] for message in messages if message["role"] == "system")
            user = next(message["content"] for message in messages if message["role"] == "user")
            assistant = next(message["content"] for message in messages if message["role"] == "assistant")
            records.append(
                Record(
                    source_name=source_name,
                    line_number=line_number,
                    record=data,
                    system=system,
                    user=user,
                    assistant=assistant,
                    user_key=normalize_text(user),
                    user_near_key=near_prompt_key(user),
                    assistant_key=normalize_text(assistant),
                )
            )
    return records


def scaffold_counts(records: list[Record]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for record in records:
        assistant_lower = record.assistant.lower()
        for scaffold in REPEATED_SCAFFOLDS:
            if scaffold in assistant_lower:
                counts[scaffold] += 1
    return counts


def score_prompt(record: Record) -> tuple[int, list[str]]:
    score = 100
    reasons: list[str] = []
    words = word_count(record.user)
    if words < 8:
        score -= 15
        reasons.append("prompt_too_short")
    if words > 26:
        score -= 10
        reasons.append("prompt_too_long")
    if " and " in record.user.lower() and record.user.count(",") >= 2:
        score -= 8
        reasons.append("prompt_overloaded")
    if len(set(record.user_key.split())) < max(4, words // 3):
        score -= 8
        reasons.append("prompt_low_variety")
    if re.search(r"\b(confused|fear|afraid|restless|discipline|trust|grief|uncertain|angry|jealous|overwhelmed|career|purpose|change|clarity|action)\b", record.user.lower()):
        score += 5
    return max(0, min(100, score)), reasons


def score_response(record: Record) -> tuple[int, int, int, list[str]]:
    score = 100
    repetition_score = 100
    actionability_score = 100
    reasons: list[str] = []
    assistant_lower = record.assistant.lower()
    words = word_count(record.assistant)
    sentences = sentence_split(record.assistant)
    normalized_sentences = [normalize_text(sentence) for sentence in sentences]
    sentence_counter = Counter(normalized_sentences)

    if words < 80:
        score -= 12
        reasons.append("response_too_short")
    if words > 150:
        score -= 12
        reasons.append("response_too_long")

    semicolon_count = record.assistant.count(";")
    if semicolon_count >= 4:
        score -= 10
        repetition_score -= 14
        reasons.append("too_many_semicolons")
    elif semicolon_count == 3:
        score -= 6
        repetition_score -= 8
        reasons.append("semicolon_heavy")

    scaffold_hits = 0
    for scaffold in REPEATED_SCAFFOLDS:
        hit_count = assistant_lower.count(scaffold)
        if hit_count:
            scaffold_hits += hit_count
            score -= 5 * hit_count
            repetition_score -= 6 * hit_count
            reasons.append(f"repeated_scaffold:{scaffold}")

    repeated_that_is = len(re.findall(r"\bthat is\b", assistant_lower))
    repeated_it_helps = len(re.findall(r"\bit helps\b", assistant_lower))
    if repeated_that_is >= 3:
        score -= 10
        repetition_score -= 12
        reasons.append("repeated_that_is")
    if repeated_it_helps >= 3:
        score -= 8
        repetition_score -= 10
        reasons.append("repeated_it_helps")

    duplicate_sentence_count = sum(count - 1 for count in sentence_counter.values() if count > 1)
    if duplicate_sentence_count:
        score -= 18
        repetition_score -= 25
        reasons.append("repeated_sentence_fragments")

    first_six_counter = Counter(first_n_words(sentence, 6) for sentence in sentences if sentence)
    if any(count > 1 for count in first_six_counter.values()):
        score -= 8
        repetition_score -= 12
        reasons.append("repeated_sentence_stem")

    if re.search(r"^\s*\d+\.\s", record.assistant, re.MULTILINE) or "**" in record.assistant:
        score -= 18
        reasons.append("listicle_style")

    if any(pattern in assistant_lower for pattern in SCRIPTURE_LEAK_PATTERNS):
        score -= 25
        reasons.append("scripture_metadata_leakage")

    if any(pattern in assistant_lower for pattern in GENERIC_MOTIVATIONAL_PATTERNS):
        score -= 8
        reasons.append("generic_motivational_advice")

    concrete_action_hits = sum(1 for marker in CONCRETE_ACTION_MARKERS if marker in assistant_lower)
    if concrete_action_hits == 0:
        score -= 10
        actionability_score -= 18
        reasons.append("no_concrete_next_step")
    elif concrete_action_hits == 1:
        actionability_score -= 5
    else:
        actionability_score += 5

    if not re.search(r"\b(pause|write|choose|set|take|name|pick|practice|remove|interrupt|breathe|return)\b", assistant_lower):
        score -= 8
        actionability_score -= 12
        reasons.append("weak_practical_action")

    if re.search(r"\b(depression|counselor|therapist|medication|diagnosis)\b", assistant_lower):
        score -= 20
        reasons.append("medical_or_therapy_language")

    if "??" in record.assistant or "again again" in assistant_lower or "cold and cold" in assistant_lower:
        score -= 20
        repetition_score -= 25
        reasons.append("looping_or_unstable_phrase")

    if re.search(r"\b(stop letting [a-z]+ decide what is right for you\b.*\bstop letting [a-z]+ decide what is right for you\b)", assistant_lower):
        score -= 25
        repetition_score -= 30
        reasons.append("looping_template")

    response_quality_score = max(0, min(100, score))
    repetition_score = max(0, min(100, repetition_score))
    actionability_score = max(0, min(100, actionability_score))
    return response_quality_score, repetition_score, actionability_score, reasons


def final_score(prompt_quality_score: int, response_quality_score: int, repetition_score: int, actionability_score: int) -> int:
    return round(
        (0.2 * prompt_quality_score)
        + (0.4 * response_quality_score)
        + (0.2 * repetition_score)
        + (0.2 * actionability_score)
    )


def evaluate_records(records: list[Record]) -> None:
    for record in records:
        prompt_score, prompt_reasons = score_prompt(record)
        response_score, repetition_score, actionability_score, response_reasons = score_response(record)
        record.prompt_quality_score = prompt_score
        record.response_quality_score = response_score
        record.repetition_score = repetition_score
        record.actionability_score = actionability_score
        record.final_score = final_score(prompt_score, response_score, repetition_score, actionability_score)
        record.removal_reasons.extend(prompt_reasons + response_reasons)


def choose_best_from_group(group: list[Record]) -> None:
    ranked = sorted(
        group,
        key=lambda item: (
            item.final_score,
            item.response_quality_score,
            item.actionability_score,
            item.repetition_score,
            -item.line_number,
        ),
        reverse=True,
    )
    if not ranked:
        return
    winner = ranked[0]
    if winner.final_score >= 80:
        winner.keep = True
    winner.duplicate_group_rank = 1
    for index, record in enumerate(ranked[1:], start=2):
        record.keep = False
        record.duplicate_group_rank = index
        record.removal_reasons.append("duplicate_user_prompt")


def deduplicate_by_prompt(records: list[Record]) -> tuple[int, int]:
    exact_groups: defaultdict[str, list[Record]] = defaultdict(list)
    near_groups: defaultdict[str, list[Record]] = defaultdict(list)
    for record in records:
        exact_groups[record.user_key].append(record)
    for group in exact_groups.values():
        if len(group) > 1:
            choose_best_from_group(group)
    singles = [record for record in records if not record.keep and record.duplicate_group_rank == 0]
    for record in singles:
        near_groups[record.user_near_key].append(record)
    duplicate_group_count = 0
    duplicate_removed = 0
    for group in near_groups.values():
        if len(group) > 1:
            duplicate_group_count += 1
            choose_best_from_group(group)
            duplicate_removed += max(0, len(group) - 1)
        else:
            record = group[0]
            if record.final_score >= 80:
                record.keep = True
            else:
                record.keep = False
                record.removal_reasons.append("below_final_score_threshold")
    return duplicate_group_count, duplicate_removed


def enforce_uniqueness(records: list[Record]) -> tuple[int, int]:
    kept = [record for record in records if record.keep]
    assistant_seen: dict[str, Record] = {}
    prompt_seen: dict[str, Record] = {}
    duplicate_assistant_removed = 0
    duplicate_prompt_removed = 0

    for record in sorted(kept, key=lambda item: item.final_score, reverse=True):
        if record.assistant_key in assistant_seen:
            record.keep = False
            record.removal_reasons.append("duplicate_assistant_response")
            duplicate_assistant_removed += 1
            continue
        assistant_seen[record.assistant_key] = record

    kept = [record for record in records if record.keep]
    for record in sorted(kept, key=lambda item: item.final_score, reverse=True):
        if record.user_key in prompt_seen:
            record.keep = False
            record.removal_reasons.append("duplicate_user_prompt")
            duplicate_prompt_removed += 1
            continue
        prompt_seen[record.user_key] = record

    return duplicate_prompt_removed, duplicate_assistant_removed


def validate_output_records(records: list[Record]) -> None:
    for record in records:
        messages = record.record["messages"]
        roles = {message["role"] for message in messages}
        if roles != EXPECTED_ROLES:
            raise ValueError("output dataset contains invalid roles")
        if messages[0]["content"] != SYSTEM_PROMPT:
            pass


def write_jsonl(path: Path, records: list[Record]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for index, record in enumerate(records):
            serialized = json.dumps(record.record, ensure_ascii=False)
            handle.write(serialized)
            if index != len(records) - 1:
                handle.write("\n")


def build_metadata(
    gita_count: int,
    upanishad_count: int,
    merged_count: int,
    removed_count: int,
    duplicate_prompt_groups: int,
    duplicate_prompt_removed: int,
    duplicate_assistant_removed: int,
) -> str:
    return "\n".join(
        [
            "Dataset: Marg Darshak Merged v2",
            f"Date: {date.today().isoformat()}",
            "Purpose: Marg Darshak LoRA v2 cleaned training dataset",
            "",
            "Source datasets:",
            f"- {GITA_DATASET}",
            f"- {UPANISHAD_DATASET}",
            f"- analysis reference: {ANALYSIS_PATH}",
            "",
            "Counts:",
            f"- Gita count: {gita_count}",
            f"- Upanishads count: {upanishad_count}",
            f"- Original merged count: {gita_count + upanishad_count}",
            f"- Cleaned merged count: {merged_count}",
            f"- Removed count: {removed_count}",
            f"- Duplicate prompt groups removed: {duplicate_prompt_groups}",
            f"- Duplicate prompt rows removed: {duplicate_prompt_removed}",
            f"- Duplicate assistant rows removed: {duplicate_assistant_removed}",
            "",
            "System prompt:",
            f"- {SYSTEM_PROMPT}",
        ]
    )


def format_example(record: Record) -> str:
    return "\n".join(
        [
            f"- source: {record.source_name}:{record.line_number}",
            f"  final_score={record.final_score} prompt={record.prompt_quality_score} response={record.response_quality_score} repetition={record.repetition_score} action={record.actionability_score}",
            f"  user: {record.user}",
            f"  assistant: {record.assistant}",
            f"  reasons: {', '.join(record.removal_reasons) if record.removal_reasons else 'kept'}",
        ]
    )


def build_report(
    all_records: list[Record],
    kept_records: list[Record],
    removed_records: list[Record],
    duplicate_prompt_groups: int,
    duplicate_prompt_removed: int,
    duplicate_assistant_removed: int,
    before_scaffolds: Counter[str],
    after_scaffolds: Counter[str],
) -> str:
    removal_reason_counts = Counter(
        reason
        for record in removed_records
        for reason in record.removal_reasons
    )
    kept_samples = sorted(kept_records, key=lambda item: item.final_score, reverse=True)[:20]
    removed_samples = sorted(removed_records, key=lambda item: item.final_score)[:20]
    lines = [
        "# Merged v2 Dataset Cleanup Report",
        "",
        f"- original count: {len(all_records)}",
        f"- kept count: {len(kept_records)}",
        f"- removed count: {len(removed_records)}",
        f"- duplicate prompt groups removed: {duplicate_prompt_groups}",
        f"- duplicate prompt rows removed: {duplicate_prompt_removed}",
        f"- duplicate assistant rows removed: {duplicate_assistant_removed}",
        "",
        "## Top Removal Reasons",
        "",
    ]
    for reason, count in removal_reason_counts.most_common(20):
        lines.append(f"- {reason}: {count}")
    lines.extend(
        [
            "",
            "## Repeated Scaffold Counts Before",
            "",
        ]
    )
    for scaffold, count in before_scaffolds.most_common():
        lines.append(f"- `{scaffold}`: {count}")
    lines.extend(
        [
            "",
            "## Repeated Scaffold Counts After",
            "",
        ]
    )
    for scaffold, count in after_scaffolds.most_common():
        lines.append(f"- `{scaffold}`: {count}")
    lines.extend(
        [
            "",
            "## 20 Sample Kept Examples",
            "",
        ]
    )
    for record in kept_samples:
        lines.append(format_example(record))
        lines.append("")
    lines.extend(
        [
            "## 20 Sample Removed Examples",
            "",
        ]
    )
    for record in removed_samples:
        lines.append(format_example(record))
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def main() -> int:
    random.seed(42)
    gita_records = load_jsonl(GITA_DATASET, "gita")
    upanishad_records = load_jsonl(UPANISHAD_DATASET, "upanishads")
    all_records = gita_records + upanishad_records

    before_scaffolds = scaffold_counts(all_records)
    evaluate_records(all_records)
    duplicate_prompt_groups, duplicate_prompt_removed_initial = deduplicate_by_prompt(all_records)
    duplicate_prompt_removed_late, duplicate_assistant_removed = enforce_uniqueness(all_records)

    for record in all_records:
        if not record.keep and "below_final_score_threshold" not in record.removal_reasons and record.final_score < 80:
            record.removal_reasons.append("below_final_score_threshold")

    kept_records = sorted(
        [record for record in all_records if record.keep and record.final_score >= 80],
        key=lambda item: (item.final_score, item.response_quality_score, item.actionability_score),
        reverse=True,
    )
    removed_records = [record for record in all_records if record not in kept_records]
    after_scaffolds = scaffold_counts(kept_records)

    validate_output_records(kept_records)
    write_jsonl(MERGED_V2_DATASET, kept_records)
    write_jsonl(TRAINING_COPY, kept_records)

    duplicate_prompt_removed = duplicate_prompt_removed_initial + duplicate_prompt_removed_late
    METADATA_PATH.write_text(
        build_metadata(
            gita_count=len(gita_records),
            upanishad_count=len(upanishad_records),
            merged_count=len(kept_records),
            removed_count=len(removed_records),
            duplicate_prompt_groups=duplicate_prompt_groups,
            duplicate_prompt_removed=duplicate_prompt_removed,
            duplicate_assistant_removed=duplicate_assistant_removed,
        ),
        encoding="utf-8",
    )
    REPORT_PATH.write_text(
        build_report(
            all_records=all_records,
            kept_records=kept_records,
            removed_records=removed_records,
            duplicate_prompt_groups=duplicate_prompt_groups,
            duplicate_prompt_removed=duplicate_prompt_removed,
            duplicate_assistant_removed=duplicate_assistant_removed,
            before_scaffolds=before_scaffolds,
            after_scaffolds=after_scaffolds,
        ),
        encoding="utf-8",
    )

    print(f"Gita count: {len(gita_records)}")
    print(f"Upanishads count: {len(upanishad_records)}")
    print(f"Original merged count: {len(all_records)}")
    print(f"Kept count: {len(kept_records)}")
    print(f"Removed count: {len(removed_records)}")
    print(f"Duplicate prompt groups removed: {duplicate_prompt_groups}")
    print(f"Duplicate prompt rows removed: {duplicate_prompt_removed}")
    print(f"Duplicate assistant rows removed: {duplicate_assistant_removed}")
    print("Repeated scaffolds before:")
    for scaffold, count in before_scaffolds.most_common():
        print(f"  {scaffold}: {count}")
    print("Repeated scaffolds after:")
    for scaffold, count in after_scaffolds.most_common():
        print(f"  {scaffold}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
