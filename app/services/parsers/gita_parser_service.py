"""Gita-specific parser for canonical verse extraction."""

from __future__ import annotations

import re
from dataclasses import dataclass


VERSE_PATTERN = re.compile(r"\((1?\d?\.\d+)\)")
CHAPTER_HEADING_PATTERN = re.compile(r"^Chapter\s+(\d{1,2})\b", re.IGNORECASE)
ANNEXURE_PATTERN = re.compile(r"^Annexure\s+\d+\b", re.IGNORECASE)
END_OF_CHAPTER_PATTERN = re.compile(r"^End of Chapter\s+(\d{1,2})\b", re.IGNORECASE)
PAGE_REFERENCE_PATTERN = re.compile(r"\b(?:Chapter\s+\d+\s+)?(\d{1,3})\b")
SPEAKER_LINE_PATTERN = re.compile(
    r"^(Dhrutarashtra|Arjuna|Sanjaya|Krishna)\s+said:\s*(.*)$",
    re.IGNORECASE | re.DOTALL,
)
STANDALONE_SPEAKER_PATTERN = re.compile(
    r"^(O King!?|Arjuna said:?|Sanjaya said:?|Krishna said:?)$",
    re.IGNORECASE,
)
CORRUPTION_PATTERN = re.compile(r"[{}@ïÌœ]|H¥|jkhh|vijkhh|iijkhh|viiijkhh")
HEADER_FOOTER_PATTERN = re.compile(
    r"^(The Bhagavad Gita|Chapter\s+\d+\s+\d+|Introduction\s+\d+|\d+\s+The Bhagavad Gita)\b",
    re.IGNORECASE,
)
PAGE_ARTIFACT_PATTERN = re.compile(r"^\d{1,3}\s*$")
HASH_SUFFIX_PATTERN = re.compile(r"\b[a-f0-9]{12,}\b", re.IGNORECASE)
MULTISPACE_PATTERN = re.compile(r"\s+")


@dataclass(slots=True)
class ParsedCanonicalVerse:
    """In-memory representation of a parsed canonical verse."""

    chapter_number: int
    verse_number: str
    speaker: str | None
    sanskrit_text: str | None
    transliteration: str | None
    english_translation: str
    commentary: str | None
    page_reference: str | None
    is_valid: bool


