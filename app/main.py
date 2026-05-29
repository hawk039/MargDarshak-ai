"""FastAPI entrypoint for the Marg Darshak AI service."""

from fastapi import FastAPI

from app.core.config import get_settings
from app.routers.document_chunk_router import document_chunk_router
from app.routers.health_router import health_router
from app.routers.source_document_router import source_document_router
from app.routers.training_dataset_router import training_dataset_router
from app.routers.wisdom_entry_router import wisdom_entry_router

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
    version="0.1.0",
    description=(
        "Standalone AI and knowledge service for ingesting philosophical documents, "
        "storing wisdom entries, and managing future fine-tuning datasets."
    ),
)

app.include_router(health_router)
app.include_router(source_document_router)
app.include_router(document_chunk_router)
app.include_router(wisdom_entry_router)
app.include_router(training_dataset_router)
