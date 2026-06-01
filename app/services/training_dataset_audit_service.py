"""Services for auditing training examples before fine-tuning export."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

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
SCRIPTURE_LEAKAGE_PATTERN = re.compile(
    r"\b(the central lesson is|my bow|gandeeva|arjuna|krishna said|sanjaya)\b",
    re.IGNORECASE,
)

OPENING_WORD_COUNT = 12
REPEATED_OPENING_THRESHOLD = 5
NEAR_DUPLICATE_FINGERPRINT_THRESHOLD = 2
REPEATED_SENTENCE_THRESHOLD = 15
MIN_SENTENCE_WORDS = 6


@dataclass(slots=True)
class CorpusAuditStats:
    """Corpus-level signals used during per-row audit writes."""

    opening_counts: Counter[str]
    normalized_response_counts: Counter[str]
    response_fingerprint_counts: Counter[str]
    repeated_sentence_counts: Counter[str]


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

    def build_corpus_stats(
        self,
        training_examples: list[TrainingExample],
    ) -> CorpusAuditStats:
        """Build corpus-level repetition signals for a batch of examples."""

        rows = [(training_example.id, training_example.assistant_response) for training_example in training_examples]
        return self.build_corpus_stats_from_rows(rows)

    def build_corpus_stats_from_rows(
        self,
        rows: list[tuple[int, str]],
    ) -> CorpusAuditStats:
        """Build corpus-level repetition signals from lightweight rows."""

        opening_counts: Counter[str] = Counter()
        normalized_response_counts: Counter[str] = Counter()
        response_fingerprint_counts: Counter[str] = Counter()
        repeated_sentence_counts: Counter[str] = Counter()

        for _, assistant_response in rows:
            opening_phrase = self.extract_opening_phrase(assistant_response)
            normalized_response = self._normalize_text(assistant_response)
            response_fingerprint = self.response_fingerprint(assistant_response)

            opening_counts[opening_phrase] += 1
            normalized_response_counts[normalized_response] += 1
            if response_fingerprint:
                response_fingerprint_counts[response_fingerprint] += 1

            for sentence_pattern in self.extract_sentence_patterns(assistant_response):
                repeated_sentence_counts[sentence_pattern] += 1

        return CorpusAuditStats(
            opening_counts=opening_counts,
            normalized_response_counts=normalized_response_counts,
            response_fingerprint_counts=response_fingerprint_counts,
            repeated_sentence_counts=repeated_sentence_counts,
        )

    def audit_examples(
        self,
        training_examples: list[TrainingExample],
    ) -> list[TrainingDatasetAuditResult]:
        """Return dataset audit results for a batch of training examples."""

        corpus_stats = self.build_corpus_stats(training_examples)

        results: list[TrainingDatasetAuditResult] = []
        for training_example in training_examples:
            results.append(
                self.audit_example_with_corpus(
                    training_example_id=training_example.id,
                    assistant_response=training_example.assistant_response,
                    corpus_stats=corpus_stats,
                )
            )

        return results

    def audit_example_with_corpus(
        self,
        training_example_id: int,
        assistant_response: str,
        corpus_stats: CorpusAuditStats,
    ) -> TrainingDatasetAuditResult:
        """Audit one response using precomputed corpus-level repetition signals."""

        opening_phrase = self.extract_opening_phrase(assistant_response)
        normalized_response = self._normalize_text(assistant_response)
        response_fingerprint = self.response_fingerprint(assistant_response)
        sentence_patterns = self.extract_sentence_patterns(assistant_response)

        issues: list[str] = []
        score = 100.0
        word_count = len(assistant_response.split())

        if corpus_stats.opening_counts[opening_phrase] > REPEATED_OPENING_THRESHOLD:
            issues.append("repeated_opening_phrase")
            score -= 18.0

        if corpus_stats.normalized_response_counts[normalized_response] > 1:
            issues.append("duplicate_response")
            score -= 35.0
        elif response_fingerprint and corpus_stats.response_fingerprint_counts[response_fingerprint] > NEAR_DUPLICATE_FINGERPRINT_THRESHOLD:
            issues.append("near_duplicate_response")
            score -= 18.0

        if any(
            corpus_stats.repeated_sentence_counts[sentence_pattern] > REPEATED_SENTENCE_THRESHOLD
            for sentence_pattern in sentence_patterns
        ):
            issues.append("repeated_sentence_pattern")
            score -= 15.0

        if CORRUPTION_PATTERN.search(assistant_response):
            issues.append("corrupted_characters")
            score -= 40.0
        if SOURCE_METADATA_PATTERN.search(assistant_response):
            issues.append("source_metadata_leakage")
            score -= 30.0
        if word_count < 60:
            issues.append("response_too_short")
            score -= 20.0
        if word_count > 180:
            issues.append("response_too_long")
            score -= 15.0
        if UNSAFE_MENTAL_HEALTH_PATTERN.search(assistant_response):
            issues.append("unsafe_mental_health_advice")
            score -= 45.0
        if PREACHY_PATTERN.search(assistant_response):
            issues.append("overly_preachy_tone")
            score -= 25.0
        if SCRIPTURE_LEAKAGE_PATTERN.search(assistant_response):
            issues.append("scripture_narration_leakage")
            score -= 40.0
        if not PRACTICAL_ACTION_PATTERN.search(assistant_response):
            issues.append("missing_practical_action")
            score -= 20.0

        score = max(0.0, min(score, 100.0))
        return TrainingDatasetAuditResult(
            training_example_id=training_example_id,
            dataset_quality_score=score,
            dataset_status=self._determine_status(score, issues),
            issues=issues,
            opening_phrase=opening_phrase,
        )

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

    def response_fingerprint(self, response: str) -> str:
        """Return a coarse fingerprint from the first 40 normalized words."""

        normalized_response = self._normalize_text(response)
        if not normalized_response:
            return ""
        return " ".join(normalized_response.split()[:40])

    def extract_sentence_patterns(self, response: str) -> list[str]:
        """Return normalized sentence patterns suitable for corpus repetition checks."""

        patterns: list[str] = []
        for raw_sentence in re.split(r"(?<=[.!?])\s+", response):
            normalized_sentence = self._normalize_text(raw_sentence)
            if not normalized_sentence:
                continue
            if len(normalized_sentence.split()) < MIN_SENTENCE_WORDS:
                continue
            patterns.append(normalized_sentence)
        return patterns

    def _determine_status(self, score: float, issues: list[str]) -> str:
        """Map a dataset audit score to a review status."""

        hard_reject_issues = {
            "duplicate_response",
            "corrupted_characters",
            "unsafe_mental_health_advice",
            "scripture_narration_leakage",
        }
        if score < 60.0 or any(issue in hard_reject_issues for issue in issues):
            return "rejected"
        if score >= 85.0 and not any(
            issue
            in {
                "repeated_opening_phrase",
                "near_duplicate_response",
                "repeated_sentence_pattern",
                "source_metadata_leakage",
            }
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
