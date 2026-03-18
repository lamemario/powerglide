"""Water-related data access operations."""

from __future__ import annotations
import sqlite3

def create_water_session(
    conn: sqlite3.Connection,
    session_date: str,
    duration_minutes: int | None = None,
    session_rpe: int | None = None,
    water_condition: str | None = None,
    wind_condition: str | None = None,
    wind_speed_kmh: float | None = None,
    temperature_c: float | None = None,
    boat_type: str = "C1",
    location: str | None = None,
    notes: str | None = None,
) -> int:
    cur = conn.execute(
        "INSERT INTO water_sessions "
        "(session_date, duration_minutes, session_rpe, water_condition, wind_condition, "
        "wind_speed_kmh, temperature_c, boat_type, location, notes) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (session_date, duration_minutes, session_rpe, water_condition, wind_condition,
         wind_speed_kmh, temperature_c, boat_type, location, notes),
    )
    conn.commit()
    return cur.lastrowid  # type: ignore[return-value]


def add_water_piece(
    conn: sqlite3.Connection,
    session_id: int,
    piece_order: int,
    distance_m: int,
    time_seconds: float,
    avg_spm: float | None = None,
    peak_spm: float | None = None,
    stroke_count: int | None = None,
    leg_drive_rpe: int | None = None,
    perceived_power: int | None = None,
    piece_rpe: int | None = None,
    notes: str | None = None,
) -> int:
    cur = conn.execute(
        "INSERT INTO water_pieces "
        "(session_id, piece_order, distance_m, time_seconds, avg_spm, peak_spm, "
        "stroke_count, leg_drive_rpe, perceived_power, piece_rpe, notes) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (session_id, piece_order, distance_m, time_seconds, avg_spm, peak_spm,
         stroke_count, leg_drive_rpe, perceived_power, piece_rpe, notes),
    )
    conn.commit()
    return cur.lastrowid  # type: ignore[return-value]


def get_water_sessions(
    conn: sqlite3.Connection, limit: int = 10, offset: int = 0
) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM water_sessions ORDER BY session_date DESC LIMIT ? OFFSET ?",
        (limit, offset),
    ).fetchall()
    return [dict(r) for r in rows]


def get_water_pieces(conn: sqlite3.Connection, session_id: int) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM water_pieces WHERE session_id = ? ORDER BY piece_order",
        (session_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def delete_water_session(conn: sqlite3.Connection, session_id: int) -> int:
    pieces_deleted = conn.execute(
        "SELECT COUNT(*) FROM water_pieces WHERE session_id = ?", (session_id,)
    ).fetchone()[0]
    conn.execute("DELETE FROM water_sessions WHERE id = ?", (session_id,))
    conn.commit()
    return pieces_deleted


def delete_water_piece(conn: sqlite3.Connection, piece_id: int) -> bool:
    cur = conn.execute("DELETE FROM water_pieces WHERE id = ?", (piece_id,))
    conn.commit()
    return cur.rowcount > 0


def delete_all_water_data(conn: sqlite3.Connection) -> tuple[int, int]:
    pieces = conn.execute("SELECT COUNT(*) FROM water_pieces").fetchone()[0]
    sessions = conn.execute("SELECT COUNT(*) FROM water_sessions").fetchone()[0]
    conn.execute("DELETE FROM water_pieces")
    conn.execute("DELETE FROM water_sessions")
    conn.commit()
    return sessions, pieces
