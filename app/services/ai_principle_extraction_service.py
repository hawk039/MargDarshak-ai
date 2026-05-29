"""Optional AI-style principle extraction service with mock local mode only."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.config import get_settings
from app.models.wisdom_entry import WisdomEntry


EMOTIONAL_TAG_KEYWORDS = {
    "confusion": ("confusion", "confused", "doubt", "uncertain", "bewildered", "delusion"),
    "grief": ("grief", "sorrow", "sadness", "lament", "mourning", "loss"),
    "attachment": ("attachment", "attached", "clinging", "possessive", "outcome", "craving"),
    "fear": ("fear", "afraid", "dread", "terror", "panic", "anxious"),
    "duty": ("duty", "responsibility", "obligation", "righteous action", "calling"),
    "anger": ("anger", "angry", "rage", "wrath", "resentment"),
    "discipline": ("discipline", "practice", "restraint", "steadfast", "effort", "focus"),
    "devotion": ("devotion", "faith", "worship", "loving service", "prayer"),
    "self-control": ("self-control", "self control", "control the senses", "restraint", "mastery"),
    "ego": ("ego", "pride", "arrogance", "self-importance"),
    "desire": ("desire", "craving", "longing", "yearning", "lust"),
    "surrender": ("surrender", "submit", "offering", "trust completely"),
    "purpose": ("purpose", "meaning", "calling", "higher aim"),
}

PHILOSOPHICAL_TAG_KEYWORDS = {
    "karma": ("karma", "action", "actions", "fruit of action", "prescribed duty"),
    "dharma": ("dharma", "duty", "righteousness", "sacred duty"),
    "bhakti": ("bhakti", "devotion", "devotional", "worship", "surrender"),
    "jnana": ("jnana", "knowledge", "wisdom", "discernment", "understanding"),
    "yoga": ("yoga", "union", "discipline", "meditation", "spiritual practice"),
    "moksha": ("moksha", "liberation", "freedom", "release", "salvation"),
    "atman": ("atman", "self", "soul", "true self"),
    "guna": ("guna", "gunas", "qualities", "modes of nature"),
    "maya": ("maya", "illusion", "delusion", "appearance"),
    "renunciation": ("renunciation", "detachment", "letting go", "non-attachment"),
    "devotion": ("devotion", "faith", "worship", "loving surrender"),
    "self-realization": ("self-realization", "realize the self", "true self", "self knowledge"),
}

USE_CASE_MAP = {
    "confusion": "finding clarity in confusion",
    "grief": "processing grief",
    "attachment": "letting go of attachment",
    "fear": "facing fear",
    "duty": "making duty-based decisions",
    "anger": "managing anger",
    "discipline": "building discipline",
    "devotion": "deepening devotion",
    "self-control": "strengthening self-control",
    "ego": "softening ego-driven reactions",
    "desire": "working with desire wisely",
    "surrender": "practicing surrender",
    "purpose": "reconnecting with purpose",
}

GENERIC_PRINCIPLES = {
    "o krishna!",
    "o partha!",
    "o king!",
    "o sanjaya!",
    "o achyuta!",
    "o my teacher!",
}

SENTENCE_PATTERN = re.compile(r"(?<=[.!?])\s+")
CORRUPTION_PATTERN = re.compile(r"[{}@ïÌœ]|H¥|jkhh|vijkhh|iijkhh|viiijkhh|�")
NARRATION_START_PATTERN = re.compile(
    r"^(arjuna said|sanjaya said|krishna said|dhrutarashtra said|the lord said)\b",
    re.IGNORECASE,
)
VOCATIVE_START_PATTERN = re.compile(r"^(o [a-z-]+[!,]?\s+)", re.IGNORECASE)


@dataclass(slots=True)
class RefinedPrincipleResult:
    """In-memory result for refined principle extraction."""

    extracted_principle: str | None
    emotional_tags: list[str]
    philosophical_tags: list[str]
    use_cases: list[str]
    confidence_score: float


class AIPrincipleExtractionService:
    """Refine wisdom entry principles with mock deterministic logic."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def refine_entry(self, wisdom_entry: WisdomEntry) -> RefinedPrincipleResult:
        """Refine principle and tags for one wisdom entry."""

        if self.settings.ai_principle_mode != "mock":
            raise ValueError("Only mock AI principle mode is supported right now.")

        translation = self._clean_text(wisdom_entry.translation)
        commentary = self._clean_text(wisdom_entry.commentary)

        candidate_sentences = self._candidate_sentences(translation, commentary)
        selected_principle = self._select_principle(candidate_sentences)
        combined_text = " ".join(
            part for part in [selected_principle or "", translation or "", commentary or ""] if part
        )

        emotional_tags = self._detect_tags(combined_text, EMOTIONAL_TAG_KEYWORDS)
        philosophical_tags = self._detect_tags(combined_text, PHILOSOPHICAL_TAG_KEYWORDS)
        use_cases = self._build_use_cases(emotional_tags, philosophical_tags)
        confidence_score = self._build_confidence_score(
            selected_principle=selected_principle,
            emotional_tags=emotional_tags,
            philosophical_tags=philosophical_tags,
            commentary=commentary,
        )

        return RefinedPrincipleResult(
            extracted_principle=selected_principle,
            emotional_tags=emotional_tags,
            philosophical_tags=philosophical_tags,
            use_cases=use_cases,
            confidence_score=confidence_score,
        )

    def _candidate_sentences(self, translation: str | None, commentary: str | None) -> list[str]:
        """Build ordered candidate sentences from translation and commentary."""

        candidates: list[str] = []
        for text in (translation, commentary):
            if not text:
                continue
            for sentence in SENTENCE_PATTERN.split(text):
                cleaned_sentence = self._normalize_sentence(sentence)
                if cleaned_sentence and cleaned_sentence not in candidates:
                    candidates.append(cleaned_sentence)
        return candidates

    def _select_principle(self, candidate_sentences: list[str]) -> str | None:
        """Pick the first acceptable non-generic principle sentence."""

        for candidate in candidate_sentences:
            if self._reject_principle(candidate):
                continue
            return candidate
        return None

    def _reject_principle(self, principle: str) -> bool:
        """Return True when a principle candidate should be rejected."""

        normalized = principle.strip().lower()
        if len(normalized.split()) < 10:
            return True
        if normalized in GENERIC_PRINCIPLES:
            return True
        if NARRATION_START_PATTERN.match(normalized):
            return True
        if CORRUPTION_PATTERN.search(normalized):
            return True
        if normalized.endswith("said:") or normalized.endswith("said."):
            return True
        return False

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
        """Build simple use cases from detected tags."""

        use_cases: list[str] = []
        for tag in emotional_tags:
            mapped_use_case = USE_CASE_MAP.get(tag)
            if mapped_use_case and mapped_use_case not in use_cases:
                use_cases.append(mapped_use_case)

        if "karma" in philosophical_tags and "reflecting on action and consequences" not in use_cases:
            use_cases.append("reflecting on action and consequences")
        if "dharma" in philosophical_tags and "ethical decision-making" not in use_cases:
            use_cases.append("ethical decision-making")
        if "self-realization" in philosophical_tags and "deep self-inquiry" not in use_cases:
            use_cases.append("deep self-inquiry")

        if not use_cases:
            use_cases.append("self-reflection")
        return use_cases

    def _build_confidence_score(
        self,
        selected_principle: str | None,
        emotional_tags: list[str],
        philosophical_tags: list[str],
        commentary: str | None,
    ) -> float:
        """Return a deterministic confidence score for refined entries."""

        score = 60.0
        if selected_principle:
            score += 10.0
        if commentary:
            score += 5.0
        if emotional_tags:
            score += 7.5
        if philosophical_tags:
            score += 7.5
        return min(score, 95.0)

    def _clean_text(self, text: str | None) -> str | None:
        """Normalize whitespace and trim text."""

        if not text:
            return None
        cleaned_text = " ".join(text.split()).strip()
        return cleaned_text or None

    def _normalize_sentence(self, sentence: str) -> str | None:
        """Normalize a candidate sentence and remove leading vocatives."""

        cleaned_sentence = self._clean_text(sentence)
        if not cleaned_sentence:
            return None
        cleaned_sentence = VOCATIVE_START_PATTERN.sub("", cleaned_sentence).strip()
        return cleaned_sentence or None
