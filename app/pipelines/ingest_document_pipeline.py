"""Pipeline that orchestrates PDF ingestion and text persistence."""

from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.extracted_document_text import ExtractedDocumentText
from app.models.source_document import SourceDocument
from app.schemas.source_document_schema import SourceDocumentCreate
from app.services.document_ingestion_service import DocumentIngestionService


class IngestDocumentPipeline:
    """Coordinate upload validation, storage, extraction, and persistence."""

    def __init__(self, ingestion_service: DocumentIngestionService | None = None) -> None:
        self.ingestion_service = ingestion_service or DocumentIngestionService()

    async def run(
        self,
        upload_file: UploadFile,
        payload: SourceDocumentCreate,
        db: AsyncSession,
    ) -> tuple[SourceDocument, ExtractedDocumentText]:
        """Persist an uploaded PDF and its extracted raw text."""

        self.ingestion_service.validate_pdf_upload(upload_file.filename, upload_file.content_type)
        file_bytes = await upload_file.read()
        if not file_bytes:
            raise ValueError("The uploaded PDF file is empty.")

        saved_file_path = self.ingestion_service.save_uploaded_pdf(
            file_bytes=file_bytes,
            original_filename=upload_file.filename or "document.pdf",
        )

        try:
            extracted_payload = self.ingestion_service.extract_text_from_pdf(saved_file_path)

            source_document = SourceDocument(
                **payload.model_dump(exclude={"file_path", "status"}),
                file_path=saved_file_path,
                status="processed",
            )
            db.add(source_document)
            await db.flush()

            extracted_document_text = ExtractedDocumentText(
                source_document_id=source_document.id,
                raw_text=str(extracted_payload["raw_text"]),
                page_count=int(extracted_payload["page_count"]),
                extraction_status=str(extracted_payload["extraction_status"]),
            )
            db.add(extracted_document_text)
            await db.commit()
            await db.refresh(source_document)
            await db.refresh(extracted_document_text)
            return source_document, extracted_document_text
        except Exception:
            Path(saved_file_path).unlink(missing_ok=True)
            raise
