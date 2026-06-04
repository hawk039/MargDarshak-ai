#!/usr/bin/env python3
"""Expand merged_v2 with prompt-only rewrites from high-value duplicate examples."""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MERGED_V2_PATH = ROOT_DIR / "datasets" / "merged" / "marg_darshak_merged_v2.jsonl"
MERGED_V21_PATH = ROOT_DIR / "datasets" / "merged" / "marg_darshak_merged_v21.jsonl"
TRAINING_COPY = ROOT_DIR / "training" / "data" / "train_merged_v21.jsonl"
METADATA_PATH = ROOT_DIR / "datasets" / "metadata" / "merged_v21.md"
REPORT_PATH = ROOT_DIR / "training" / "evaluation" / "merged_v21_rewrite_report.md"


def load_cleaner():
    spec = importlib.util.spec_from_file_location("cleaner", ROOT_DIR / "scripts" / "clean_merged_dataset_v2.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["cleaner"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


cleaner = load_cleaner()

SEVERE_REASONS = {
    "looping_or_unstable_phrase",
    "looping_template",
    "listicle_style",
    "scripture_metadata_leakage",
    "repeated_sentence_fragments",
    "repeated_sentence_stem",
    "medical_or_therapy_language",
}
SAFE_SCAFFOLD_THRESHOLD = 50
TARGET_MIN = 90
TARGET_PREFERRED = 100
TARGET_MAX = 115


@dataclass
class RewriteCandidate:
    record: cleaner.Record
    theme: str
    rewritten_user: str | None = None
    skip_reason: str | None = None


THEME_TEMPLATE_BANKS: dict[str, list[str]] = {
    "clarity_decision": [
        "I keep circling the same choice, and I need a steadier way to decide.",
        "My thoughts are crowding the decision in front of me, and I want to act with more clarity.",
        "I keep getting lost in overthinking when I need to make one honest choice.",
        "Mental noise keeps taking over when I try to choose carefully.",
        "I want to decide from steadiness, but my mind keeps multiplying outcomes.",
        "I keep second-guessing what is true for me, and it is making action harder.",
    ],
    "duty_action": [
        "The responsibility is clear, but I still hesitate when it is time to act.",
        "I know the work that is mine, but I keep stalling when the moment arrives.",
        "When duty feels heavy, I start wavering instead of moving forward.",
        "I keep shrinking back from the responsibility that I know belongs to me.",
        "The next action is obvious, but emotional pressure keeps making me delay it.",
        "I want to act with integrity, but I keep freezing when responsibility becomes real.",
    ],
    "discipline_self_control": [
        "My better intentions keep collapsing under impulse, and I want steadier discipline.",
        "I start with sincerity, but I keep losing structure when discomfort appears.",
        "I want stronger self-control, but my habits keep sliding back into what is easy.",
        "My resolve keeps weakening at the moment I most need discipline.",
        "I keep breaking trust with myself in small ways, and I want a wiser habit to replace that.",
        "I know what steadiness requires, but I keep yielding to the easier impulse.",
    ],
    "trust_let_go": [
        "I keep gripping for certainty, and it is making honest trust harder.",
        "Part of me wants to release control, but another part keeps tightening around it.",
        "I want to let go without becoming careless, but I do not know how to do that cleanly.",
        "The more uncertain life feels, the more tightly I try to force it.",
        "I want to trust what I cannot control, but I keep turning uncertainty into pressure.",
        "I can feel myself clinging harder when life asks for surrender and honesty.",
    ],
    "attachment_outcome": [
        "My peace keeps getting tied to the result, and it is draining the honesty from my effort.",
        "I keep measuring everything by the outcome, and it is making the work feel heavier.",
        "My mind gets trapped in how things should turn out, and it keeps disturbing my steadiness.",
        "I want to work sincerely, but I keep handing my peace over to the result.",
        "The outcome keeps pulling too much of my attention, and I want a cleaner way to act.",
        "I keep exhausting myself by trying to control how everything ends.",
    ],
    "fear_steadiness": [
        "Fear keeps getting ahead of me, and it is making the next step feel larger than it is.",
        "I want to stay grounded under emotional pressure, but fear keeps narrowing my view.",
        "When uncertainty rises, fear starts deciding too much for me.",
        "I can feel fear running ahead of my judgment, and I need a steadier response.",
        "Emotional pressure keeps shaking my center, and I want to return to steadiness.",
        "I keep treating fear like final truth, and it is making calm action harder.",
    ],
}


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def get_message_content(record: dict, role: str) -> str:
    for message in record["messages"]:
        if message["role"] == role:
            return message["content"]
    raise KeyError(role)


def classify_theme(record: cleaner.Record) -> str:
    text = f"{record.user} {record.assistant}".lower()
    if any(token in text for token in ["duty", "responsibility", "right action", "work that is mine", "integrity"]):
        return "duty_action"
    if any(token in text for token in ["discipline", "self-control", "habit", "impulse", "restraint", "consistency"]):
        return "discipline_self_control"
    if any(token in text for token in ["trust", "surrender", "let go", "uncertainty", "devotion"]):
        return "trust_let_go"
    if any(token in text for token in ["outcome", "result", "attachment", "clinging", "expectation"]):
        return "attachment_outcome"
    if any(token in text for token in ["fear", "grief", "emotional pressure", "steadiness", "grounded"]):
        return "fear_steadiness"
    return "clarity_decision"


def prompt_fingerprint(text: str) -> str:
    return cleaner.near_prompt_key(text)


def assistant_has_forbidden_structure(record: cleaner.Record) -> bool:
    lower = record.assistant.lower()
    if has_scripture_leakage(lower):
        return True
    if re_count(lower, "that is") >= 4:
        return True
    if re_count(lower, "it helps") >= 4:
        return True
    if record.assistant.count(";") >= 5:
        return True
    if "1." in record.assistant or "**" in record.assistant:
        return True
    return False


def re_count(text: str, phrase: str) -> int:
    return text.count(phrase)


def has_scripture_leakage(text: str) -> bool:
    for pattern in cleaner.SCRIPTURE_LEAK_PATTERNS:
        regex = r"\b" + re.escape(pattern.strip()) + r"\b"
        if re.search(regex, text):
            return True
    return False


def candidate_pool() -> list[RewriteCandidate]:
    records = cleaner.load_jsonl(cleaner.GITA_DATASET, "gita") + cleaner.load_jsonl(cleaner.UPANISHAD_DATASET, "upanishads")
    cleaner.evaluate_records(records)
    cleaner.deduplicate_by_prompt(records)
    cleaner.enforce_uniqueness(records)
    pool: list[RewriteCandidate] = []
    for record in records:
        if record.keep and record.final_score >= 80:
            continue
        base_reasons = {reason.split(":")[0] if ":" in reason else reason for reason in record.removal_reasons}
        if "duplicate_user_prompt" not in base_reasons:
            continue
        if record.final_score < 78:
            continue
        if SEVERE_REASONS & base_reasons:
            continue
        if assistant_has_forbidden_structure(record):
            continue
        theme = classify_theme(record)
        pool.append(RewriteCandidate(record=record, theme=theme))
    pool.sort(
        key=lambda item: (
            item.record.final_score,
            item.record.response_quality_score,
            -sum(item.record.assistant.lower().count(scaffold) for scaffold in cleaner.REPEATED_SCAFFOLDS),
        ),
        reverse=True,
    )
    return pool


def choose_rewrite_text(
    candidate: RewriteCandidate,
    used_exact_prompts: set[str],
    used_near_prompts: set[str],
    theme_variant_index: Counter[str],
) -> str | None:
    templates = THEME_TEMPLATE_BANKS.get(candidate.theme, THEME_TEMPLATE_BANKS["clarity_decision"])
    start = (candidate.record.line_number + candidate.record.final_score) % len(templates)
    for offset in range(len(templates)):
        template = templates[(start + offset + theme_variant_index[candidate.theme]) % len(templates)]
        exact_key = cleaner.normalize_text(template)
        near_key = prompt_fingerprint(template)
        if exact_key in used_exact_prompts:
            continue
        if near_key in used_near_prompts:
            continue
        if template.startswith("I am trying to work on"):
            continue
        theme_variant_index[candidate.theme] += 1
        return template
    return None


def scaffold_counts(records: list[dict]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for record in records:
        assistant = get_message_content(record, "assistant").lower()
        for scaffold in cleaner.REPEATED_SCAFFOLDS:
            if scaffold in assistant:
                counts[scaffold] += 1
    return counts


def build_rewritten_record(record: dict, new_user: str) -> dict:
    messages = []
    for message in record["messages"]:
        cloned = dict(message)
        if cloned["role"] == "user":
            cloned["content"] = new_user
        messages.append(cloned)
    return {"messages": messages}


def validate_records(records: list[dict]) -> tuple[int, int]:
    exact_prompts: set[str] = set()
    assistant_exact: set[str] = set()
    repeated_scaffolds = scaffold_counts(records)
    for scaffold, count in repeated_scaffolds.items():
        if count > SAFE_SCAFFOLD_THRESHOLD:
            raise ValueError(f"scaffold {scaffold!r} exceeds safe threshold with count {count}")
    for record in records:
        roles = {message["role"] for message in record["messages"]}
        if roles != cleaner.EXPECTED_ROLES:
            raise ValueError("invalid roles in output dataset")
        prompt = get_message_content(record, "user")
        assistant = get_message_content(record, "assistant")
        prompt_key = cleaner.normalize_text(prompt)
        assistant_key = cleaner.normalize_text(assistant)
        if prompt_key in exact_prompts:
            raise ValueError(f"duplicate prompt detected: {prompt}")
        if assistant_key in assistant_exact:
            raise ValueError("duplicate assistant response detected")
        exact_prompts.add(prompt_key)
        assistant_exact.add(assistant_key)
        lower = assistant.lower()
        if "1." in assistant or "**" in assistant:
            raise ValueError("unsafe assistant structure detected")
        if has_scripture_leakage(lower):
            raise ValueError("scripture leakage detected")
        if "again again" in lower or "cold and cold" in lower:
            raise ValueError("loop-like phrase detected")
    return len(exact_prompts), len(assistant_exact)


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for index, record in enumerate(records):
            handle.write(json.dumps(record, ensure_ascii=False))
            if index != len(records) - 1:
                handle.write("\n")


def build_metadata(start_count: int, added_count: int, final_count: int) -> str:
    return "\n".join(
        [
            "Dataset: Marg Darshak Merged v2.1",
            f"Date: {date.today().isoformat()}",
            "Purpose: Marg Darshak LoRA v2 cleaned dataset with prompt-only rewrite expansion",
            "",
            "Source datasets:",
            f"- {cleaner.GITA_DATASET}",
            f"- {cleaner.UPANISHAD_DATASET}",
            f"- base cleaned dataset: {MERGED_V2_PATH}",
            f"- cleanup analysis: {ROOT_DIR / 'training' / 'evaluation' / 'merged_v2_dataset_cleanup_report.md'}",
            "",
            "Counts:",
            f"- merged_v2 starting count: {start_count}",
            f"- rewritten additions: {added_count}",
            f"- merged_v2.1 final count: {final_count}",
        ]
    )


def build_report(
    start_count: int,
    added: list[RewriteCandidate],
    skipped: list[RewriteCandidate],
    final_records: list[dict],
    before_scaffolds: Counter[str],
    after_scaffolds: Counter[str],
) -> str:
    lines = [
        "# Merged v2.1 Rewrite Expansion Report",
        "",
        f"- starting v2 count: {start_count}",
        f"- added rewritten count: {len(added)}",
        f"- final v2.1 count: {len(final_records)}",
        f"- skipped count: {len(skipped)}",
        "",
        "## Repeated Scaffold Counts Before",
        "",
    ]
    for scaffold, count in before_scaffolds.most_common():
        lines.append(f"- `{scaffold}`: {count}")
    lines.extend(["", "## Repeated Scaffold Counts After", ""])
    for scaffold, count in after_scaffolds.most_common():
        lines.append(f"- `{scaffold}`: {count}")
    lines.extend(["", "## Duplicate Prompt Checks", ""])
    lines.append(f"- exact unique prompts: {len({cleaner.normalize_text(get_message_content(record, 'user')) for record in final_records})}")
    lines.append(f"- exact unique assistant responses: {len({cleaner.normalize_text(get_message_content(record, 'assistant')) for record in final_records})}")
    lines.extend(["", "## Rewrite Examples Before/After", ""])
    for candidate in added[:20]:
        lines.append(f"- source: {candidate.record.source_name}:{candidate.record.line_number}")
        lines.append(f"  theme: {candidate.theme}")
        lines.append(f"  before: {candidate.record.user}")
        lines.append(f"  after: {candidate.rewritten_user}")
        lines.append(f"  assistant_score: {candidate.record.response_quality_score} final_score: {candidate.record.final_score}")
        lines.append("")
    lines.extend(["## Skipped Examples", ""])
    for candidate in skipped[:20]:
        lines.append(f"- source: {candidate.record.source_name}:{candidate.record.line_number}")
        lines.append(f"  theme: {candidate.theme}")
        lines.append(f"  user: {candidate.record.user}")
        lines.append(f"  skip_reason: {candidate.skip_reason}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def main() -> int:
    base_records = load_jsonl(MERGED_V2_PATH)
    base_count = len(base_records)
    before_scaffolds = scaffold_counts(base_records)
    candidates = candidate_pool()

    used_exact_prompts = {cleaner.normalize_text(get_message_content(record, "user")) for record in base_records}
    used_near_prompts = {prompt_fingerprint(get_message_content(record, "user")) for record in base_records}
    used_assistant = {cleaner.normalize_text(get_message_content(record, "assistant")) for record in base_records}
    theme_counts = Counter(classify_theme(cleaner.Record(
        source_name="base",
        line_number=index,
        record=record,
        system=get_message_content(record, "system"),
        user=get_message_content(record, "user"),
        assistant=get_message_content(record, "assistant"),
        user_key=cleaner.normalize_text(get_message_content(record, "user")),
        user_near_key=prompt_fingerprint(get_message_content(record, "user")),
        assistant_key=cleaner.normalize_text(get_message_content(record, "assistant")),
    )) for index, record in enumerate(base_records, start=1))
    theme_variant_index: Counter[str] = Counter()

    added: list[RewriteCandidate] = []
    skipped: list[RewriteCandidate] = []
    final_records = list(base_records)

    theme_soft_caps = {
        "clarity_decision": 6,
        "duty_action": 6,
        "discipline_self_control": 8,
        "trust_let_go": 8,
        "attachment_outcome": 6,
        "fear_steadiness": 6,
    }
    added_per_theme: Counter[str] = Counter()

    for candidate in candidates:
        if len(final_records) >= TARGET_PREFERRED:
            candidate.skip_reason = "target_reached"
            skipped.append(candidate)
            continue
        if added_per_theme[candidate.theme] >= theme_soft_caps.get(candidate.theme, 6):
            candidate.skip_reason = "theme_cap_reached"
            skipped.append(candidate)
            continue
        assistant_key = cleaner.normalize_text(candidate.record.assistant)
        if assistant_key in used_assistant:
            candidate.skip_reason = "duplicate_assistant_response"
            skipped.append(candidate)
            continue
        rewritten = choose_rewrite_text(candidate, used_exact_prompts, used_near_prompts, theme_variant_index)
        if not rewritten:
            candidate.skip_reason = "no_safe_prompt_rewrite"
            skipped.append(candidate)
            continue

        new_record = build_rewritten_record(candidate.record.record, rewritten)
        final_records.append(new_record)
        candidate.rewritten_user = rewritten
        added.append(candidate)
        added_per_theme[candidate.theme] += 1
        used_exact_prompts.add(cleaner.normalize_text(rewritten))
        used_near_prompts.add(prompt_fingerprint(rewritten))
        used_assistant.add(assistant_key)

    exact_prompt_count, exact_assistant_count = validate_records(final_records)
    after_scaffolds = scaffold_counts(final_records)

    write_jsonl(MERGED_V21_PATH, final_records)
    write_jsonl(TRAINING_COPY, final_records)
    METADATA_PATH.write_text(build_metadata(base_count, len(added), len(final_records)), encoding="utf-8")
    REPORT_PATH.write_text(
        build_report(
            start_count=base_count,
            added=added,
            skipped=skipped,
            final_records=final_records,
            before_scaffolds=before_scaffolds,
            after_scaffolds=after_scaffolds,
        ),
        encoding="utf-8",
    )

    print(f"starting v2 count: {base_count}")
    print(f"added rewritten count: {len(added)}")
    print(f"final v2.1 count: {len(final_records)}")
    print(f"skipped count: {len(skipped)}")
    print(f"exact unique prompts: {exact_prompt_count}")
    print(f"exact unique assistant responses: {exact_assistant_count}")
    print("Repeated scaffold counts after:")
    for scaffold, count in after_scaffolds.most_common():
        print(f"  {scaffold}: {count}")
    if len(final_records) < TARGET_MIN:
        print(f"warning: final count {len(final_records)} is below hard minimum target {TARGET_MIN}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
