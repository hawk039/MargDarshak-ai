"""Quality rules for filtering Upanishad pilot canonical passages."""

from __future__ import annotations

import re


TITLE_ONLY_PATTERN = re.compile(
    r"^(kena|katha|mundaka)(\s+upanishad)?$|^section\s+[ivx0-9]+$|^part\s+[ivx0-9]+$|^khanda\s+[ivx0-9]+$",
    re.IGNORECASE,
)
SPEAKER_ONLY_PATTERN = re.compile(
    r"^(death|nachiketas|teacher|student|disciple|indra|agni|vayu|brahma|the teacher|the pupil)\s+said:?\s*$",
    re.IGNORECASE,
)
FOOTNOTE_PATTERN = re.compile(
    r"(translator'?s note|published by|cf\.|see also|sbe|vol\.|footnote)",
    re.IGNORECASE,
)
BIBLIOGRAPHY_PATTERN = re.compile(
    r"(bibliography|index|table of contents|compiled by|copyright|printed by)",
    re.IGNORECASE,
)
RITUAL_METADATA_PATTERN = re.compile(
    r"^(om ! peace ! peace ! peace !|here ends the .+upanishad.*)$",
    re.IGNORECASE,
)
CORRUPTION_PATTERN = re.compile(r"[{}@ïÌœ]|H¥|�|Translaetd")
ALPHA_WORD_PATTERN = re.compile(r"[A-Za-z][A-Za-z'-]+")


class UpanishadQualityService:
    """Apply deterministic validity checks to Upanishad pilot passages."""

    def is_valid_passage(
        self,
        english_translation: str,
        commentary_text: str | None = None,
    ) -> bool:
        """Return whether the passage is suitable for downstream wisdom extraction."""

        text = " ".join(part for part in [english_translation, commentary_text or ""] if part).strip()
        if not text:
            return False
        if len(text) < 60:
            return False
        if TITLE_ONLY_PATTERN.fullmatch(text):
            return False
        if SPEAKER_ONLY_PATTERN.fullmatch(text):
            return False
        if FOOTNOTE_PATTERN.search(text):
            return False
        if BIBLIOGRAPHY_PATTERN.search(text):
            return False
        if RITUAL_METADATA_PATTERN.fullmatch(text):
            return False
        if CORRUPTION_PATTERN.search(text):
            return False
        if len(ALPHA_WORD_PATTERN.findall(text)) < 10:
            return False
        if not self._has_usable_teaching_content(text):
            return False
        return True

    def _has_usable_teaching_content(self, text: str) -> bool:
        """Return True when text looks like a teachable philosophical passage."""

        lowered = text.lower()
        useful_markers = (
            "self",
            "brahman",
            "know",
            "wisdom",
            "immortal",
            "mind",
            "truth",
            "desire",
            "death",
            "teach",
            "knowledge",
            "wise",
            "realize",
            "attain",
        )
        return any(marker in lowered for marker in useful_markers)
