"""Services for ingesting source documents into the system."""

from pathlib import Path

import fitz

from app.core.config import get_settings
from app.utils.file_utils import build_uploaded_file_path


class InvalidDocumentTypeError(ValueError):
    """Raised when the uploaded file is not a supported PDF."""


class DocumentExtractionError(ValueError):
    """Raised when text extraction from a PDF fails."""


class DocumentIngestionService:
    """Handle local PDF storage and text extraction for source documents."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def validate_pdf_upload(self, filename: str | None, content_type: str | None) -> None:
        """Validate that the upload looks like a PDF file."""

        has_pdf_extension = bool(filename and filename.lower().endswith(".pdf"))
        is_pdf_content_type = content_type in {"application/pdf", "application/x-pdf"}
        if not has_pdf_extension and not is_pdf_content_type:
            raise InvalidDocumentTypeError("Only PDF files are supported for document ingestion.")

    def save_uploaded_pdf(self, file_bytes: bytes, original_filename: str) -> str:
        """Persist an uploaded PDF to local storage and return the saved path."""

        output_path = build_uploaded_file_path(
            self.settings.storage_source_documents_directory,
            original_filename,
        )
        output_path.write_bytes(file_bytes)
        return str(output_path)

    def extract_text_from_pdf(self, file_path: str) -> dict[str, str | int]:
        """Extract text and page count from a text-based PDF."""

        pdf_path = Path(file_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"Document not found at path: {file_path}")

        try:
            with fitz.open(pdf_path) as pdf_document:
                page_count = pdf_document.page_count
                page_text_segments = [page.get_text("text") for page in pdf_document]
        except RuntimeError as exc:
            raise DocumentExtractionError("Unable to read the uploaded PDF file.") from exc

        raw_text = "\n\n".join(segment.strip() for segment in page_text_segments if segment.strip())
        if not raw_text.strip():
            raise DocumentExtractionError(
                "No extractable text found in the PDF. Only text-based PDFs are supported right now."
            )

        # TODO: Add OCR support for scanned PDFs and image-based scriptures.
        return {
            "raw_text": raw_text,
            "page_count": page_count,
            "extraction_status": "processed",
        }
