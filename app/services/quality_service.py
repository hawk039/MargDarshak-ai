"""Services for validating generated wisdom entries and training examples."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.models.quality_review import QualityReview
from app.models.training_example import TrainingExample
from app.models.wisdom_entry import WisdomEntry


MIN_ENTRY_TEXT_LENGTH = 20
MIN_PRINCIPLE_WORDS = 10
MAX_REPEATED_RESPONSE_COUNT = 6

SPEAKER_PREFIXES = (
    "o king",
    "arjuna said",
    "sanjaya said",
    "krishna said",
)
CORRUPTION_PATTERNS = (
    re.compile(r"�"),
    re.compile(r"\b[jkvx]{3,}hh\b", re.IGNORECASE),
    re.compile(r"[A-Za-z]{0,2}[{}|~`^]{1,}"),
)
PAGE_ARTIFACT_PATTERNS = (
    re.compile(r"\bpage\s+\d+\b", re.IGNORECASE),
    re.compile(r"^\s*\d+\s+(the bhagavad gita|chapter)\b", re.IGNORECASE),
    re.compile(r"\b\d{1,3}\s*$"),
)
HEADER_FOOTER_PATTERNS = (
    re.compile(r"\bthe bhagavad gita\b", re.IGNORECASE),
    re.compile(r"\bchapter\s+\d+\s+\d+\b", re.IGNORECASE),
    re.compile(r"\bcontents\b", re.IGNORECASE),
)
RAW_OCR_PATTERNS = (
    re.compile(r"\b[i1l]{3,}[a-z]{2,}\b", re.IGNORECASE),
    re.compile(r"[A-Za-z0-9]{20,}"),
)
METADATA_PATTERNS = (
    re.compile(r"\bchapter\s+\d+\b", re.IGNORECASE),
    re.compile(r"\bpage\s+\d+\b", re.IGNORECASE),
    re.compile(r"\b\d+\.\d+\b"),
)


@dataclass(slots=True)
class QualityReviewResult:
    """In-memory quality review result before persistence."""

    wisdom_entry_id: int
    quality_score: int
    validation_status: str
    issues: list[str]


class QualityService:
    """Apply deterministic quality validation to generated content."""

    def review_source_document(
        self,
        wisdom_entries: list[WisdomEntry],
        training_examples: list[TrainingExample],
    ) -> list[QualityReviewResult]:
        """Return quality reviews for wisdom entries in a source document."""

        training_examples_by_entry: dict[int, list[TrainingExample]] = {}
        for training_example in training_examples:
            training_examples_by_entry.setdefault(training_example.wisdom_entry_id, []).append(
                training_example
            )

        repeated_response_counts: dict[str, int] = {}
        for training_example in training_examples:
            repeated_response_counts[training_example.assistant_response] = (
                repeated_response_counts.get(training_example.assistant_response, 0) + 1
            )

        return [
            self.review_wisdom_entry(
                wisdom_entry=wisdom_entry,
                training_examples=training_examples_by_entry.get(wisdom_entry.id, []),
                repeated_response_counts=repeated_response_counts,
            )
            for wisdom_entry in wisdom_entries
        ]

    def review_wisdom_entry(
        self,
        wisdom_entry: WisdomEntry,
        training_examples: list[TrainingExample],
        repeated_response_counts: dict[str, int],
    ) -> QualityReviewResult:
        """Return a quality review for one wisdom entry and its training examples."""

        issues: list[str] = []
        score = 100

        entry_text = " ".join(
            value
            for value in [
                wisdom_entry.original_text,
                wisdom_entry.translation,
                wisdom_entry.commentary,
            ]
            if value
        ).strip()
        principle_text = (wisdom_entry.extracted_principle or "").strip()

        if self._contains_encoding_corruption(entry_text):
            issues.append("entry_contains_encoding_corruption")
            score -= 40
        if len(entry_text) < MIN_ENTRY_TEXT_LENGTH:
            issues.append("entry_text_too_short")
            score -= 30
        if self._contains_page_number_artifacts(entry_text):
            issues.append("entry_contains_page_number_artifacts")
            score -= 20
        if self._contains_header_footer_artifacts(entry_text):
            issues.append("entry_contains_header_footer_artifacts")
            score -= 20

        if self._principle_too_short(principle_text):
            issues.append("principle_too_short")
            score -= 35
        if self._principle_is_speaker_text(principle_text):
            issues.append("principle_is_only_speaker_text")
            score -= 40
        if self._principle_starts_with_speaker_text(principle_text):
            issues.append("principle_starts_with_speaker_text")
            score -= 40

        for training_example in training_examples:
            response_issues = self._validate_training_example(
                training_example,
                repeated_response_counts,
            )
            for response_issue in response_issues:
                if response_issue not in issues:
                    issues.append(response_issue)

        if "training_response_repeated_too_many_times" in issues:
            score -= 25
        if "training_response_contains_corruption" in issues:
            score -= 35
        if "training_response_contains_raw_ocr_output" in issues:
            score -= 30
        if "training_response_contains_metadata_artifacts" in issues:
            score -= 25

        score = max(0, min(score, 100))
        validation_status = "approved" if score >= 80 and not self._has_rejecting_issue(issues) else "rejected"
        return QualityReviewResult(
            wisdom_entry_id=wisdom_entry.id,
            quality_score=score,
            validation_status=validation_status,
            issues=issues,
        )

    def _validate_training_example(
        self,
        training_example: TrainingExample,
        repeated_response_counts: dict[str, int],
    ) -> list[str]:
        """Return quality issues detected in a training example response."""

        issues: list[str] = []
        assistant_response = training_example.assistant_response
        if repeated_response_counts.get(assistant_response, 0) > MAX_REPEATED_RESPONSE_COUNT:
            issues.append("training_response_repeated_too_many_times")
        if self._contains_encoding_corruption(assistant_response):
            issues.append("training_response_contains_corruption")
        if self._contains_raw_ocr_output(assistant_response):
            issues.append("training_response_contains_raw_ocr_output")
        if self._contains_metadata_artifacts(assistant_response):
            issues.append("training_response_contains_metadata_artifacts")
        return issues

    def _principle_too_short(self, principle_text: str) -> bool:
        """Return True when the extracted principle is too short."""

        return len(principle_text.split()) < MIN_PRINCIPLE_WORDS

    def _principle_is_speaker_text(self, principle_text: str) -> bool:
        """Return True when the principle contains only speaker text."""

        normalized = principle_text.strip().lower().rstrip(":.")
        return normalized in SPEAKER_PREFIXES

    def _principle_starts_with_speaker_text(self, principle_text: str) -> bool:
        """Return True when the principle begins with a speaker-text prefix."""

        normalized = principle_text.strip().lower()
        return any(normalized.startswith(prefix) for prefix in SPEAKER_PREFIXES)

    def _contains_encoding_corruption(self, text: str) -> bool:
        """Return True when text appears to contain encoding corruption."""

        if not text:
            return False
        return any(pattern.search(text) for pattern in CORRUPTION_PATTERNS)

    def _contains_page_number_artifacts(self, text: str) -> bool:
        """Return True when text contains page numbering artifacts."""

        if not text:
            return False
        return any(pattern.search(text) for pattern in PAGE_ARTIFACT_PATTERNS)

    def _contains_header_footer_artifacts(self, text: str) -> bool:
        """Return True when text contains chapter header/footer residue."""

        if not text:
            return False
        return any(pattern.search(text) for pattern in HEADER_FOOTER_PATTERNS)

    def _contains_raw_ocr_output(self, text: str) -> bool:
        """Return True when text still looks like uncleaned OCR output."""

        if not text:
            return False
        return any(pattern.search(text) for pattern in RAW_OCR_PATTERNS)

    def _contains_metadata_artifacts(self, text: str) -> bool:
        """Return True when a response contains chapter or page metadata."""

        if not text:
            return False
        return any(pattern.search(text) for pattern in METADATA_PATTERNS)

    def _has_rejecting_issue(self, issues: list[str]) -> bool:
        """Return True when the issue list includes a hard rejection condition."""

        return any(
            issue
            in {
                "entry_contains_encoding_corruption",
                "entry_text_too_short",
                "entry_contains_page_number_artifacts",
                "entry_contains_header_footer_artifacts",
                "principle_too_short",
                "principle_is_only_speaker_text",
                "principle_starts_with_speaker_text",
                "training_response_contains_corruption",
                "training_response_contains_raw_ocr_output",
                "training_response_contains_metadata_artifacts",
            }
            for issue in issues
        )
