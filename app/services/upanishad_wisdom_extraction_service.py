"""Services for converting canonical Upanishad passages into structured wisdom entries."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.models.canonical_passage import CanonicalPassage


EMOTIONAL_TAG_KEYWORDS = {
    "confusion": ("confusion", "confused", "doubt", "unknown", "bewildered"),
    "fear": ("fear", "afraid", "terror", "death", "perish"),
    "grief": ("grief", "sorrow", "lament", "mourning", "moans"),
    "desire": ("desire", "desires", "covet", "craving", "pleasant"),
    "discipline": ("discipline", "austerity", "practice", "concentration", "continence"),
    "self-control": ("self-control", "self restraint", "restrain", "senses", "collected"),
    "restlessness": ("restless", "wandering", "ramble", "agitated", "unsettled"),
    "ego": ("pride", "ego", "glory", "ours alone", "self-importance"),
    "purpose": ("purpose", "goal", "seek", "seeking", "desirable"),
    "detachment": ("detachment", "renouncing", "renunciation", "desireless", "without attachment"),
    "trust": ("trust", "faith", "rely", "teacher", "reveals"),
    "inner_steadiness": ("steady", "steadiness", "tranquility", "calm", "composed"),
}

PHILOSOPHICAL_TAG_KEYWORDS = {
    "atman": ("self", "atman", "soul", "inner self"),
    "brahman": ("brahman", "imperishable", "purusha"),
    "self_knowledge": ("know", "knowledge", "realize", "wisdom"),
    "non_duality": ("one", "all this is brahman", "non-dual", "unity"),
    "liberation": ("liberation", "freed", "freedom", "moksha"),
    "consciousness": ("consciousness", "mind", "intelligence", "awareness"),
    "meditation": ("meditation", "concentration", "contemplate", "om"),
    "renunciation": ("renunciation", "renounce", "desireless", "withdrawn"),
    "teacher_student": ("teacher", "disciple", "asked", "said", "instruct"),
    "death": ("death", "yama", "mortal", "immortal"),
    "immortality": ("immortal", "immortality", "eternal", "undecaying"),
    "reality": ("truth", "real", "reality", "imperishable"),
}

USE_CASE_MAP = {
    "confusion": "finding clarity in confusion",
    "fear": "facing fear",
    "grief": "processing grief and loss",
    "desire": "working with desire and craving",
    "discipline": "building spiritual discipline",
    "self-control": "strengthening self-control",
    "restlessness": "calming mental restlessness",
    "ego": "loosening ego-driven reactions",
    "purpose": "searching for purpose",
    "detachment": "letting go of attachment",
    "trust": "learning to trust the process",
    "inner_steadiness": "finding inner steadiness",
}

SENTENCE_PATTERN = re.compile(r"(?<=[.!?])\s+")
CORRUPTION_PATTERN = re.compile(r"[{}@ïÌœ]|H¥|�")
SUSPICIOUS_PRINCIPLE_PATTERN = re.compile(
    r"^(om\b|here ends\b|translated by\b|published by\b)",
    re.IGNORECASE,
)


@dataclass(slots=True)
class ExtractedUpanishadWisdomEntry:
    """In-memory representation of a wisdom entry generated from canonical passages."""

    source_document_id: int
    book_title: str | None
    chapter: str | None
    section: str | None
    verse_number: str | None
    original_text: str
    translation: str | None
    commentary: str | None
    extracted_principle: str | None
    emotional_tags: list[str]
    philosophical_tags: list[str]
    use_cases: list[str]
    confidence_score: float


class UpanishadWisdomExtractionService:
    """Deterministically convert canonical Upanishad passages into wisdom entries."""

    def extract_entries(
        self,
        canonical_passages: list[CanonicalPassage],
    ) -> list[ExtractedUpanishadWisdomEntry]:
        """Return rule-based wisdom entries derived from valid canonical passages."""

        extracted_entries: list[ExtractedUpanishadWisdomEntry] = []

        for canonical_passage in canonical_passages:
            if not canonical_passage.is_valid:
                continue

            original_text = self._clean_text(canonical_passage.original_text) or ""
            translation = self._clean_text(canonical_passage.english_translation)
            commentary = self._clean_text(canonical_passage.commentary_text)
            extracted_principle = self._extract_principle(translation)

            combined_text = " ".join(
                value for value in [translation or "", commentary or "", extracted_principle or ""] if value
            )
            emotional_tags = self._detect_tags(combined_text, EMOTIONAL_TAG_KEYWORDS)
            philosophical_tags = self._detect_tags(combined_text, PHILOSOPHICAL_TAG_KEYWORDS)
            use_cases = self._build_use_cases(emotional_tags, philosophical_tags)

            extracted_entries.append(
                ExtractedUpanishadWisdomEntry(
                    source_document_id=canonical_passage.source_document_id,
                    book_title=canonical_passage.upanishad_name,
                    chapter=canonical_passage.chapter,
                    section=canonical_passage.section,
                    verse_number=canonical_passage.passage_number,
                    original_text=original_text,
                    translation=translation,
                    commentary=commentary,
                    extracted_principle=extracted_principle,
                    emotional_tags=emotional_tags,
                    philosophical_tags=philosophical_tags,
                    use_cases=use_cases,
                    confidence_score=70.0,
                )
            )

        return extracted_entries

    def _extract_principle(self, translation: str | None) -> str | None:
        """Build a first-pass principle from the first clean sentence."""

        cleaned_text = self._clean_text(translation)
        if not cleaned_text:
            return None

        for sentence in SENTENCE_PATTERN.split(cleaned_text):
            candidate = sentence.strip()
            if not candidate:
                continue
            if CORRUPTION_PATTERN.search(candidate):
                continue
            if SUSPICIOUS_PRINCIPLE_PATTERN.match(candidate):
                continue
            return candidate
        return None

    def _detect_tags(
        self,
        text: str,
        keyword_map: dict[str, tuple[str, ...]],
    ) -> list[str]:
        """Return deterministic tags based on keyword matching."""

        lowered_text = text.lower()
        return [
            tag
            for tag, keywords in keyword_map.items()
            if any(keyword in lowered_text for keyword in keywords)
        ]

    def _build_use_cases(
        self,
        emotional_tags: list[str],
        philosophical_tags: list[str],
    ) -> list[str]:
        """Return simple use cases derived from detected tags."""

        use_cases: list[str] = []
        for tag in emotional_tags:
            mapped_use_case = USE_CASE_MAP.get(tag)
            if mapped_use_case and mapped_use_case not in use_cases:
                use_cases.append(mapped_use_case)

        if "atman" in philosophical_tags and "identity and self-inquiry" not in use_cases:
            use_cases.append("identity and self-inquiry")
        if "death" in philosophical_tags and "working with mortality and fear" not in use_cases:
            use_cases.append("working with mortality and fear")
        if "meditation" in philosophical_tags and "deepening contemplative practice" not in use_cases:
            use_cases.append("deepening contemplative practice")
        if "reality" in philosophical_tags and "seeing beyond appearances" not in use_cases:
            use_cases.append("seeing beyond appearances")

        if not use_cases:
            use_cases.append("self-reflection")
        return use_cases

    def _clean_text(self, text: str | None) -> str | None:
        """Normalize whitespace while preserving readable content."""

        if not text:
            return None
        cleaned_text = " ".join(text.split()).strip()
        return cleaned_text or None
