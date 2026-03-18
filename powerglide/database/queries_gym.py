"""Gym-related data access operations."""

from __future__ import annotations
import json
import sqlite3
from datetime import date

def create_gym_session(
    conn: sqlite3.Connection,
    session_date: str,
    duration_minutes: int | None = None,
    session_rpe: int | None = None,
    start_time: str | None = None,
    notes: str | None = None,
) -> int:
    cur = conn.execute(
        "INSERT INTO gym_sessions (session_date, start_time, duration_minutes, session_rpe, notes) "
        "VALUES (?, ?, ?, ?, ?)",
        (session_date, start_time, duration_minutes, session_rpe, notes),
    )
    conn.commit()
    return cur.lastrowid  # type: ignore[return-value]


def add_gym_set(
    conn: sqlite3.Connection,
    session_id: int,
    exercise_id: int,
    set_order: int,
    weight_kg: float,
    reps: int,
    rpe: int | None = None,
    tempo: str | None = None,
    is_warmup: bool = False,
    is_amrap: bool = False,
    tags: list[str] | None = None,
    time_seconds: int | None = None,
) -> int:
    tags_json = json.dumps(tags) if tags else None
    cur = conn.execute(
        "INSERT INTO gym_sets "
        "(session_id, exercise_id, set_order, weight_kg, reps, rpe, tempo, is_warmup, is_amrap, tags, time_seconds) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (session_id, exercise_id, set_order, weight_kg, reps, rpe, tempo,
         int(is_warmup), int(is_amrap), tags_json, time_seconds),
    )
    conn.commit()
    return cur.lastrowid  # type: ignore[return-value]


def get_gym_sessions(
    conn: sqlite3.Connection,
    limit: int = 10,
    offset: int = 0,
) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM gym_sessions ORDER BY session_date DESC, id DESC LIMIT ? OFFSET ?",
        (limit, offset),
    ).fetchall()
    return [dict(r) for r in rows]


def get_gym_sets_for_session(conn: sqlite3.Connection, session_id: int) -> list[dict]:
    rows = conn.execute(
        "SELECT gs.*, e.name AS exercise_name "
        "FROM gym_sets gs JOIN exercises e ON gs.exercise_id = e.id "
        "WHERE gs.session_id = ? ORDER BY gs.set_order",
        (session_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def get_gym_session_by_id(conn: sqlite3.Connection, session_id: int) -> dict | None:
    """Get a single gym session by id, or None if not found."""
    row = conn.execute(
        "SELECT * FROM gym_sessions WHERE id = ?", (session_id,)
    ).fetchone()
    return dict(row) if row else None


def get_exercise_history(
    conn: sqlite3.Connection,
    exercise_id: int,
    limit: int = 50,
) -> list[dict]:
    rows = conn.execute(
        "SELECT gs.*, s.session_date "
        "FROM gym_sets gs JOIN gym_sessions s ON gs.session_id = s.id "
        "WHERE gs.exercise_id = ? ORDER BY s.session_date DESC, gs.set_order "
        "LIMIT ?",
        (exercise_id, limit),
    ).fetchall()
    return [dict(r) for r in rows]


def get_or_create_today_gym_session(
    conn: sqlite3.Connection,
    session_date: str | None = None,
) -> int:
    """Get today's gym session or create one if it doesn't exist."""
    d = session_date or date.today().isoformat()
    row = conn.execute(
        "SELECT id FROM gym_sessions WHERE session_date = ? ORDER BY id DESC LIMIT 1",
        (d,),
    ).fetchone()
    if row:
        return row["id"]
    return create_gym_session(conn, d)


def get_next_set_order(conn: sqlite3.Connection, session_id: int) -> int:
    row = conn.execute(
        "SELECT COALESCE(MAX(set_order), 0) + 1 AS next_order "
        "FROM gym_sets WHERE session_id = ?",
        (session_id,),
    ).fetchone()
    return row["next_order"]


def update_gym_session(
    conn: sqlite3.Connection,
    session_id: int,
    duration_minutes: int | None = None,
    session_rpe: int | None = None,
) -> bool:
    """Update gym session duration and/or RPE."""
    fields = []
    params = []
    if duration_minutes is not None:
        fields.append("duration_minutes = ?")
        params.append(duration_minutes)
    if session_rpe is not None:
        fields.append("session_rpe = ?")
        params.append(session_rpe)

    if not fields:
        return False

    params.append(session_id)
    cur = conn.execute(
        f"UPDATE gym_sessions SET {', '.join(fields)} WHERE id = ?",
        tuple(params),
    )
    conn.commit()
    return cur.rowcount > 0


def delete_gym_session(conn: sqlite3.Connection, session_id: int) -> int:
    """Delete a gym session and all its sets (CASCADE). Returns rows affected."""
    sets_deleted = conn.execute(
        "SELECT COUNT(*) FROM gym_sets WHERE session_id = ?", (session_id,)
    ).fetchone()[0]
    conn.execute("DELETE FROM gym_sessions WHERE id = ?", (session_id,))
    conn.commit()
    return sets_deleted


def delete_gym_set(conn: sqlite3.Connection, set_id: int) -> bool:
    cur = conn.execute("DELETE FROM gym_sets WHERE id = ?", (set_id,))
    conn.commit()
    return cur.rowcount > 0


def delete_all_gym_data(conn: sqlite3.Connection) -> tuple[int, int]:
    sets = conn.execute("SELECT COUNT(*) FROM gym_sets").fetchone()[0]
    sessions = conn.execute("SELECT COUNT(*) FROM gym_sessions").fetchone()[0]
    conn.execute("DELETE FROM gym_sets")
    conn.execute("DELETE FROM gym_sessions")
    conn.commit()
    return sessions, sets
