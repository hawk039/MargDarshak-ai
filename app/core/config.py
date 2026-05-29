"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings for local and production-like environments."""

    app_name: str = "Marg Darshak AI Service"
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    database_url: str = Field(
        default="sqlite+aiosqlite:///./marg_darshak_ai_service.db",
        description="Async SQLAlchemy database URL.",
    )
    storage_source_documents_directory: str = "storage/source_documents"
    export_directory: str = "exports"
    ai_principle_mode: str = "mock"

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""

    return Settings()
