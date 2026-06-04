#!/usr/bin/env python3
"""Score base and LoRA responses with deterministic rubric-based heuristics."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
EVAL_DIR = ROOT_DIR / "training" / "evaluation"
RESULTS_PATH = EVAL_DIR / "results.json"
REPORT_PATH = EVAL_DIR / "evaluation_report.md"

CALM_WORDS = {
    "calm",
    "steady",
    "gently",
    "gentle",
    "soften",
    "patience",
    "patient",
    "grounded",
    "breathe",
    "breathing",
    "quietly",
}
PHILOSOPHICAL_WORDS = {
    "clarity",
    "wisdom",
    "truth",
    "attachment",
    "discipline",
    "fear",
    "duty",
    "action",
    "choice",
    "steadiness",
    "awareness",
    "inner",
    "ego",
    "desire",
    "trust",
    "surrender",
    "purpose",
}
ACTION_WORDS = {
    "write",
    "choose",
    "pause",
    "notice",
    "name",
    "act",
    "take",
    "complete",
    "return",
    "release",
    "remove",
    "schedule",
    "ground",
    "soften",
}
PREACHY_PATTERNS = re.compile(
    r"\b(must obey|god commands|worship|sinful|punishment|you should surrender to god|only god)\b",
    re.IGNORECASE,
)
EMPATHY_PATTERNS = re.compile(
    r"\b(it makes sense|understandable|you are not weak|human|it is natural|anyone would)\b",
    re.IGNORECASE,
)
SCRIPTURE_PATTERNS = re.compile(
    r"\b(arjuna|krishna|sanjaya|gandeeva|o king|bhagavad gita|chapter \d+)\b",
    re.IGNORECASE,
)


def load_results() -> list[dict[str, object]]:
    """Load generated evaluation responses."""

    with RESULTS_PATH.open("r", encoding="utf-8") as handle:
        results = json.load(handle)
    if not isinstance(results, list) or not results:
        raise ValueError("results.json must contain a non-empty list")
    return results


def normalize_words(text: str) -> list[str]:
    """Return normalized word tokens."""

    return re.findall(r"[a-z']+", text.lower())


def repeated_ngram_penalty(text: str) -> int:
    """Return a rough repetition penalty from repeated 3-grams."""

    words = normalize_words(text)
    ngrams = [" ".join(words[index : index + 3]) for index in range(max(0, len(words) - 2))]
    if not ngrams:
        return 0
    counts = Counter(ngrams)
    return sum(count - 1 for count in counts.values() if count > 1)


def clamp(value: int) -> int:
    """Clamp rubric scores to 1-5."""

    return max(1, min(5, value))


def score_response(prompt: str, response: str) -> dict[str, int]:
    """Score one response across the evaluation rubric."""

    lower = response.lower()
    words = set(normalize_words(response))

    calm_score = 2 + min(3, sum(1 for word in CALM_WORDS if word in words))
    if "!" in response:
        calm_score -= 1

    philosophical_score = 2 + min(3, sum(1 for word in PHILOSOPHICAL_WORDS if word in words) // 2 + 1)
    if SCRIPTURE_PATTERNS.search(response):
        philosophical_score -= 1

    actionable_hits = sum(1 for word in ACTION_WORDS if word in words)
    practical_score = 1
    if actionable_hits >= 1:
        practical_score = 3
    if actionable_hits >= 2:
        practical_score = 4
    if actionable_hits >= 3:
        practical_score = 5
    if re.search(r"\b(today|next step|for the next hour|one action|one step)\b", lower):
        practical_score += 1

    non_preachy_score = 5
    if PREACHY_PATTERNS.search(response):
        non_preachy_score = 1
    elif SCRIPTURE_PATTERNS.search(response):
        non_preachy_score -= 2
    if re.search(r"\byou must\b", lower):
        non_preachy_score -= 1

    emotional_score = 2
    if EMPATHY_PATTERNS.search(response):
        emotional_score += 2
    if re.search(r"\b(feel|feeling|fear|grief|anger|confusion|restless|uncertain)\b", lower):
        emotional_score += 1

    repetition_score = 5
    penalty = repeated_ngram_penalty(response)
    if penalty >= 2:
        repetition_score -= 1
    if penalty >= 4:
        repetition_score -= 1
    if ";" in response:
        repetition_score -= 1
    if response.count(";") >= 3:
        repetition_score -= 1

    scores = {
        "calm_tone": clamp(calm_score),
        "philosophical_clarity": clamp(philosophical_score),
        "practical_actionability": clamp(practical_score),
        "non_preachy_style": clamp(non_preachy_score),
        "emotional_understanding": clamp(emotional_score),
        "repetition_issues": clamp(repetition_score),
    }
    scores["total"] = sum(scores.values())
    return scores


def format_score_line(label: str, scores: dict[str, int]) -> str:
    """Format one score block line."""

    return (
        f"{label}: total={scores['total']} | "
        f"calm={scores['calm_tone']} | "
        f"clarity={scores['philosophical_clarity']} | "
        f"action={scores['practical_actionability']} | "
        f"non_preachy={scores['non_preachy_style']} | "
        f"empathy={scores['emotional_understanding']} | "
        f"repetition={scores['repetition_issues']}"
    )


def main() -> int:
    """Score base and LoRA outputs and write the evaluation report."""

    if not RESULTS_PATH.exists():
        raise FileNotFoundError(f"results file not found: {RESULTS_PATH}")

    results = load_results()
    report_lines: list[str] = [
        "# Marg Darshak LoRA Evaluation Report",
        "",
        "This report uses a deterministic rubric to compare base Qwen against the Marg Darshak LoRA adapter.",
        "",
    ]

    base_total_score = 0
    lora_total_score = 0

    for item in results:
        prompt = str(item["prompt"])
        base_response = str(item["base_response"])
        lora_response = str(item["lora_response"])

        base_scores = score_response(prompt, base_response)
        lora_scores = score_response(prompt, lora_response)

        base_total_score += base_scores["total"]
        lora_total_score += lora_scores["total"]

        report_lines.extend(
            [
                f"## Prompt {item['id']}",
                "",
                f"**Prompt:** {prompt}",
                "",
                format_score_line("Base", base_scores),
                "",
                format_score_line("LoRA", lora_scores),
                "",
                "**Base Response**",
                "",
                base_response,
                "",
                "**LoRA Response**",
                "",
                lora_response,
                "",
            ]
        )

    prompt_count = len(results)
    base_average = round(base_total_score / prompt_count, 2)
    lora_average = round(lora_total_score / prompt_count, 2)
    verdict = "LoRA outperformed base Qwen." if lora_total_score > base_total_score else "Base Qwen outperformed or matched LoRA."

    summary_lines = [
        "## Summary",
        "",
        f"* prompt_count: {prompt_count}",
        f"* base_total_score: {base_total_score}",
        f"* lora_total_score: {lora_total_score}",
        f"* base_average_score: {base_average}",
        f"* lora_average_score: {lora_average}",
        f"* verdict: {verdict}",
        "",
    ]

    REPORT_PATH.write_text("\n".join(summary_lines + report_lines), encoding="utf-8")
    print(f"base_total_score={base_total_score}")
    print(f"lora_total_score={lora_total_score}")
    print(f"report={REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
