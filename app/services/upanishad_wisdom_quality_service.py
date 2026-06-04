"""Quality rules for Upanishad distilled wisdom refinement."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

from app.models.wisdom_entry import WisdomEntry


CORRUPTION_PATTERN = re.compile(r"[{}@ïÌœ]|H¥|�|\.\.\.")
SCRIPTURE_NARRATION_PATTERN = re.compile(
    r"\b(these gods|thus he said|taking hold of the bow|therefore these|death told him|he then said|o death|o brahmana)\b",
    re.IGNORECASE,
)
SPEAKER_ONLY_PATTERN = re.compile(r"^(death said|teacher said|disciple said|student said)\b", re.IGNORECASE)
RITUAL_PATTERN = re.compile(
    r"\b(sacrifice|oblations|altar|agnihotra|ritual|rites?|vow of holding fire|bricks|guest enters the houses)\b",
    re.IGNORECASE,
)
GENERIC_PATTERN = re.compile(
    r"^(truth becomes transformative|real learning matures|peace grows|freedom deepens|fear softens|a restless mind becomes clearer)\b",
    re.IGNORECASE,
)
METAPHYSICAL_PATTERN = re.compile(
    r"\b(absolute|imperishable|all-pervasive|indivisible|immortal|truth alone|deepest awareness|what is deepest in you)\b",
    re.IGNORECASE,
)
INNER_CONFLICT_PATTERN = re.compile(
    r"\b(fear|desire|grief|restless|ego|pride|clarity|discipline|control|attachment|choice|humility|confusion|steadiness)\b",
    re.IGNORECASE,
)
SELF_KNOWLEDGE_PATTERN = re.compile(
    r"\b(self-knowledge|awareness|truth|understanding|humility|attention|witness|clarity)\b",
    re.IGNORECASE,
)
HUMAN_APPLICABILITY_PATTERN = re.compile(
    r"\b(choose|attention|practice|mind|heart|control|clarity|desire|fear|pride|attachment|learning|discipline|truth)\b",
    re.IGNORECASE,
)
PRACTICAL_TRAINING_PATTERN = re.compile(
    r"\b(choose|practice|pause|train|guide|loosen|remember|live|deepens|grows)\b",
    re.IGNORECASE,
)


@dataclass(slots=True)
class UpanishadWisdomQualityResult:
    """In-memory Upanishad distilled wisdom quality evaluation result."""

    principle_quality_score: float
    principle_status: str
    confidence_score: float
    reasons: list[str]


class UpanishadWisdomQualityService:
    """Score distilled Upanishad wisdom for downstream training eligibility."""

    def evaluate_entry(self, wisdom_entry: WisdomEntry) -> UpanishadWisdomQualityResult:
        """Return quality scoring and status for one Upanishad wisdom entry."""

        distilled = self._clean_text(wisdom_entry.distilled_wisdom)
        reasons: list[str] = []
        score = 50.0

        if not distilled:
            reasons.append("blank_distilled_wisdom")
            score = 0.0
            return self._result(score, reasons)

        if CORRUPTION_PATTERN.search(distilled):
            reasons.append("contamination_or_ocr")
            score -= 40.0
        if SCRIPTURE_NARRATION_PATTERN.search(distilled):
            reasons.append("scripture_narration")
            score -= 30.0
        if SPEAKER_ONLY_PATTERN.match(distilled):
            reasons.append("speaker_only")
            score -= 30.0
        if RITUAL_PATTERN.search(distilled):
            reasons.append("ritual_only")
            score -= 30.0

        word_count = len(distilled.split())
        if word_count < 8:
            reasons.append("too_short")
            score -= 25.0
        if word_count > 30:
            reasons.append("too_long")
            score -= 25.0

        if HUMAN_APPLICABILITY_PATTERN.search(distilled):
            score += 20.0
        else:
            reasons.append("weak_human_applicability")

        if INNER_CONFLICT_PATTERN.search(distilled):
            score += 15.0
        else:
            reasons.append("weak_inner_conflict_relevance")

        if SELF_KNOWLEDGE_PATTERN.search(distilled):
            score += 15.0
        else:
            reasons.append("weak_self_knowledge_signal")

        if wisdom_entry.emotional_tags:
            score += 10.0
        else:
            reasons.append("missing_emotional_tags")

        if PRACTICAL_TRAINING_PATTERN.search(distilled):
            score += 10.0
        else:
            reasons.append("weak_practical_training_potential")

        if METAPHYSICAL_PATTERN.search(distilled) and not INNER_CONFLICT_PATTERN.search(distilled):
            reasons.append("too_metaphysical")
            score -= 20.0

        if GENERIC_PATTERN.match(distilled):
            reasons.append("too_generic")
            score -= 20.0

        if not wisdom_entry.philosophical_tags:
            reasons.append("missing_philosophical_tags")

        if not wisdom_entry.use_cases:
            reasons.append("weak_human_problem_mapping")

        return self._result(score, reasons)

    def top_reason_counts(self, results: list[UpanishadWisdomQualityResult], status: str) -> list[tuple[str, int]]:
        """Return aggregated reason counts for a target review status."""

        counter: Counter[str] = Counter()
        for result in results:
            if result.principle_status == status:
                counter.update(result.reasons)
        return counter.most_common()

    def _result(self, score: float, reasons: list[str]) -> UpanishadWisdomQualityResult:
        """Build a normalized evaluation result."""

        normalized_score = max(0.0, min(score, 100.0))
        if any(
            reason in {
                "blank_distilled_wisdom",
                "contamination_or_ocr",
                "scripture_narration",
                "speaker_only",
                "ritual_only",
            }
            for reason in reasons
        ):
            status = "rejected"
        elif normalized_score >= 85.0 and not any(
            reason in {
                "missing_emotional_tags",
                "missing_philosophical_tags",
                "weak_human_problem_mapping",
                "too_metaphysical",
                "too_generic",
            }
            for reason in reasons
        ):
            status = "approved"
        elif normalized_score < 60.0:
            status = "rejected"
        else:
            status = "needs_review"

        confidence_score = self._determine_confidence(normalized_score, status)
        return UpanishadWisdomQualityResult(
            principle_quality_score=normalized_score,
            principle_status=status,
            confidence_score=confidence_score,
            reasons=reasons,
        )

    def _determine_confidence(self, score: float, status: str) -> float:
        """Align confidence score to the refined quality status."""

        if status == "approved":
            return max(85.0, score)
        if status == "needs_review":
            return min(84.0, max(60.0, score))
        return min(59.0, score)

    def _clean_text(self, text: str | None) -> str | None:
        """Normalize whitespace and trim text."""

        if not text:
            return None
        cleaned_text = " ".join(text.split()).strip()
        return cleaned_text or None
