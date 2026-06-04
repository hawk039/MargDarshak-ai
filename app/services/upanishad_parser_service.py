"""Services for extracting pilot Upanishad canonical passages from PDF sources."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import fitz

from app.models.source_document import SourceDocument
from app.services.upanishad_quality_service import UpanishadQualityService


PILOT_UPANISHAD_SPECS = {
    "Kena": {
        "title_text": "kena upanishad",
        "commentary_text": "kena upanishad commentary",
    },
    "Katha": {
        "title_text": "katha upanishad",
        "commentary_text": "katha upanishad commentary",
    },
    "Mundaka": {
        "title_text": "mundaka upanishad",
        "commentary_text": "mundaka upanishad commentary",
    },
}

PASSAGE_START_PATTERN = re.compile(
    r"^(?P<marker>(?:[IVX]+|[0-9]+)(?:-[IVXivx0-9]+){1,2})[.:]\s*(?P<content>.*)$"
)
SPEAKER_INLINE_PATTERN = re.compile(r"^\((?P<speaker>[^)]+)\)\s*(?P<content>.*)$")
STANDALONE_SPEAKER_PATTERN = re.compile(
    r"^(death|nachiketas|teacher|student|disciple|indra|agni|vayu)\s+said:?\s*$",
    re.IGNORECASE,
)
IGNORE_LINE_PATTERN = re.compile(
    r"^(translated by|published by|commentary on|here ends the|om ! peace ! peace ! peace !|108 upanishads|compiled by)",
    re.IGNORECASE,
)
FOOTNOTE_OR_EDITOR_PATTERN = re.compile(
    r"(translator'?s note|cf\.|vol\.|published by|commentary on|here ends the)",
    re.IGNORECASE,
)


@dataclass(slots=True)
class ParsedCanonicalPassage:
    """In-memory representation of a parsed Upanishad canonical passage."""

    source_document_id: int
    upanishad_name: str
    chapter: str | None
    section: str | None
    passage_number: str
    speaker: str | None
    original_text: str | None
    english_translation: str
    commentary_text: str | None
    page_reference: str
    is_valid: bool


class UpanishadParserService:
    """Extract pilot canonical passages for Kena, Katha, and Mundaka."""

    def __init__(self) -> None:
        self.quality_service = UpanishadQualityService()

    def parse_document(self, source_document: SourceDocument) -> list[ParsedCanonicalPassage]:
        """Extract pilot Upanishad canonical passages from the source PDF."""

        pdf_path = Path(source_document.file_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"Document not found at path: {pdf_path}")

        with fitz.open(pdf_path) as pdf_document:
            page_texts = [
                (index + 1, pdf_document.load_page(index).get_text("text"))
                for index in range(pdf_document.page_count)
            ]

        passages: list[ParsedCanonicalPassage] = []
        for upanishad_name, spec in PILOT_UPANISHAD_SPECS.items():
            translation_pages = self._collect_translation_pages(page_texts, spec)
            passages.extend(
                self._parse_upanishad_pages(
                    source_document_id=source_document.id,
                    upanishad_name=upanishad_name,
                    page_segments=translation_pages,
                )
            )

        return passages

    def _collect_translation_pages(
        self,
        page_texts: list[tuple[int, str]],
        spec: dict[str, str],
    ) -> list[tuple[int, str]]:
        """Return only the translation pages for one pilot Upanishad."""

        collected: list[tuple[int, str]] = []
        is_collecting = False
        for page_number, page_text in page_texts:
            first_line = self._first_content_line(page_text).lower()
            if not is_collecting and first_line == spec["title_text"]:
                is_collecting = True

            if not is_collecting:
                continue

            if spec["commentary_text"] in page_text.lower():
                break

            collected.append((page_number, page_text))
        return collected

    def _parse_upanishad_pages(
        self,
        source_document_id: int,
        upanishad_name: str,
        page_segments: list[tuple[int, str]],
    ) -> list[ParsedCanonicalPassage]:
        """Parse translation pages for a single Upanishad into canonical passages."""

        parsed_passages: list[ParsedCanonicalPassage] = []
        current_marker: str | None = None
        current_lines: list[str] = []
        current_page_reference: str | None = None
        current_speaker: str | None = None
        started_passages = False

        for page_number, page_text in page_segments:
            for raw_line in page_text.splitlines():
                line = self._normalize_line(raw_line)
                if not line:
                    continue
                if IGNORE_LINE_PATTERN.match(line):
                    continue
                if FOOTNOTE_OR_EDITOR_PATTERN.search(line):
                    continue
                if STANDALONE_SPEAKER_PATTERN.fullmatch(line):
                    continue
                if line.isdigit():
                    continue

                marker_match = PASSAGE_START_PATTERN.match(line)
                if marker_match:
                    started_passages = True
                    if current_marker and current_lines and current_page_reference:
                        parsed_passages.append(
                            self._build_passage(
                                source_document_id=source_document_id,
                                upanishad_name=upanishad_name,
                                marker=current_marker,
                                page_reference=current_page_reference,
                                lines=current_lines,
                                speaker=current_speaker,
                            )
                        )
                    current_marker = marker_match.group("marker")
                    current_lines = [marker_match.group("content").strip()]
                    current_page_reference = f"p. {page_number}"
                    current_speaker = None
                    continue

                if not started_passages or current_marker is None:
                    continue

                if line.lower().startswith("here ends the"):
                    break

                speaker_match = SPEAKER_INLINE_PATTERN.match(line)
                if speaker_match:
                    current_speaker = self._normalize_speaker(speaker_match.group("speaker"))
                    if speaker_match.group("content").strip():
                        current_lines.append(speaker_match.group("content").strip())
                    continue

                current_lines.append(line)

        if current_marker and current_lines and current_page_reference:
            parsed_passages.append(
                self._build_passage(
                    source_document_id=source_document_id,
                    upanishad_name=upanishad_name,
                    marker=current_marker,
                    page_reference=current_page_reference,
                    lines=current_lines,
                    speaker=current_speaker,
                )
            )

        return parsed_passages

    def _build_passage(
        self,
        source_document_id: int,
        upanishad_name: str,
        marker: str,
        page_reference: str,
        lines: list[str],
        speaker: str | None,
    ) -> ParsedCanonicalPassage:
        """Build one parsed canonical passage."""

        english_translation = self._clean_joined_text(lines)
        chapter, section = self._derive_structure(upanishad_name, marker)
        is_valid = self.quality_service.is_valid_passage(english_translation=english_translation)
        return ParsedCanonicalPassage(
            source_document_id=source_document_id,
            upanishad_name=upanishad_name,
            chapter=chapter,
            section=section,
            passage_number=marker,
            speaker=speaker,
            original_text=None,
            english_translation=english_translation,
            commentary_text=None,
            page_reference=page_reference,
            is_valid=is_valid,
        )

    def _derive_structure(self, upanishad_name: str, marker: str) -> tuple[str | None, str | None]:
        """Derive chapter and section labels from a pilot marker."""

        parts = marker.split("-")
        if upanishad_name == "Kena" and len(parts) == 2:
            chapter = parts[0]
            return chapter, f"Section {parts[0]}"
        if upanishad_name == "Katha" and len(parts) == 3:
            chapter = parts[0]
            return chapter, f"Part {parts[1]}"
        if upanishad_name == "Mundaka" and len(parts) == 3:
            chapter = parts[0]
            return chapter, f"Khanda {parts[1]}"
        return None, None

    def _normalize_speaker(self, speaker: str) -> str | None:
        """Return a normalized speaker label."""

        normalized = speaker.strip().strip(":")
        if not normalized:
            return None
        lowered = normalized.lower()
        if "nachiketas" in lowered:
            return "Nachiketas"
        if "death" in lowered or "yama" in lowered:
            return "Death"
        if "teacher" in lowered:
            return "teacher"
        if "disciple" in lowered or "student" in lowered:
            return "student"
        return normalized

    def _normalize_line(self, line: str) -> str:
        """Normalize one extracted PDF line."""

        normalized = " ".join(line.split()).strip()
        return normalized

    def _first_content_line(self, page_text: str) -> str:
        """Return the first non-empty line for page-level heading detection."""

        for line in page_text.splitlines():
            normalized = self._normalize_line(line)
            if normalized:
                return normalized
        return ""

    def _clean_joined_text(self, lines: list[str]) -> str:
        """Join lines into readable passage text."""

        text = " ".join(line.strip() for line in lines if line.strip())
        text = re.sub(r"\s+", " ", text)
        return text.strip()
