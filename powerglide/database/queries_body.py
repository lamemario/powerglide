"""Body composition and athlete constraints data operations."""

from __future__ import annotations
import json
import sqlite3

def add_body_composition(
    conn: sqlite3.Connection,
    measured_date: str,
    total_weight_kg: float | None = None,
    muscle_mass_kg: float | None = None,
    body_fat_pct: float | None = None,
    total_body_water_pct: float | None = None,
    visceral_fat_level: int | None = None,
    bmr_kcal: int | None = None,
    notes: str | None = None,
) -> int:
    cur = conn.execute(
        "INSERT INTO body_composition "
        "(measured_date, total_weight_kg, muscle_mass_kg, body_fat_pct, "
        "total_body_water_pct, visceral_fat_level, bmr_kcal, notes) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (measured_date, total_weight_kg, muscle_mass_kg, body_fat_pct,
         total_body_water_pct, visceral_fat_level, bmr_kcal, notes),
    )
    conn.commit()
    return cur.lastrowid  # type: ignore[return-value]


def get_body_compositions(
    conn: sqlite3.Connection, limit: int = 20
) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM body_composition ORDER BY measured_date DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]


def add_constraint(
    conn: sqlite3.Connection,
    name: str,
    date_start: str,
    description: str | None = None,
    affected_muscles: list[str] | None = None,
) -> int:
    muscles_json = json.dumps(affected_muscles) if affected_muscles else None
    cur = conn.execute(
        "INSERT INTO athlete_constraints (name, description, affected_muscles, date_start) "
        "VALUES (?, ?, ?, ?)",
        (name, description, muscles_json, date_start),
    )
    conn.commit()
    return cur.lastrowid  # type: ignore[return-value]


def end_constraint(conn: sqlite3.Connection, constraint_id: int, date_end: str) -> None:
    conn.execute(
        "UPDATE athlete_constraints SET date_end = ? WHERE id = ?",
        (date_end, constraint_id),
    )
    conn.commit()


def get_active_constraints(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM athlete_constraints WHERE date_end IS NULL"
    ).fetchall()
    return [dict(r) for r in rows]


def get_all_constraints(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM athlete_constraints ORDER BY date_start DESC"
    ).fetchall()
    return [dict(r) for r in rows]


def delete_body_composition(conn: sqlite3.Connection, record_id: int) -> bool:
    cur = conn.execute("DELETE FROM body_composition WHERE id = ?", (record_id,))
    conn.commit()
    return cur.rowcount > 0


def delete_constraint(conn: sqlite3.Connection, constraint_id: int) -> bool:
    cur = conn.execute("DELETE FROM athlete_constraints WHERE id = ?", (constraint_id,))
    conn.commit()
    return cur.rowcount > 0
