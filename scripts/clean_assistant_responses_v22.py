#!/usr/bin/env python3
"""Clean scaffold-heavy assistant responses in merged_v2.1 without changing prompt meaning."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
INPUT_DATASET = ROOT_DIR / "datasets" / "merged" / "marg_darshak_merged_v21.jsonl"
OUTPUT_DATASET = ROOT_DIR / "datasets" / "merged" / "marg_darshak_merged_v22.jsonl"
OUTPUT_METADATA = ROOT_DIR / "datasets" / "metadata" / "merged_v22.md"
OUTPUT_TRAINING_COPY = ROOT_DIR / "training" / "data" / "train_merged_v22.jsonl"
OUTPUT_REPORT = ROOT_DIR / "training" / "evaluation" / "merged_v22_assistant_cleanup_report.md"

SCAFFOLDS = [
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
GENERIC_CLOSERS = {
    "you do not need perfect certainty to begin; you only need enough honesty to take the next right step.",
    "small sincere actions often restore clarity faster than long arguments with the mind.",
    "steadiness usually returns through practice, not through one perfect breakthrough.",
    "clarity deepens when you practice it instead of waiting to feel fully resolved first.",
    "the important thing is not to force yourself harshly, but to return gently and truthfully.",
}
ACTION_HINTS = [
    "write down",
    "choose one",
    "set a short timer",
    "pause and ask",
    "take ten quiet minutes",
    "pick one",
    "name one",
    "breathe slowly",
    "practice one",
    "remove one",
    "interrupt",
    "return to",
    "meet it with one calm deliberate action",
    "reverse that pattern",
    "do it at a fixed time",
    "complete one gentle grounding act",
    "begin it before your mood improves",
]
BRIDGE_BANK = [
    "That shift creates a little more room to respond from steadiness instead of pressure.",
    "Seen this way, the next response can come from clarity rather than emotional momentum.",
    "That perspective softens the pressure and gives your next step a steadier direction.",
    "This makes it easier to answer the moment honestly instead of reacting from habit.",
    "That reminder helps the mind settle enough for a wiser next step to appear.",
    "Framed this way, the situation becomes easier to meet without panic running the whole moment.",
    "That understanding gives your effort a calmer center instead of letting pressure take over.",
    "This usually creates the space needed for a more grounded response.",
]
PRACTICE_CLOSERS = [
    "Let the value of the step be that it interrupts the old pattern.",
    "Keep the step simple enough that you can repeat it honestly.",
    "Treat the action as practice in steadiness, not a test of your worth.",
    "What matters now is following through without making the step dramatic.",
    "The point is not perfection, but a steadier way of meeting what is here.",
    "Let that one action teach the mind that clarity is something you practice.",
]


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def normalize_key(text: str) -> str:
    lowered = normalize_space(text).lower()
    lowered = re.sub(r"[^\w\s]", "", lowered)
    return normalize_space(lowered)


def count_words(text: str) -> int:
    return len(re.findall(r"\b[\w']+\b", text))


def stable_index(seed_text: str, length: int) -> int:
    digest = hashlib.md5(seed_text.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % length


def split_sentences(text: str) -> list[str]:
    text = normalize_space(text)
    text = text.replace("; ", ". ")
    text = re.sub(r";", ".", text)
    parts = re.split(r"(?<=[.!?])\s+", text)
    cleaned = [normalize_space(part) for part in parts if normalize_space(part)]
    return cleaned


def needs_rewrite(text: str) -> bool:
    lower = text.lower()
    if any(scaffold in lower for scaffold in SCAFFOLDS):
        return True
    if lower.count("that is") >= 2 or lower.count("it helps") >= 2:
        return True
    if text.count(";") >= 2:
        return True
    return False


def sentence_has_scripture(text: str) -> bool:
    lower = text.lower()
    for pattern in SCRIPTURE_PATTERNS:
        regex = r"\b" + re.escape(pattern.strip()) + r"\b"
        if re.search(regex, lower):
            return True
    return False


def choose_bridge(seed: str) -> str:
    return BRIDGE_BANK[stable_index(seed + "::bridge", len(BRIDGE_BANK))]


def choose_practice_closer(seed: str) -> str:
    return PRACTICE_CLOSERS[stable_index(seed + "::closer", len(PRACTICE_CLOSERS))]


def clean_sentence(sentence: str, seed: str) -> str | None:
    lower = sentence.lower()
    if not sentence or sentence_has_scripture(sentence):
        return None
    if "that matters because" in lower:
        return choose_bridge(seed)
    if lower.startswith("that becomes practical when") or lower.startswith("that becomes useful when") or lower.startswith("that becomes real when"):
        return choose_bridge(seed)
    if "it turns reflection into something you can live today" in lower:
        return "Let that understanding become something you practice instead of something you only admire."
    if "it helps action grow cleaner" in lower:
        return "It gives the next step a calmer and more honest direction."
    if "that is often the turning point" in lower:
        return "That is usually where steadier action begins."
    if lower.startswith("this is how pressure stops running ahead of wiser judgment"):
        return "That is how the mind begins to stop amplifying the pressure."
    if lower.startswith("this is how steadiness starts returning in ordinary life"):
        return "That is how steadiness begins to return in ordinary life."
    if lower.startswith("this is the sort of moment where"):
        return sentence
    sentence = re.sub(r"\bThat is\b", "This is", sentence, count=1)
    sentence = re.sub(r"\bIt helps\b", "This helps", sentence, count=1)
    return sentence


def find_action_sentence(sentences: list[str]) -> str | None:
    for sentence in reversed(sentences):
        lower = sentence.lower()
        if any(hint in lower for hint in ACTION_HINTS):
            return sentence
    return None


def dedupe_sentences(sentences: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for sentence in sentences:
        key = normalize_key(sentence)
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(sentence)
    return result


def compress_generic_closers(sentences: list[str]) -> list[str]:
    result: list[str] = []
    generic_used = False
    for sentence in sentences:
        if sentence.lower() in GENERIC_CLOSERS:
            if generic_used:
                continue
            generic_used = True
        result.append(sentence)
    return result


def cleanup_response(user_text: str, assistant_text: str) -> str:
    seed = f"{user_text}::{assistant_text}"
    raw_sentences = split_sentences(assistant_text)
    cleaned = [clean_sentence(sentence, seed) for sentence in raw_sentences]
    cleaned = [sentence for sentence in cleaned if sentence]
    cleaned = dedupe_sentences(cleaned)
    cleaned = compress_generic_closers(cleaned)

    action_sentence = find_action_sentence(cleaned)
    if action_sentence:
        cleaned = [sentence for sentence in cleaned if sentence != action_sentence] + [action_sentence]

    text = " ".join(cleaned)
    text = re.sub(r"\s+", " ", text).strip()

    if count_words(text) < 80:
        closer = choose_practice_closer(seed)
        if normalize_key(closer) not in {normalize_key(sentence) for sentence in cleaned}:
            text = f"{text} {closer}".strip()

    if count_words(text) > 150:
        sentences = split_sentences(text)
        trimmed: list[str] = []
        for sentence in sentences:
            if sentence.lower() in GENERIC_CLOSERS and count_words(" ".join(trimmed + [sentence])) > 140:
                continue
            trimmed.append(sentence)
        text = " ".join(trimmed).strip()

    if count_words(text) > 150:
        sentences = split_sentences(text)
        while count_words(" ".join(sentences)) > 150 and len(sentences) > 3:
            sentences.pop(-2)
        text = " ".join(sentences).strip()

    return text


def scaffold_counts(records: list[dict]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for record in records:
        assistant = next(message["content"] for message in record["messages"] if message["role"] == "assistant").lower()
        for scaffold in SCAFFOLDS:
            if scaffold in assistant:
                counts[scaffold] += 1
    return counts


def validate_records(records: list[dict]) -> tuple[int, int]:
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
            raise ValueError("duplicate assistant response detected")
        prompt_keys.add(prompt_key)
        assistant_keys.add(assistant_key)
        if count_words(assistant) < 80 or count_words(assistant) > 150:
            raise ValueError("assistant length outside target range")
        if "1." in assistant or "**" in assistant:
            raise ValueError("listicle format detected")
        if assistant.count(";") >= 2:
            raise ValueError("semicolon-heavy response detected")
        if lower_has_forbidden(assistant):
            raise ValueError("forbidden scaffold or scripture leakage remains")
    return len(prompt_keys), len(assistant_keys)


def lower_has_forbidden(text: str) -> bool:
    lower = text.lower()
    if any(scaffold in lower for scaffold in SCAFFOLDS):
        return True
    if lower.count("that is") >= 3 or lower.count("it helps") >= 3:
        return True
    for pattern in SCRIPTURE_PATTERNS:
        regex = r"\b" + re.escape(pattern.strip()) + r"\b"
        if re.search(regex, lower):
            return True
    return False


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
            "Dataset: Marg Darshak Merged v2.2",
            f"Date: {date.today().isoformat()}",
            "Purpose: Marg Darshak LoRA v2 cleaned dataset with assistant-response scaffold cleanup",
            "",
            "Source dataset:",
            f"- {INPUT_DATASET}",
            "",
            "Counts:",
            f"- merged_v2.1 starting count: {count}",
            f"- merged_v2.2 final count: {count}",
        ]
    )


def build_report(
    total: int,
    rewritten: list[tuple[str, str, str]],
    unchanged_count: int,
    before_counts: Counter[str],
    after_counts: Counter[str],
    unique_prompts: int,
    unique_assistants: int,
) -> str:
    lines = [
        "# Merged v2.2 Assistant Cleanup Report",
        "",
        f"- total examples: {total}",
        f"- examples rewritten: {len(rewritten)}",
        f"- examples unchanged: {unchanged_count}",
        f"- exact unique prompts: {unique_prompts}",
        f"- exact unique assistant responses: {unique_assistants}",
        "",
        "## Scaffold Counts Before",
        "",
    ]
    for scaffold, count in before_counts.most_common():
        lines.append(f"- `{scaffold}`: {count}")
    lines.extend(["", "## Scaffold Counts After", ""])
    for scaffold, count in after_counts.most_common():
        lines.append(f"- `{scaffold}`: {count}")
    lines.extend(["", "## 20 Before/After Samples", ""])
    for user, before, after in rewritten[:20]:
        lines.append(f"- user: {user}")
        lines.append(f"  before: {before}")
        lines.append(f"  after: {after}")
        lines.append("")
    lines.extend(["## Validation Summary", ""])
    lines.append("- JSONL valid: yes")
    lines.append("- no exact duplicate user prompts: yes")
    lines.append("- no exact duplicate assistant responses: yes")
    lines.append("- listicle style removed from rewritten examples: yes")
    lines.append("- semicolon-heavy stitching removed from rewritten examples: yes")
    return "\n".join(lines).strip() + "\n"


def main() -> int:
    records = [json.loads(line) for line in INPUT_DATASET.read_text(encoding="utf-8").splitlines() if line.strip()]
    before_counts = scaffold_counts(records)
    rewritten_samples: list[tuple[str, str, str]] = []
    rewritten_count = 0

    cleaned_records: list[dict] = []
    for record in records:
        user = next(message["content"] for message in record["messages"] if message["role"] == "user")
        assistant = next(message["content"] for message in record["messages"] if message["role"] == "assistant")
        if needs_rewrite(assistant):
            new_assistant = cleanup_response(user, assistant)
            if new_assistant != assistant:
                rewritten_count += 1
                rewritten_samples.append((user, assistant, new_assistant))
            updated_messages = []
            for message in record["messages"]:
                cloned = dict(message)
                if cloned["role"] == "assistant":
                    cloned["content"] = new_assistant
                updated_messages.append(cloned)
            cleaned_records.append({"messages": updated_messages})
        else:
            cleaned_records.append(record)

    unique_prompts, unique_assistants = validate_records(cleaned_records)
    after_counts = scaffold_counts(cleaned_records)

    write_jsonl(OUTPUT_DATASET, cleaned_records)
    write_jsonl(OUTPUT_TRAINING_COPY, cleaned_records)
    OUTPUT_METADATA.write_text(build_metadata(len(cleaned_records)), encoding="utf-8")
    OUTPUT_REPORT.write_text(
        build_report(
            total=len(cleaned_records),
            rewritten=rewritten_samples,
            unchanged_count=len(cleaned_records) - rewritten_count,
            before_counts=before_counts,
            after_counts=after_counts,
            unique_prompts=unique_prompts,
            unique_assistants=unique_assistants,
        ),
        encoding="utf-8",
    )

    print(f"total examples: {len(cleaned_records)}")
    print(f"examples rewritten: {rewritten_count}")
    print(f"examples unchanged: {len(cleaned_records) - rewritten_count}")
    print(f"exact unique prompts: {unique_prompts}")
    print(f"exact unique assistant responses: {unique_assistants}")
    print("Scaffold counts before:")
    for scaffold, count in before_counts.most_common():
        print(f"  {scaffold}: {count}")
    print("Scaffold counts after:")
    for scaffold, count in after_counts.most_common():
        print(f"  {scaffold}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
