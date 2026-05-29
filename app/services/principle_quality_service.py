"""Services for evaluating and refining wisdom principle quality."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

from app.models.wisdom_entry import WisdomEntry


CORRUPTION_PATTERN = re.compile(r"[{}@ïÌœ]|H¥|jkhh|vijkhh|iijkhh|viiijkhh|�")
HEADER_FOOTER_PATTERN = re.compile(
    r"(chapter\s+\d+|page\s+\d+|the bhagavad gita|introduction\s+\d+)",
    re.IGNORECASE,
)
SPEAKER_START_PATTERN = re.compile(
    r"^(o king|o partha|arjuna said|sanjaya said|krishna said)\b",
    re.IGNORECASE,
)
GENERIC_PATTERN = re.compile(
    r"^(pause, observe your inner state|listen to some more|i am the|now i will|thus, i heard)\b",
    re.IGNORECASE,
)
NARRATION_PATTERN = re.compile(
    r"\b(said|asked|look at|sounded|heard|saw|narrated|replied|rushed)\b",
    re.IGNORECASE,
)
LESSON_PATTERN = re.compile(
    r"\b(should|must|let go|perform|surrender|focus|control|discipline|duty|detachment|wisdom|fear|desire|clarity|devotion|self-control|action)\b",
    re.IGNORECASE,
)
INNER_CONFLICT_PATTERN = re.compile(
    r"\b(inner|mind|fear|desire|attachment|anger|confusion|discipline|devotion|self-control|duty|detachment|clarity|wisdom|surrender)\b",
    re.IGNORECASE,
)


@dataclass(slots=True)
class PrincipleQualityResult:
    """In-memory principle quality evaluation result."""

    principle_quality_score: float
    principle_status: str
    confidence_score: float
    reasons: list[str]


class PrincipleQualityService:
    """Score and refine wisdom principles for downstream use."""

    def evaluate_entry(self, wisdom_entry: WisdomEntry) -> PrincipleQualityResult:
        """Return quality scoring and status for one wisdom entry."""

        principle = self._clean_text(wisdom_entry.extracted_principle)
        translation = self._clean_text(wisdom_entry.translation)
        commentary = self._clean_text(wisdom_entry.commentary)

        reasons: list[str] = []
        score = 100.0

        if not principle:
            reasons.append("missing_principle")
            score -= 60.0
        else:
            if len(principle.split()) < 10:
                reasons.append("principle_too_short")
                score -= 35.0
            if SPEAKER_START_PATTERN.match(principle):
                reasons.append("speaker_text_opening")
                score -= 35.0
            if CORRUPTION_PATTERN.search(principle):
                reasons.append("corrupted_characters")
                score -= 40.0
            if HEADER_FOOTER_PATTERN.search(principle):
                reasons.append("header_footer_artifact")
                score -= 30.0
            if GENERIC_PATTERN.match(principle):
                reasons.append("too_generic")
                score -= 30.0
            if self._is_mostly_narration(principle):
                reasons.append("mostly_narration")
                score -= 25.0
            if not LESSON_PATTERN.search(principle):
                reasons.append("weak_lesson_signal")
                score -= 10.0
            if not INNER_CONFLICT_PATTERN.search(principle):
                reasons.append("weak_inner_conflict_signal")
                score -= 10.0

        if translation and CORRUPTION_PATTERN.search(translation):
            reasons.append("translation_corruption")
            score -= 20.0
        if commentary and CORRUPTION_PATTERN.search(commentary):
            reasons.append("commentary_corruption")
            score -= 20.0

        score = max(0.0, min(score, 100.0))
        status = self._determine_status(score, reasons)
        confidence_score = self._determine_confidence(score)

        return PrincipleQualityResult(
            principle_quality_score=score,
            principle_status=status,
            confidence_score=confidence_score,
            reasons=reasons,
        )

    def top_rejection_reasons(self, results: list[PrincipleQualityResult]) -> list[tuple[str, int]]:
        """Return aggregated rejection reason counts."""

        counter: Counter[str] = Counter()
        for result in results:
            if result.principle_status == "rejected":
                counter.update(result.reasons)
        return counter.most_common()

    def _determine_status(self, score: float, reasons: list[str]) -> str:
        """Map a quality score and reasons to a review status."""

        if score < 60.0 or any(
            reason in {"missing_principle", "corrupted_characters", "header_footer_artifact"}
            for reason in reasons
        ):
            return "rejected"
        if score >= 85.0:
            return "approved"
        return "needs_review"

    def _determine_confidence(self, score: float) -> float:
        """Align confidence score with principle quality buckets."""

        if score >= 85.0:
            return max(85.0, score)
        if score >= 60.0:
            return min(84.0, max(60.0, score))
        return min(59.0, score)

    def _is_mostly_narration(self, principle: str) -> bool:
        """Return True when narration signals outweigh teaching signals."""

        narration_hits = len(NARRATION_PATTERN.findall(principle))
        lesson_hits = len(LESSON_PATTERN.findall(principle))
        return narration_hits >= 2 and lesson_hits == 0

    def _clean_text(self, text: str | None) -> str | None:
        """Normalize whitespace and trim text."""

        if not text:
            return None
        cleaned_text = " ".join(text.split()).strip()
        return cleaned_text or None
