"""Utility helpers for file system operations."""

from pathlib import Path
from uuid import uuid4


def ensure_directory(directory_path: str) -> Path:
    """Create a directory if it does not already exist and return it."""

    path = Path(directory_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def build_uploaded_file_path(directory_path: str, original_filename: str) -> Path:
    """Build a unique local path for an uploaded source document."""

    safe_stem = Path(original_filename).stem.strip().replace(" ", "_").lower() or "document"
    safe_suffix = Path(original_filename).suffix.lower() or ".pdf"
    unique_filename = f"{safe_stem}_{uuid4().hex}{safe_suffix}"
    return ensure_directory(directory_path) / unique_filename
