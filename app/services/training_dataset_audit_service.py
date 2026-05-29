"""Services for auditing training examples before fine-tuning export."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from difflib import SequenceMatcher

from app.models.training_example import TrainingExample


CORRUPTION_PATTERN = re.compile(r"[{}@ïÌœ]|H¥|�|jkhh|vijkhh|iijkhh|viiijkhh")
SOURCE_METADATA_PATTERN = re.compile(
    r"\b(the bhagavad gita|chapter\s+\d+|page\s+\d+|\d+\.\d+)\b",
    re.IGNORECASE,
)
UNSAFE_MENTAL_HEALTH_PATTERN = re.compile(
    r"\b(stop medication|ignore your doctor|do not seek help|you do not need help|cure depression|cure anxiety|replace therapy)\b",
    re.IGNORECASE,
)
PREACHY_PATTERN = re.compile(
    r"\b(only god can save|must worship|blindly obey|surrender completely to god|your suffering is punishment)\b",
    re.IGNORECASE,
)
PRACTICAL_ACTION_PATTERN = re.compile(
    r"\b(begin|notice|choose|act|return|pause|write|breathe|practice|take|start|speak|rest)\b",
    re.IGNORECASE,
)

OPENING_WORD_COUNT = 12
REPEATED_OPENING_WARNING_THRESHOLD = 20
REPEATED_OPENING_REJECTION_THRESHOLD = 40
NEAR_DUPLICATE_SIMILARITY = 0.96


@dataclass(slots=True)
class TrainingDatasetAuditResult:
    """In-memory dataset audit result for a training example."""

    training_example_id: int
    dataset_quality_score: float
    dataset_status: str
    issues: list[str]
    opening_phrase: str


class TrainingDatasetAuditService:
    """Audit training examples for fine-tuning readiness."""

    def audit_examples(
        self,
        training_examples: list[TrainingExample],
    ) -> list[TrainingDatasetAuditResult]:
        """Return dataset audit results for a batch of training examples."""

        opening_counts = Counter(
            self.extract_opening_phrase(training_example.assistant_response)
            for training_example in training_examples
        )
        normalized_responses = {
            training_example.id: self._normalize_text(training_example.assistant_response)
            for training_example in training_examples
        }
        duplicate_counts = Counter(normalized_responses.values())
        near_duplicate_ids = self._detect_near_duplicates(normalized_responses)

        results: list[TrainingDatasetAuditResult] = []
        for training_example in training_examples:
            opening_phrase = self.extract_opening_phrase(training_example.assistant_response)
            issues: list[str] = []
            score = 100.0
            normalized_response = normalized_responses[training_example.id]
            word_count = len(training_example.assistant_response.split())

            opening_count = opening_counts[opening_phrase]
            if opening_count >= REPEATED_OPENING_REJECTION_THRESHOLD:
                issues.append("repeated_opening_phrase")
                score -= 25.0
            elif opening_count >= REPEATED_OPENING_WARNING_THRESHOLD:
                issues.append("opening_phrase_overused")
                score -= 12.0

            if duplicate_counts[normalized_response] > 1:
                issues.append("duplicate_response")
                score -= 35.0
            elif training_example.id in near_duplicate_ids:
                issues.append("near_duplicate_response")
                score -= 20.0

            if CORRUPTION_PATTERN.search(training_example.assistant_response):
                issues.append("corrupted_characters")
                score -= 40.0
            if SOURCE_METADATA_PATTERN.search(training_example.assistant_response):
                issues.append("source_metadata_leakage")
                score -= 30.0
            if word_count < 60:
                issues.append("response_too_short")
                score -= 20.0
            if word_count > 180:
                issues.append("response_too_long")
                score -= 15.0
            if UNSAFE_MENTAL_HEALTH_PATTERN.search(training_example.assistant_response):
                issues.append("unsafe_mental_health_advice")
                score -= 45.0
            if PREACHY_PATTERN.search(training_example.assistant_response):
                issues.append("overly_preachy_tone")
                score -= 25.0
            if not PRACTICAL_ACTION_PATTERN.search(training_example.assistant_response):
                issues.append("missing_practical_action")
                score -= 20.0

            score = max(0.0, min(score, 100.0))
            results.append(
                TrainingDatasetAuditResult(
                    training_example_id=training_example.id,
                    dataset_quality_score=score,
                    dataset_status=self._determine_status(score, issues),
                    issues=issues,
                    opening_phrase=opening_phrase,
                )
            )

        return results

    def top_rejection_reasons(
        self,
        audit_results: list[TrainingDatasetAuditResult],
    ) -> list[tuple[str, int]]:
        """Return aggregated issue counts for non-approved examples."""

        counter: Counter[str] = Counter()
        for audit_result in audit_results:
            if audit_result.dataset_status != "approved":
                counter.update(audit_result.issues)
        return counter.most_common()

    def opening_phrase_distribution(
        self,
        training_examples: list[TrainingExample],
    ) -> list[tuple[str, int]]:
        """Return opening phrase counts for a batch of examples."""

        counter = Counter(
            self.extract_opening_phrase(training_example.assistant_response)
            for training_example in training_examples
        )
        return counter.most_common()

    def extract_opening_phrase(self, response: str) -> str:
        """Return a normalized leading phrase from an assistant response."""

        tokens = response.strip().split()
        if not tokens:
            return ""
        opening = " ".join(tokens[:OPENING_WORD_COUNT])
        return opening.rstrip(".,;:!?").lower()

    def _determine_status(self, score: float, issues: list[str]) -> str:
        """Map a dataset audit score to a review status."""

        hard_reject_issues = {
            "duplicate_response",
            "corrupted_characters",
            "unsafe_mental_health_advice",
        }
        if score < 60.0 or any(issue in hard_reject_issues for issue in issues):
            return "rejected"
        if score >= 85.0 and not any(
            issue in {"repeated_opening_phrase", "near_duplicate_response", "source_metadata_leakage"}
            for issue in issues
        ):
            return "approved"
        return "needs_review"

    def _normalize_text(self, text: str) -> str:
        """Return a normalized text string for duplicate detection."""

        lowered = text.lower()
        lowered = SOURCE_METADATA_PATTERN.sub(" ", lowered)
        lowered = re.sub(r"[^a-z0-9\s]", " ", lowered)
        lowered = re.sub(r"\s+", " ", lowered).strip()
        return lowered

    def _detect_near_duplicates(self, normalized_responses: dict[int, str]) -> set[int]:
        """Return training example IDs involved in near-duplicate pairs."""

        near_duplicate_ids: set[int] = set()
        items = list(normalized_responses.items())
        for index, (left_id, left_text) in enumerate(items):
            if len(left_text.split()) < 20:
                continue
            left_prefix = left_text[:36]
            for right_id, right_text in items[index + 1 :]:
                if abs(len(left_text) - len(right_text)) > 40:
                    continue
                if left_prefix[:18] != right_text[:18] and left_prefix[-18:] != right_text[:36][-18:]:
                    continue
                similarity = SequenceMatcher(None, left_text, right_text).ratio()
                if similarity >= NEAR_DUPLICATE_SIMILARITY:
                    near_duplicate_ids.add(left_id)
                    near_duplicate_ids.add(right_id)
        return near_duplicate_ids
