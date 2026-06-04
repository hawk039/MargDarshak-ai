"""Audit Upanishad training examples before pilot dataset export."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

from app.models.training_example import TrainingExample


CORRUPTION_PATTERN = re.compile(r"[{}@ïÌœ]|H¥|�|jkhh|vijkhh|iijkhh|viiijkhh")
FORBIDDEN_PATTERN = re.compile(
    r"\b(kena|katha|mundaka|upanishad|chapter|passage|verse|these gods|taking hold of the bow|brahman said)\b",
    re.IGNORECASE,
)
PREACHY_PATTERN = re.compile(
    r"\b(only god can save|must worship|blindly obey|your suffering is punishment|submit completely)\b",
    re.IGNORECASE,
)
MEDICAL_CLAIM_PATTERN = re.compile(
    r"\b(cure anxiety|cure depression|replace therapy|you do not need therapy|stop medication|ignore your doctor)\b",
    re.IGNORECASE,
)
PRACTICAL_ACTION_PATTERN = re.compile(
    r"\b(write|choose|pause|return|take|name|set|practice|notice|pick|ask|breathe|complete|spend)\b",
    re.IGNORECASE,
)
LISTICLE_PATTERN = re.compile(r"(^|\n)\s*(\d+\.|- )")
OPENING_WORD_COUNT = 10
REPEATED_OPENING_THRESHOLD = 2
DUPLICATE_USER_PROBLEM_THRESHOLD = 1


@dataclass(slots=True)
class UpanishadCorpusAuditStats:
    """Corpus-level repetition signals for Upanishad training examples."""

    opening_counts: Counter[str]
    response_counts: Counter[str]
    response_fingerprint_counts: Counter[str]
    user_problem_counts: Counter[str]


@dataclass(slots=True)
class UpanishadTrainingAuditResult:
    """In-memory audit result for one Upanishad training example."""

    training_example_id: int
    dataset_quality_score: float
    dataset_status: str
    issues: list[str]
    opening_phrase: str


class UpanishadTrainingDatasetAuditService:
    """Audit Upanishad-generated training examples for dataset export readiness."""

    def build_corpus_stats(self, training_examples: list[TrainingExample]) -> UpanishadCorpusAuditStats:
        """Build corpus-level audit signals."""

        opening_counts: Counter[str] = Counter()
        response_counts: Counter[str] = Counter()
        response_fingerprint_counts: Counter[str] = Counter()
        user_problem_counts: Counter[str] = Counter()

        for example in training_examples:
            opening_phrase = self.extract_opening_phrase(example.assistant_response)
            normalized_response = self._normalize_text(example.assistant_response)
            response_fingerprint = self.response_fingerprint(example.assistant_response)
            normalized_problem = self._normalize_text(example.user_problem)

            opening_counts[opening_phrase] += 1
            response_counts[normalized_response] += 1
            if response_fingerprint:
                response_fingerprint_counts[response_fingerprint] += 1
            user_problem_counts[normalized_problem] += 1

        return UpanishadCorpusAuditStats(
            opening_counts=opening_counts,
            response_counts=response_counts,
            response_fingerprint_counts=response_fingerprint_counts,
            user_problem_counts=user_problem_counts,
        )

    def audit_examples(self, training_examples: list[TrainingExample]) -> list[UpanishadTrainingAuditResult]:
        """Audit a batch of Upanishad training examples."""

        corpus_stats = self.build_corpus_stats(training_examples)
        return [
            self.audit_example(example, corpus_stats)
            for example in training_examples
        ]

    def audit_example(
        self,
        training_example: TrainingExample,
        corpus_stats: UpanishadCorpusAuditStats,
    ) -> UpanishadTrainingAuditResult:
        """Audit one Upanishad training example using precomputed corpus stats."""

        issues: list[str] = []
        score = 100.0
        response = training_example.assistant_response
        word_count = len(response.split())
        opening_phrase = self.extract_opening_phrase(response)
        normalized_problem = self._normalize_text(training_example.user_problem)
        normalized_response = self._normalize_text(response)
        fingerprint = self.response_fingerprint(response)

        if word_count < 80:
            issues.append("response_too_short")
            score -= 20.0
        if word_count > 170:
            issues.append("response_too_long")
            score -= 15.0
        if FORBIDDEN_PATTERN.search(response):
            issues.append("scripture_metadata_leakage")
            score -= 40.0
        if CORRUPTION_PATTERN.search(response):
            issues.append("corrupted_characters")
            score -= 40.0
        if corpus_stats.response_counts[normalized_response] > 1:
            issues.append("duplicate_response")
            score -= 40.0
        elif fingerprint and corpus_stats.response_fingerprint_counts[fingerprint] > 1:
            issues.append("near_duplicate_response")
            score -= 20.0
        if corpus_stats.user_problem_counts[normalized_problem] > DUPLICATE_USER_PROBLEM_THRESHOLD:
            issues.append("duplicate_user_problem")
            score -= 12.0
        if corpus_stats.opening_counts[opening_phrase] > REPEATED_OPENING_THRESHOLD:
            issues.append("repeated_opening_phrase")
            score -= 18.0
        if not PRACTICAL_ACTION_PATTERN.search(response):
            issues.append("missing_practical_action")
            score -= 20.0
        if PREACHY_PATTERN.search(response):
            issues.append("preachy_tone")
            score -= 25.0
        if LISTICLE_PATTERN.search(response):
            issues.append("listicle_format")
            score -= 20.0
        if MEDICAL_CLAIM_PATTERN.search(response):
            issues.append("medical_or_therapy_claim")
            score -= 45.0
        if response.count("!") > 0:
            issues.append("tone_too_emphatic")
            score -= 8.0

        score = max(0.0, min(score, 100.0))
        status = self._determine_status(score, issues)
        return UpanishadTrainingAuditResult(
            training_example_id=training_example.id,
            dataset_quality_score=score,
            dataset_status=status,
            issues=issues,
            opening_phrase=opening_phrase,
        )

    def top_issue_counts(self, results: list[UpanishadTrainingAuditResult]) -> list[tuple[str, int]]:
        """Return aggregated issue counts for non-approved examples."""

        counter: Counter[str] = Counter()
        for result in results:
            if result.dataset_status != "approved":
                counter.update(result.issues)
        return counter.most_common()

    def extract_opening_phrase(self, response: str) -> str:
        """Return the normalized leading phrase of a response."""

        words = response.split()
        return " ".join(words[:OPENING_WORD_COUNT]).rstrip(".,;:!?").lower()

    def response_fingerprint(self, response: str) -> str:
        """Return a normalized response fingerprint."""

        normalized = self._normalize_text(response)
        return " ".join(normalized.split()[:45]) if normalized else ""

    def _determine_status(self, score: float, issues: list[str]) -> str:
        """Map score and issues to a dataset review status."""

        hard_reject = {
            "scripture_metadata_leakage",
            "corrupted_characters",
            "duplicate_response",
            "medical_or_therapy_claim",
        }
        if score < 60.0 or any(issue in hard_reject for issue in issues):
            return "rejected"
        if score >= 85.0 and not issues:
            return "approved"
        return "needs_review"

    def _normalize_text(self, text: str) -> str:
        """Normalize text for repetition checks."""

        lowered = text.lower()
        lowered = re.sub(r"[^a-z0-9\s]", " ", lowered)
        lowered = re.sub(r"\s+", " ", lowered).strip()
        return lowered
