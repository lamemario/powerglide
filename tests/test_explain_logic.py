"""Unit tests for the transparency logic (fatigue breakdown, etc.)."""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

from powerglide.database.queries_analytics import (
    get_fatigue_breakdown_by_muscle,
)
from powerglide.database.queries_gym import (
    get_gym_session_by_id,
)

# In-memory DB with same schema as production.
MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "powerglide" / "database" / "migrations"


def _get_migration_sql() -> str:
    mig = MIGRATIONS_DIR / "001_initial.sql"
    return mig.read_text(encoding="utf-8")


@pytest.fixture
def conn() -> sqlite3.Connection:
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    c.executescript(_get_migration_sql())
    return c


def test_get_gym_session_by_id(conn: sqlite3.Connection) -> None:
    conn.execute(
        "INSERT INTO gym_sessions (id, session_date, duration_minutes, session_rpe) "
        "VALUES (10, '2026-02-21', 45, 8)"
    )
    session = get_gym_session_by_id(conn, 10)
    assert session is not None
    assert session["id"] == 10
    assert session["session_rpe"] == 8


def test_get_fatigue_breakdown_by_muscle(conn: sqlite3.Connection) -> None:
    # Setup data
    conn.execute("INSERT INTO muscle_groups (id, name, label, is_front) VALUES (1, 'triceps', 'Triceps', 0)")
    conn.execute("INSERT INTO muscles (id, name, label, muscle_group_id) VALUES (1, 'Triceps Long Head', 'Triceps Long Head', 1)")
    conn.execute("INSERT INTO exercises (id, name, category) VALUES (1, 'Close-Grip Bench', 'compound')")
    conn.execute("INSERT INTO exercise_muscles (exercise_id, muscle_id, coefficient, role) VALUES (1, 1, 1.0, 'primary')")
    
    # Session within last 72 hours
    today = date.today().isoformat()
    conn.execute(f"INSERT INTO gym_sessions (id, session_date) VALUES (1, '{today}')")
    
    # 100kg x 5 = 500 volume
    conn.execute(
        "INSERT INTO gym_sets (session_id, exercise_id, set_order, weight_kg, reps) "
        "VALUES (1, 1, 1, 100.0, 5)"
    )
    conn.commit()
    
    rows, total, label = get_fatigue_breakdown_by_muscle(conn, "Triceps", hours=72)
    
    assert label == "Triceps"
    assert total == 500.0
    assert len(rows) == 1
    assert rows[0]["exercise_name"] == "Close-Grip Bench"
    assert rows[0]["weighted_volume"] == 500.0


def test_get_fatigue_breakdown_muscle_not_found(conn: sqlite3.Connection) -> None:
    # If no rows are found, it returns None for the label
    rows, total, label = get_fatigue_breakdown_by_muscle(conn, "NonExistent", hours=72)
    assert rows == []
    assert total == 0.0
    assert label is None
