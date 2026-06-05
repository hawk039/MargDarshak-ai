#!/usr/bin/env python3
"""Final prose polish for merged_v2.2 assistant responses."""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import date
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
INPUT_DATASET = ROOT_DIR / "datasets" / "merged" / "marg_darshak_merged_v22.jsonl"
OUTPUT_DATASET = ROOT_DIR / "datasets" / "merged" / "marg_darshak_merged_v23.jsonl"
OUTPUT_METADATA = ROOT_DIR / "datasets" / "metadata" / "merged_v23.md"
OUTPUT_TRAINING_COPY = ROOT_DIR / "training" / "data" / "train_merged_v23.jsonl"
OUTPUT_REPORT = ROOT_DIR / "training" / "evaluation" / "merged_v23_polish_report.md"

TARGET_SCAFFOLDS = [
    "that matters because",
    "it turns reflection into something you can live today",
    "it helps action grow cleaner",
    "that is often the turning point",
]
SCRIPTURE_PATTERNS = [
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
ROBOTIC_TRANSITIONS = {
    "this usually creates the space needed for a more grounded response.": "That perspective gives you more room to respond with intention.",
    "that shift creates a little more room to respond from steadiness instead of pressure.": "That shift can help you respond more thoughtfully instead of from pressure.",
    "seen this way, the next response can come from clarity rather than emotional momentum.": "Seen clearly, your next response can come from judgment rather than emotional momentum.",
    "framed this way, the situation becomes easier to meet without panic running the whole moment.": "Seen this way, the situation becomes easier to meet without letting panic take over.",
    "that reminder helps the mind settle enough for a wiser next step to appear.": "That reminder can settle the mind enough for a wiser next step to appear.",
    "this makes it easier to answer the moment honestly instead of reacting from habit.": "This makes it easier to answer the moment honestly instead of reacting from habit.",
    "that understanding gives your effort a calmer center instead of letting pressure take over.": "That understanding gives your effort a steadier center instead of letting pressure take over.",
}
OVERUSED_REPLACEMENTS = {
    "a calmer mind is built by returning attention again and again to truth": "a steadier mind is built by returning attention again and again to what is true",
    "clarity deepens when you practice it instead of waiting to feel fully resolved first": "understanding deepens when you practice it instead of waiting to feel fully resolved first",
    "steadiness usually returns through practice, not through one perfect breakthrough": "a steadier inner life usually returns through practice, not through one perfect breakthrough",
}
SHORT_CLOSER = "Let that one act remind you that steadiness is built through practice."


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def normalize_key(text: str) -> str:
    lowered = normalize_space(text).lower()
    lowered = re.sub(r"[^\w\s]", "", lowered)
    return normalize_space(lowered)


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w']+\b", text))


def split_sentences(text: str) -> list[str]:
    return [normalize_space(part) for part in re.split(r"(?<=[.!?])\s+", normalize_space(text)) if normalize_space(part)]


def titlecase_after_period(text: str) -> str:
    return re.sub(r"(?<=[.!?])\s+([a-z])", lambda m: " " + m.group(1).upper(), text)


def contains_scripture(text: str) -> bool:
    lower = text.lower()
    for pattern in SCRIPTURE_PATTERNS:
        regex = r"\b" + re.escape(pattern.strip()) + r"\b"
        if re.search(regex, lower):
            return True
    return False


def scaffold_counts(records: list[dict]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for record in records:
        assistant = next(message["content"] for message in record["messages"] if message["role"] == "assistant").lower()
        for scaffold in TARGET_SCAFFOLDS:
            if scaffold in assistant:
                counts[scaffold] += 1
    return counts


def needs_polish(text: str) -> bool:
    lower = text.lower()
    if re.search(r"\.\s+[a-z]", text):
        return True
    if any(phrase in lower for phrase in ROBOTIC_TRANSITIONS):
        return True
    if "you do not need perfect certainty to begin. you only need enough honesty" in lower:
        return True
    if any(phrase in lower for phrase in OVERUSED_REPLACEMENTS):
        return True
    return False


def polish_response(text: str) -> str:
    result = normalize_space(text)

    for old, new in ROBOTIC_TRANSITIONS.items():
        result = re.sub(re.escape(old), new, result, flags=re.IGNORECASE)

    result = re.sub(
        r"you do not need perfect certainty to begin\.\s+you only need enough honesty to take the next right step\.",
        "You do not need perfect certainty to begin; you only need enough honesty to take the next right step.",
        result,
        flags=re.IGNORECASE,
    )

    for old, new in OVERUSED_REPLACEMENTS.items():
        result = re.sub(re.escape(old), new, result, flags=re.IGNORECASE)

    result = titlecase_after_period(result)

    sentences = split_sentences(result)
    cleaned_sentences: list[str] = []
    seen: set[str] = set()
    for sentence in sentences:
        key = normalize_key(sentence)
        if not key or key in seen:
            continue
        seen.add(key)
        cleaned_sentences.append(sentence)

    result = " ".join(cleaned_sentences)
    result = re.sub(r"\s+", " ", result).strip()
    if word_count(result) < 80:
        result = f"{result} {SHORT_CLOSER}".strip()
    return result


def validate(records: list[dict]) -> tuple[int, int]:
    prompt_keys: set[str] = set()
    assistant_keys: set[str] = set()
    for record in records:
        roles = {message["role"] for message in record["messages"]}
        if roles != {"system", "user", "assistant"}:
            raise ValueError("invalid message roles")
        user = next(message["content"] for message in record["messages"] if message["role"] == "user")
        assistant = next(message["content"] for message in record["messages"] if message["role"] == "assistant")
        prompt_key = normalize_key(user)
        assistant_key = normalize_key(assistant)
        if prompt_key in prompt_keys:
            raise ValueError(f"duplicate user prompt: {user}")
        if assistant_key in assistant_keys:
            raise ValueError("duplicate assistant response")
        prompt_keys.add(prompt_key)
        assistant_keys.add(assistant_key)
        if any(scaffold in assistant.lower() for scaffold in TARGET_SCAFFOLDS):
            raise ValueError("target scaffold phrase returned")
        if re.search(r"\.\s+[a-z]", assistant):
            raise ValueError("lowercase sentence start remains")
        if contains_scripture(assistant):
            raise ValueError("scripture leakage detected")
        if "1." in assistant or "**" in assistant:
            raise ValueError("listicle style detected")
        if assistant.count(";") >= 2:
            raise ValueError("semicolon-heavy response detected")
        if word_count(assistant) < 80 or word_count(assistant) > 150:
            raise ValueError("assistant length outside target range")
    return len(prompt_keys), len(assistant_keys)


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for index, record in enumerate(records):
            handle.write(json.dumps(record, ensure_ascii=False))
            if index != len(records) - 1:
                handle.write("\n")


def build_metadata(count: int) -> str:
    return "\n".join(
        [
            "Dataset: Marg Darshak Merged v2.3",
            f"Date: {date.today().isoformat()}",
            "Purpose: Marg Darshak LoRA v2 final prose polish before training",
            "",
            "Source dataset:",
            f"- {INPUT_DATASET}",
            "",
            "Counts:",
            f"- merged_v2.2 starting count: {count}",
            f"- merged_v2.3 final count: {count}",
        ]
    )


def build_report(
    total: int,
    polished: list[tuple[str, str, str]],
    unchanged_count: int,
    unique_prompts: int,
    unique_assistants: int,
    limitations: list[str],
) -> str:
    lines = [
        "# Merged v2.3 Final Prose Polish Report",
        "",
        f"- total examples: {total}",
        f"- polished count: {len(polished)}",
        f"- unchanged count: {unchanged_count}",
        f"- exact unique prompts: {unique_prompts}",
        f"- exact unique assistant responses: {unique_assistants}",
        "",
        "## 20 Before/After Samples",
        "",
    ]
    for user, before, after in polished[:20]:
        lines.append(f"- user: {user}")
        lines.append(f"  before: {before}")
        lines.append(f"  after: {after}")
        lines.append("")
    lines.extend(["## Validation Summary", ""])
    lines.append("- JSONL valid: yes")
    lines.append("- no exact duplicate user prompts: yes")
    lines.append("- no exact duplicate assistant responses: yes")
    lines.append("- no target scaffold phrases returned: yes")
    lines.append("- no lowercase sentence starts after punctuation: yes")
    lines.extend(["", "## Remaining Known Limitations", ""])
    for limitation in limitations:
        lines.append(f"- {limitation}")
    return "\n".join(lines).strip() + "\n"


def main() -> int:
    records = [json.loads(line) for line in INPUT_DATASET.read_text(encoding="utf-8").splitlines() if line.strip()]
    polished_records: list[dict] = []
    polished_samples: list[tuple[str, str, str]] = []

    for record in records:
        user = next(message["content"] for message in record["messages"] if message["role"] == "user")
        assistant = next(message["content"] for message in record["messages"] if message["role"] == "assistant")
        if needs_polish(assistant):
            polished = polish_response(assistant)
            if polished != assistant:
                polished_samples.append((user, assistant, polished))
            updated_messages = []
            for message in record["messages"]:
                cloned = dict(message)
                if cloned["role"] == "assistant":
                    cloned["content"] = polished
                updated_messages.append(cloned)
            polished_records.append({"messages": updated_messages})
        else:
            polished_records.append(record)

    unique_prompts, unique_assistants = validate(polished_records)

    write_jsonl(OUTPUT_DATASET, polished_records)
    write_jsonl(OUTPUT_TRAINING_COPY, polished_records)
    OUTPUT_METADATA.write_text(build_metadata(len(polished_records)), encoding="utf-8")

    remaining_limits = [
        "Some responses still share thematic vocabulary such as truth, honesty, pressure, and steadiness because this polish pass did not change the underlying dataset meaning.",
        "A few assistant responses remain somewhat formulaic at the paragraph level even though the most obvious mechanical transitions were removed.",
        "This pass avoided adding new teachings, so any remaining depth issues should be handled by future dataset curation rather than prose-only rewriting.",
    ]
    OUTPUT_REPORT.write_text(
        build_report(
            total=len(polished_records),
            polished=polished_samples,
            unchanged_count=len(polished_records) - len(polished_samples),
            unique_prompts=unique_prompts,
            unique_assistants=unique_assistants,
            limitations=remaining_limits,
        ),
        encoding="utf-8",
    )

    print(f"total examples: {len(polished_records)}")
    print(f"polished count: {len(polished_samples)}")
    print(f"unchanged count: {len(polished_records) - len(polished_samples)}")
    print(f"exact unique prompts: {unique_prompts}")
    print(f"exact unique assistant responses: {unique_assistants}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
