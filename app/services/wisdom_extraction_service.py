"""Services for converting canonical verses into structured wisdom entries."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.models.canonical_verse import CanonicalVerse
from app.models.source_document import SourceDocument


EMOTIONAL_TAG_KEYWORDS = {
    "anxiety": ("anxiety", "anxious", "worry", "worried", "restless"),
    "grief": ("grief", "sorrow", "sadness", "lament", "mourning"),
    "fear": ("fear", "afraid", "terror", "panic", "dread"),
    "duty": ("duty", "responsibility", "obligation", "calling"),
    "attachment": ("attachment", "attached", "clinging", "possessive"),
    "anger": ("anger", "angry", "rage", "wrath", "resentment"),
    "confusion": ("confusion", "confused", "doubt", "bewildered", "delusion"),
    "discipline": ("discipline", "practice", "restraint", "steadfast", "focus"),
    "devotion": ("devotion", "surrender", "faith", "worship", "loving service"),
    "self-control": ("self-control", "self control", "control the senses", "mastery"),
}

PHILOSOPHICAL_TAG_KEYWORDS = {
    "karma": ("karma", "action", "actions", "fruit of action"),
    "dharma": ("dharma", "duty", "righteousness", "sacred duty"),
    "atman": ("atman", "self", "soul", "true self"),
    "bhakti": ("bhakti", "devotion", "devotional", "surrender"),
    "jnana": ("jnana", "knowledge", "wisdom", "discernment"),
    "yoga": ("yoga", "union", "discipline", "meditation"),
    "moksha": ("moksha", "liberation", "freedom", "release"),
    "maya": ("maya", "illusion", "delusion", "appearance"),
    "guna": ("guna", "gunas", "qualities", "modes of nature"),
    "renunciation": ("renunciation", "detachment", "letting go", "non-attachment"),
}

USE_CASE_MAP = {
    "anxiety": "coping with anxiety",
    "grief": "processing grief",
    "fear": "facing fear",
    "duty": "making duty-based decisions",
    "attachment": "letting go of attachment",
    "anger": "managing anger",
    "confusion": "finding clarity in confusion",
    "discipline": "building discipline",
    "devotion": "deepening devotion",
    "self-control": "strengthening self-control",
}

SENTENCE_PATTERN = re.compile(r"(?<=[.!?])\s+")
CORRUPTION_PATTERN = re.compile(r"[{}@ïÌœ]|H¥|jkhh|vijkhh|iijkhh|viiijkhh|�")
SPEAKER_START_PATTERN = re.compile(
    r"^(o king|o partha|arjuna said|sanjaya said|krishna said)\b",
    re.IGNORECASE,
)


@dataclass(slots=True)
class ExtractedWisdomEntry:
    """In-memory representation of a wisdom entry generated from canonical verses."""

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


class WisdomExtractionService:
    """Deterministically convert canonical verses into wisdom entries."""

    def extract_entries(
        self,
        source_document: SourceDocument,
        canonical_verses: list[CanonicalVerse],
    ) -> list[ExtractedWisdomEntry]:
        """Return rule-based wisdom entries derived from canonical verses."""

        extracted_entries: list[ExtractedWisdomEntry] = []

        for canonical_verse in canonical_verses:
            if not self._is_usable_canonical_verse(canonical_verse):
                continue

            original_text = self._clean_text(canonical_verse.sanskrit_text) or ""
            translation = self._clean_text(canonical_verse.english_translation)
            commentary = self._clean_text(canonical_verse.commentary)
            extracted_principle = self._extract_principle(translation=translation, commentary=commentary)

            combined_text = " ".join(
                value for value in [translation or "", commentary or "", extracted_principle or ""] if value
            )
            emotional_tags = self._detect_tags(combined_text, EMOTIONAL_TAG_KEYWORDS)
            philosophical_tags = self._detect_tags(combined_text, PHILOSOPHICAL_TAG_KEYWORDS)
            use_cases = self._build_use_cases(emotional_tags, philosophical_tags)

            extracted_entries.append(
                ExtractedWisdomEntry(
                    source_document_id=canonical_verse.source_document_id,
                    book_title=source_document.title,
                    chapter=str(canonical_verse.chapter_number),
                    section=canonical_verse.speaker,
                    verse_number=canonical_verse.verse_number,
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

        # TODO: Replace deterministic heuristics with LLM-based principle and tag extraction.
        return extracted_entries

    def _is_usable_canonical_verse(self, canonical_verse: CanonicalVerse) -> bool:
        """Return True when a canonical verse is fit for wisdom extraction."""

        if not canonical_verse.is_valid:
            return False

        translation = self._clean_text(canonical_verse.english_translation)
        if not translation or len(translation) < 30:
            return False
        if SPEAKER_START_PATTERN.match(translation):
            return False
        if self._contains_corruption(translation):
            return False
        if canonical_verse.commentary and self._contains_corruption(canonical_verse.commentary):
            return False
        return True

    def _extract_principle(self, translation: str | None, commentary: str | None) -> str | None:
        """Build a placeholder principle from the first clean sentence available."""

        for candidate in (translation, commentary):
            sentence = self._first_sentence(candidate)
            if sentence:
                return sentence
        return None

    def _first_sentence(self, text: str | None) -> str | None:
        """Return the first clean summary sentence from a block of text."""

        cleaned_text = self._clean_text(text)
        if not cleaned_text:
            return None

        sentences = SENTENCE_PATTERN.split(cleaned_text)
        first_sentence = sentences[0].strip()
        return first_sentence if first_sentence else None

    def _detect_tags(
        self,
        text: str,
        keyword_map: dict[str, tuple[str, ...]],
    ) -> list[str]:
        """Return deterministic tags based on simple keyword matching."""

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

        if "dharma" in philosophical_tags and "ethical decision-making" not in use_cases:
            use_cases.append("ethical decision-making")
        if "karma" in philosophical_tags and "reflecting on action and consequences" not in use_cases:
            use_cases.append("reflecting on action and consequences")
        if "yoga" in philosophical_tags and "developing a spiritual practice" not in use_cases:
            use_cases.append("developing a spiritual practice")

        if not use_cases:
            use_cases.append("self-reflection")
        return use_cases

    def _clean_text(self, text: str | None) -> str | None:
        """Normalize whitespace while preserving readable content."""

        if not text:
            return None
        cleaned_text = " ".join(text.split()).strip()
        return cleaned_text or None

    def _contains_corruption(self, text: str) -> bool:
        """Return True when text contains obvious encoding corruption."""

        return bool(CORRUPTION_PATTERN.search(text))
