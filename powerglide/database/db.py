"""SQLite connection manager with migration support."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from powerglide.core.config import settings

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or settings.db_path
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def transaction(conn: sqlite3.Connection) -> Generator[sqlite3.Cursor, None, None]:
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def get_schema_version(conn: sqlite3.Connection) -> int:
    try:
        row = conn.execute(
            "SELECT MAX(version) FROM schema_version"
        ).fetchone()
        return row[0] if row and row[0] is not None else 0
    except sqlite3.OperationalError:
        return 0


def init_db(conn: sqlite3.Connection | None = None) -> sqlite3.Connection:
    """Run all unapplied migrations in order."""
    if conn is None:
        conn = get_connection()

    current = get_schema_version(conn)

    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    for mig_file in migration_files:
        version = int(mig_file.stem.split("_")[0])
        if version > current:
            sql = mig_file.read_text(encoding="utf-8")
            conn.executescript(sql)

    return conn
