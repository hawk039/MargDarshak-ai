"""Utility helpers for reusable text transformations."""


def normalize_whitespace(text: str) -> str:
    """Collapse repeated whitespace and trim the final result."""

    return " ".join(text.split())
