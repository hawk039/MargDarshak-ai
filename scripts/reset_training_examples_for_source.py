"""Delete training examples for one source document and reclaim SQLite space."""

from __future__ import annotations

import argparse
import asyncio
import sqlite3
import sys
from pathlib import Path

from sqlalchemy import delete, func, select

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.models.training_example import TrainingExample
from app.models.wisdom_entry import WisdomEntry


def _resolve_sqlite_path() -> Path:
    """Return the local SQLite database path."""

    database_url = get_settings().database_url
    prefix = "sqlite+aiosqlite:///"
    if not database_url.startswith(prefix):
        raise ValueError("VACUUM helper currently supports only sqlite+aiosqlite URLs.")
    raw_path = database_url.removeprefix(prefix)
    return (PROJECT_ROOT / raw_path).resolve() if raw_path.startswith("./") else Path(raw_path).resolve()


def _format_size(num_bytes: int) -> str:
    """Return a compact human-readable byte size."""

    units = ["B", "KB", "MB", "GB"]
    size = float(num_bytes)
    for unit in units:
        if size < 1024.0 or unit == units[-1]:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{num_bytes} B"


async def reset_training_examples_for_source(source_document_id: int) -> None:
    """Delete training examples for one source document and vacuum the SQLite file."""

    db_path = _resolve_sqlite_path()
    size_before = db_path.stat().st_size if db_path.exists() else 0

    async with AsyncSessionLocal() as db:
        id_result = await db.execute(
            select(TrainingExample.id)
            .join(WisdomEntry, TrainingExample.wisdom_entry_id == WisdomEntry.id)
            .where(WisdomEntry.source_document_id == source_document_id)
        )
        training_example_ids = list(id_result.scalars().all())

        count_result = await db.execute(
            select(func.count())
            .select_from(TrainingExample)
            .join(WisdomEntry, TrainingExample.wisdom_entry_id == WisdomEntry.id)
            .where(WisdomEntry.source_document_id == source_document_id)
        )
        deleted_count = count_result.scalar_one()

        if training_example_ids:
            await db.execute(delete(TrainingExample).where(TrainingExample.id.in_(training_example_ids)))
            await db.commit()
        else:
            await db.rollback()

    sqlite_connection = sqlite3.connect(db_path)
    try:
        sqlite_connection.execute("VACUUM")
    finally:
        sqlite_connection.close()

    size_after = db_path.stat().st_size if db_path.exists() else 0
    print(f"source_document_id={source_document_id}")
    print(f"deleted_training_examples={deleted_count}")
    print("related_audit_rows=none_separate")
    print(f"db_size_before={_format_size(size_before)}")
    print(f"db_size_after={_format_size(size_after)}")


def parse_args() -> argparse.Namespace:
    """Parse CLI args."""

    parser = argparse.ArgumentParser(description="Reset training examples for one source document.")
    parser.add_argument("--source-document-id", type=int, required=True)
    return parser.parse_args()


def main() -> None:
    """CLI entrypoint."""

    args = parse_args()
    asyncio.run(reset_training_examples_for_source(source_document_id=args.source_document_id))


if __name__ == "__main__":
    main()
