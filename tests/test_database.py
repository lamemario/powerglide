"""Integration tests for database: generated columns, cascades, and views."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

# In-memory DB with same schema as production (run migration).
MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "powerglide" / "database" / "migrations"


def _get_migration_sql() -> str:
    mig = MIGRATIONS_DIR / "001_initial.sql"
    return mig.read_text(encoding="utf-8")


@pytest.fixture
def conn() -> sqlite3.Connection:
    """In-memory SQLite connection with PowerGlide schema applied."""
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    c.executescript(_get_migration_sql())
    return c


def test_gym_sets_generated_estimated_1rm_and_volume_load(conn: sqlite3.Connection) -> None:
    """Generated columns estimated_1rm and volume_load are computed on insert."""
    conn.execute(
        "INSERT INTO exercises (id, name, category) VALUES (1, 'Bench Press', 'compound')"
    )
    conn.execute(
        "INSERT INTO gym_sessions (id, session_date, duration_minutes, session_rpe) "
        "VALUES (1, '2026-01-15', 60, 7)"
    )
    # 100 kg x 5 reps: Brzycki 1RM = 100 * 36 / (37-5) = 112.5; volume_load = 500
    conn.execute(
        "INSERT INTO gym_sets (session_id, exercise_id, set_order, weight_kg, reps) "
        "VALUES (1, 1, 1, 100.0, 5)"
    )
    conn.commit()

    row = conn.execute(
        "SELECT estimated_1rm, volume_load FROM gym_sets WHERE session_id = 1"
    ).fetchone()
    assert row is not None
    assert row["estimated_1rm"] == 112.5
    assert row["volume_load"] == 500.0


def test_gym_sets_cascade_delete(conn: sqlite3.Connection) -> None:
    """Deleting a gym_session removes all related gym_sets."""
    conn.execute(
        "INSERT INTO exercises (id, name, category) VALUES (1, 'Squat', 'compound')"
    )
    conn.execute(
        "INSERT INTO gym_sessions (id, session_date) VALUES (1, '2026-01-01')"
    )
    conn.execute(
        "INSERT INTO gym_sets (session_id, exercise_id, set_order, weight_kg, reps) "
        "VALUES (1, 1, 1, 80.0, 10)"
    )
    conn.commit()

    before = conn.execute("SELECT COUNT(*) AS n FROM gym_sets").fetchone()["n"]
    assert before == 1

    conn.execute("DELETE FROM gym_sessions WHERE id = 1")
    conn.commit()

    after = conn.execute("SELECT COUNT(*) AS n FROM gym_sets").fetchone()["n"]
    assert after == 0


def test_daily_training_load_view_merges_gym_and_water_srpe(conn: sqlite3.Connection) -> None:
    """VIEW daily_training_load returns gym and water sRPE rows."""
    conn.execute(
        "INSERT INTO gym_sessions (id, session_date, duration_minutes, session_rpe) "
        "VALUES (1, '2026-01-10', 45, 7)"
    )
    conn.execute(
        "INSERT INTO water_sessions (id, session_date, duration_minutes, session_rpe) "
        "VALUES (1, '2026-01-10', 30, 8)"
    )
    conn.commit()

    rows = conn.execute(
        "SELECT session_date, session_type, training_load FROM daily_training_load ORDER BY session_type"
    ).fetchall()

    assert len(rows) == 2
    gym_row = next(r for r in rows if r["session_type"] == "gym")
    water_row = next(r for r in rows if r["session_type"] == "water")
    assert gym_row["session_date"] == "2026-01-10"
    assert gym_row["training_load"] == 45 * 7  # 315
    assert water_row["training_load"] == 30 * 8  # 240
