"""Services for preparing raw text before downstream processing."""

from app.utils.text_utils import normalize_whitespace


class TextCleaningService:
    """Clean and normalize raw text extracted from source files."""

    def clean_text(self, raw_text: str) -> str:
        """Return a normalized version of the input text."""

        return normalize_whitespace(raw_text)
