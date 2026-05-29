"""Database engine, session management, and ORM base definitions."""

from collections.abc import AsyncGenerator
from datetime import datetime

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.config import get_settings


NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


metadata = MetaData(naming_convention=NAMING_CONVENTION)
settings = get_settings()
engine = create_async_engine(settings.database_url, echo=settings.app_debug, future=True)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    metadata = metadata

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session for request handlers."""

    async with AsyncSessionLocal() as session:
        yield session
