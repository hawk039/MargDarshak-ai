"""Run the full local development pipeline for one PDF file."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import AsyncSessionLocal
from app.models.extracted_document_text import ExtractedDocumentText
from app.models.source_document import SourceDocument
from app.pipelines.chunk_document_pipeline import ChunkDocumentPipeline
from app.pipelines.extract_wisdom_pipeline import ExtractWisdomPipeline
from app.pipelines.generate_training_dataset_pipeline import GenerateTrainingDatasetPipeline
from app.pipelines.generate_training_examples_pipeline import GenerateTrainingExamplesPipeline
from app.services.document_ingestion_service import DocumentIngestionService
from app.utils.file_utils import ensure_directory


EXPORT_PATH = PROJECT_ROOT / "storage" / "exports" / "marg_darshak_training_v1.jsonl"


def parse_args() -> argparse.Namespace:
    """Parse command line arguments for the full pipeline runner."""

    parser = argparse.ArgumentParser(
        description="Run the full Marg Darshak pipeline for one local PDF file."
    )
    parser.add_argument("pdf_path", help="Path to a local PDF file.")
    parser.add_argument(
        "--title",
        default=None,
        help="Optional source document title. Defaults to the PDF filename stem.",
    )
    parser.add_argument("--tradition", default="Indian wisdom traditions")
    parser.add_argument("--document-type", default="scripture")
    parser.add_argument("--language", default="English")
    parser.add_argument("--author-or-translator", default=None)
    parser.add_argument("--source-name", default="local-dev-pipeline")
    return parser.parse_args()


async def run_pipeline(args: argparse.Namespace) -> None:
    """Run ingestion, chunking, wisdom extraction, training generation, and export."""

    pdf_path = Path(args.pdf_path).expanduser().resolve()
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError("The provided file must be a PDF.")

    title = args.title or pdf_path.stem.replace("_", " ").replace("-", " ").strip().title()
    ingestion_service = DocumentIngestionService()
    chunk_pipeline = ChunkDocumentPipeline()
    wisdom_pipeline = ExtractWisdomPipeline()
    training_pipeline = GenerateTrainingExamplesPipeline()
    dataset_pipeline = GenerateTrainingDatasetPipeline()

    async with AsyncSessionLocal() as db:
        file_bytes = pdf_path.read_bytes()
        if not file_bytes:
            raise ValueError("The provided PDF file is empty.")

        ingestion_service.validate_pdf_upload(pdf_path.name, "application/pdf")
        saved_file_path = ingestion_service.save_uploaded_pdf(file_bytes, pdf_path.name)
        extracted_payload = ingestion_service.extract_text_from_pdf(saved_file_path)

        source_document = SourceDocument(
            title=title,
            tradition=args.tradition,
            document_type=args.document_type,
            language=args.language,
            author_or_translator=args.author_or_translator,
            source_name=args.source_name,
            file_path=saved_file_path,
            status="processed",
        )
        db.add(source_document)
        await db.flush()
        print(f"document created: id={source_document.id} title={source_document.title}")

        extracted_text = ExtractedDocumentText(
            source_document_id=source_document.id,
            raw_text=str(extracted_payload["raw_text"]),
            page_count=int(extracted_payload["page_count"]),
            extraction_status=str(extracted_payload["extraction_status"]),
        )
        db.add(extracted_text)
        await db.commit()
        await db.refresh(source_document)
        await db.refresh(extracted_text)
        print(
            "text extracted: "
            f"source_document_id={source_document.id} page_count={extracted_text.page_count}"
        )

        document_chunks = await chunk_pipeline.run(
            source_document=source_document,
            extracted_text=extracted_text,
            db=db,
        )
        print(
            "chunks generated: "
            f"source_document_id={source_document.id} total_chunks={len(document_chunks)}"
        )

        wisdom_entries = await wisdom_pipeline.run(
            source_document=source_document,
            document_chunks=document_chunks,
            db=db,
        )
        print(
            "wisdom entries generated: "
            f"source_document_id={source_document.id} total_entries={len(wisdom_entries)}"
        )

        training_examples = await training_pipeline.run(wisdom_entries=wisdom_entries, db=db)
        print(
            "training examples generated: "
            f"source_document_id={source_document.id} total_examples={len(training_examples)}"
        )

        jsonl_lines = dataset_pipeline.run(training_examples)
        ensure_directory(str(EXPORT_PATH.parent))
        EXPORT_PATH.write_text("\n".join(jsonl_lines), encoding="utf-8")
        print(f"JSONL exported: path={EXPORT_PATH} lines={len(jsonl_lines)}")


def main() -> None:
    """Entrypoint for the local pipeline runner."""

    args = parse_args()
    asyncio.run(run_pipeline(args))


if __name__ == "__main__":
    main()