class GitaParserService:
    """Convert extracted Bhagavad Gita text into clean verse-level records."""

    def clean_source_title(self, title: str) -> str:
        """Remove trailing hash-like IDs from a source document title."""

        cleaned_title = HASH_SUFFIX_PATTERN.sub("", title).replace("_", " ").strip()
        cleaned_title = MULTISPACE_PATTERN.sub(" ", cleaned_title)
        return cleaned_title or title

    def parse_canonical_verses(self, raw_text: str) -> list[ParsedCanonicalVerse]:
        """Parse extracted raw text into canonical verse records."""

        blocks = self._split_into_blocks(raw_text)
        start_index = self._find_start_index(blocks)
        end_index = self._find_end_index(blocks, start_index)
        active_blocks = blocks[start_index:end_index]

        verses: list[ParsedCanonicalVerse] = []
        for index, block in enumerate(active_blocks):
            verse_match = VERSE_PATTERN.search(block)
            if verse_match is None:
                continue
            if not self._is_translation_block(block, verse_match.group(1)):
                continue

            verse_number = verse_match.group(1)
            chapter_number = int(verse_number.split(".", maxsplit=1)[0])
            if chapter_number < 1 or chapter_number > 18:
                continue

            english_translation = self._clean_translation_block(block)
            if not english_translation or STANDALONE_SPEAKER_PATTERN.match(english_translation):
                continue

            speaker, english_translation = self._extract_speaker(english_translation)
            sanskrit_text, transliteration = self._extract_preceding_verse_text(active_blocks, index)
            commentary = self._extract_commentary(active_blocks, index)
            page_reference = self._extract_page_reference(active_blocks, index)
            is_valid = self._is_valid_record(
                english_translation=english_translation,
                commentary=commentary,
            )

            verses.append(
                ParsedCanonicalVerse(
                    chapter_number=chapter_number,
                    verse_number=verse_number,
                    speaker=speaker,
                    sanskrit_text=sanskrit_text,
                    transliteration=transliteration,
                    english_translation=english_translation,
                    commentary=commentary,
                    page_reference=page_reference,
                    is_valid=is_valid,
                )
            )

        return verses

    def _split_into_blocks(self, raw_text: str) -> list[str]:
        """Split text into paragraph-like blocks for deterministic parsing."""

        normalized_text = raw_text.replace("\r\n", "\n").replace("\r", "\n").strip()
        raw_blocks = re.split(r"\n\s*\n+", normalized_text)
        blocks: list[str] = []
        for raw_block in raw_blocks:
            normalized_block = "\n".join(line.rstrip() for line in raw_block.splitlines()).strip()
            if normalized_block:
                blocks.append(normalized_block)
        return blocks

    def _find_start_index(self, blocks: list[str]) -> int:
        """Return the first block index that contains verse (1.1)."""

        for index, block in enumerate(blocks):
            if "(1.1)" in block:
                return max(0, index - 2)
        return 0

    def _find_end_index(self, blocks: list[str], start_index: int) -> int:
        """Return the block index where annexures begin after chapter 18."""

        seen_chapter_18 = False
        for index in range(start_index, len(blocks)):
            block = blocks[index]
            verse_match = VERSE_PATTERN.search(block)
            if verse_match and verse_match.group(1).startswith("18."):
                seen_chapter_18 = True
            if seen_chapter_18 and ANNEXURE_PATTERN.match(block):
                return index
        return len(blocks)

    def _clean_translation_block(self, block: str) -> str:
        """Normalize a verse translation block and preserve the verse marker."""

        cleaned_lines = []
        for line in block.splitlines():
            cleaned_line = self._normalize_line(line)
            if not cleaned_line or self._is_header_footer(cleaned_line):
                continue
            cleaned_lines.append(cleaned_line)
        return " ".join(cleaned_lines).strip()

    def _extract_speaker(self, translation: str) -> tuple[str | None, str]:
        """Return a speaker name and translation text stripped of speaker prefixes."""

        match = SPEAKER_LINE_PATTERN.match(translation)
        if match is None:
            return None, translation.strip()

        speaker = match.group(1).strip().title()
        remainder = match.group(2).strip()
        return speaker, remainder

    def _extract_preceding_verse_text(
        self,
        blocks: list[str],
        verse_index: int,
    ) -> tuple[str | None, str | None]:
        """Return cleaned Sanskrit/transliteration text from the block before a verse."""

        candidate_block = blocks[verse_index - 1] if verse_index > 0 else ""
        if not candidate_block or self._is_header_footer(candidate_block):
            return None, None
        if VERSE_PATTERN.search(candidate_block) or candidate_block.startswith("Comments:"):
            return None, None
        if STANDALONE_SPEAKER_PATTERN.match(candidate_block.strip()):
            return None, None
        if self._contains_corruption(candidate_block):
            return None, None

        cleaned_candidate = "\n".join(
            line for line in (self._normalize_line(line) for line in candidate_block.splitlines()) if line
        ).strip()
        if not cleaned_candidate:
            return None, None

        if self._looks_like_transliteration(cleaned_candidate):
            return None, cleaned_candidate
        return cleaned_candidate, None

    def _extract_commentary(self, blocks: list[str], verse_index: int) -> str | None:
        """Return commentary paragraphs following the verse translation."""

        commentary_blocks: list[str] = []
        for next_index in range(verse_index + 1, len(blocks)):
            next_block = blocks[next_index].strip()
            if not next_block:
                break
            if ANNEXURE_PATTERN.match(next_block):
                break
            if END_OF_CHAPTER_PATTERN.match(next_block):
                break
            if CHAPTER_HEADING_PATTERN.match(next_block) and not next_block.lower().startswith("chapter introduction"):
                break
            if self._is_section_heading(next_block):
                break
            if VERSE_PATTERN.search(next_block):
                break
            if self._is_header_footer(next_block) or PAGE_ARTIFACT_PATTERN.match(next_block):
                continue
            if self._contains_corruption(next_block):
                continue

            normalized_block = " ".join(
                line for line in (self._normalize_line(line) for line in next_block.splitlines()) if line
            ).strip()
            if not normalized_block:
                continue
            if normalized_block.startswith("Comments:"):
                normalized_block = normalized_block.replace("Comments:", "", 1).strip()
            commentary_blocks.append(normalized_block)

        return "\n\n".join(commentary_blocks).strip() or None

    def _extract_page_reference(self, blocks: list[str], verse_index: int) -> str | None:
        """Return a page reference from nearby header/footer blocks."""

        for offset in (-2, -1, 1, 2):
            neighbor_index = verse_index + offset
            if not 0 <= neighbor_index < len(blocks):
                continue
            neighbor_block = blocks[neighbor_index].strip()
            match = re.search(r"\b(\d{1,3})\b", neighbor_block)
            if match and (
                HEADER_FOOTER_PATTERN.search(neighbor_block)
                or CHAPTER_HEADING_PATTERN.search(neighbor_block)
                or "The Bhagavad Gita" in neighbor_block
            ):
                return f"page {match.group(1)}"
        return None

    def _looks_like_transliteration(self, text: str) -> bool:
        """Return True when a block resembles transliteration more than translation."""

        lowered_text = text.lower()
        return any(token in lowered_text for token in ("ā", "ī", "ū", "ṛ", "ś", "ṣ", "ṁ", "ḥ"))

    def _is_translation_block(self, block: str, verse_number: str) -> bool:
        """Return True when a block looks like a verse translation rather than commentary."""

        normalized_block = " ".join(self._normalize_line(line) for line in block.splitlines()).strip()
        if normalized_block.startswith("Comments:"):
            return False
        if len(VERSE_PATTERN.findall(normalized_block)) != 1:
            return False
        return normalized_block.endswith(f"({verse_number})")

    def _is_valid_record(self, english_translation: str, commentary: str | None) -> bool:
        """Return True when a parsed record looks clean enough for downstream use."""

        if len(english_translation) < 20:
            return False
        if self._contains_corruption(english_translation):
            return False
        if commentary and self._contains_corruption(commentary):
            return False
        if self._contains_page_or_header_artifacts(english_translation):
            return False
        return True

    def _contains_corruption(self, text: str) -> bool:
        """Return True when text contains obvious encoding corruption."""

        return bool(CORRUPTION_PATTERN.search(text))

    def _contains_page_or_header_artifacts(self, text: str) -> bool:
        """Return True when text still contains page/header residue."""

        return bool(HEADER_FOOTER_PATTERN.search(text) or PAGE_ARTIFACT_PATTERN.match(text.strip()))

    def _is_header_footer(self, text: str) -> bool:
        """Return True when a block is a header, footer, or page artifact."""

        stripped_text = text.strip()
        if not stripped_text:
            return True
        if HEADER_FOOTER_PATTERN.search(stripped_text):
            return True
        if PAGE_ARTIFACT_PATTERN.match(stripped_text):
            return True
        if ANNEXURE_PATTERN.match(stripped_text):
            return True
        return False

    def _is_section_heading(self, text: str) -> bool:
        """Return True when a block looks like a short section heading before a verse."""

        normalized = " ".join(self._normalize_line(line) for line in text.splitlines()).strip()
        if not normalized or len(normalized.split()) > 8:
            return False
        if normalized.endswith((".", "?", "!", ":")):
            return False
        if VERSE_PATTERN.search(normalized):
            return False
        capitalized_words = sum(1 for word in normalized.split() if word[:1].isupper())
        return capitalized_words >= max(1, len(normalized.split()) - 1)

    def _normalize_line(self, line: str) -> str:
        """Normalize a single line while preserving readable punctuation."""

        return MULTISPACE_PATTERN.sub(" ", line.replace("\t", " ")).strip()
