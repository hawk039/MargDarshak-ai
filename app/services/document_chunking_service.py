"""Rule-based parsing service for splitting extracted text into structured chunks."""

from __future__ import annotations

import re
from dataclasses import dataclass


CHAPTER_PATTERN = re.compile(r"^(chapter\s+(?:\d+|[ivxlcdm]+)\b.*)$", re.IGNORECASE)
VERSE_PATTERN = re.compile(r"\((\d+(?:\.\d+)+)\)")
PAGE_PATTERN = re.compile(r"\bpage\s+(\d+)\b", re.IGNORECASE)
SUMMARY_PATTERN = re.compile(r"^(summary|in summary|overall)\b", re.IGNORECASE)


@dataclass(slots=True)
class ParsedDocumentChunk:
    """In-memory representation of a parsed document chunk."""

    chunk_index: int
    chapter: str | None
    section_title: str | None
    verse_number: str | None
    content: str
    content_type: str
    page_reference: str | None


class DocumentChunkingService:
    """Convert extracted raw text into simple, debuggable structured chunks."""

    def parse_raw_text(self, raw_text: str) -> list[ParsedDocumentChunk]:
        """Split raw extracted text into chunk records using rule-based parsing."""

        blocks = self._split_into_blocks(raw_text)
        parsed_chunks: list[ParsedDocumentChunk] = []
        buffer: ParsedDocumentChunk | None = None
        current_chapter: str | None = None
        current_section_title: str | None = None
        current_verse_number: str | None = None
        next_chunk_index = 1

        for block in blocks:
            if self._is_chapter_title(block):
                buffer = self._flush_buffer(buffer, parsed_chunks)
                current_chapter = block
                current_section_title = None
                current_verse_number = None
                parsed_chunks.append(
                    ParsedDocumentChunk(
                        chunk_index=next_chunk_index,
                        chapter=current_chapter,
                        section_title=None,
                        verse_number=None,
                        content=block,
                        content_type="chapter_title",
                        page_reference=self._extract_page_reference(block),
                    )
                )
                next_chunk_index += 1
                continue

            if self._is_section_title(block):
                buffer = self._flush_buffer(buffer, parsed_chunks)
                current_section_title = block
                current_verse_number = None
                continue

            verse_number = self._extract_verse_number(block)
            if verse_number is not None:
                buffer = self._flush_buffer(buffer, parsed_chunks)
                current_verse_number = verse_number
                parsed_chunks.append(
                    ParsedDocumentChunk(
                        chunk_index=next_chunk_index,
                        chapter=current_chapter,
                        section_title=current_section_title,
                        verse_number=verse_number,
                        content=block,
                        content_type="verse",
                        page_reference=self._extract_page_reference(block),
                    )
                )
                next_chunk_index += 1
                continue

            content_type = self._classify_non_verse_block(block, current_verse_number)
            page_reference = self._extract_page_reference(block)

            if buffer and self._can_merge_blocks(
                existing_chunk=buffer,
                chapter=current_chapter,
                section_title=current_section_title,
                verse_number=current_verse_number,
                content_type=content_type,
                page_reference=page_reference,
            ):
                buffer.content = f"{buffer.content}\n\n{block}"
                continue

            buffer = self._flush_buffer(buffer, parsed_chunks)
            buffer = ParsedDocumentChunk(
                chunk_index=next_chunk_index,
                chapter=current_chapter,
                section_title=current_section_title,
                verse_number=current_verse_number if content_type != "unknown" else None,
                content=block,
                content_type=content_type,
                page_reference=page_reference,
            )
            next_chunk_index += 1

        self._flush_buffer(buffer, parsed_chunks)
        # TODO: Add book-specific parsers for scriptures with consistent layout conventions.
        return parsed_chunks

    def _split_into_blocks(self, raw_text: str) -> list[str]:
        """Preserve paragraph boundaries while cleaning each block for parsing."""

        normalized_text = raw_text.replace("\r\n", "\n").replace("\r", "\n").strip()
        if not normalized_text:
            return []

        raw_blocks = re.split(r"\n\s*\n+", normalized_text)
        blocks: list[str] = []
        for raw_block in raw_blocks:
            normalized_block = self._normalize_block(raw_block)
            if normalized_block:
                blocks.append(normalized_block)
        return blocks

    def _normalize_block(self, block: str) -> str:
        """Collapse line-level whitespace without removing paragraph structure."""

        return " ".join(line.strip() for line in block.splitlines() if line.strip()).strip()

    def _is_chapter_title(self, block: str) -> bool:
        """Return True when the block looks like a chapter heading."""

        return bool(CHAPTER_PATTERN.match(block)) and len(block.split()) <= 12

    def _is_section_title(self, block: str) -> bool:
        """Return True when the block looks like a non-chapter section heading."""

        if self._is_chapter_title(block) or self._extract_verse_number(block):
            return False
        if len(block.split()) > 12:
            return False
        if block.endswith((".", "!", "?", ";", ":")):
            return False

        words = block.split()
        title_case_words = sum(1 for word in words if word[:1].isupper())
        return bool(words) and title_case_words >= max(1, len(words) - 1)

    def _extract_verse_number(self, block: str) -> str | None:
        """Extract verse references such as (2.47) from a text block."""

        match = VERSE_PATTERN.search(block)
        if match is None:
            return None
        return match.group(1)

    def _extract_page_reference(self, block: str) -> str | None:
        """Extract an explicit page reference when one appears in the text."""

        match = PAGE_PATTERN.search(block)
        if match is None:
            return None
        return f"page {match.group(1)}"

    def _classify_non_verse_block(self, block: str, current_verse_number: str | None) -> str:
        """Classify a non-verse block into a simple content type."""

        if SUMMARY_PATTERN.match(block):
            return "summary"
        if current_verse_number is not None:
            return "commentary"
        return "unknown"

    def _can_merge_blocks(
        self,
        existing_chunk: ParsedDocumentChunk,
        chapter: str | None,
        section_title: str | None,
        verse_number: str | None,
        content_type: str,
        page_reference: str | None,
    ) -> bool:
        """Return True when a new block should be appended to the current buffered chunk."""

        return (
            existing_chunk.chapter == chapter
            and existing_chunk.section_title == section_title
            and existing_chunk.verse_number == verse_number
            and existing_chunk.content_type == content_type
            and existing_chunk.page_reference == page_reference
        )

    def _flush_buffer(
        self,
        buffer: ParsedDocumentChunk | None,
        parsed_chunks: list[ParsedDocumentChunk],
    ) -> ParsedDocumentChunk | None:
        """Persist the buffered chunk into the parsed result list."""

        if buffer is not None:
            parsed_chunks.append(buffer)
        return None
