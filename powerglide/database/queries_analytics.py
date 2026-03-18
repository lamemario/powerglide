"""Analytics and reporting queries (e.g. 72h fatigue map, correlations)."""

from __future__ import annotations
import sqlite3
from datetime import date

def get_daily_training_loads(
    conn: sqlite3.Connection, days: int = 90
) -> list[tuple[date, float]]:
    """Aggregate sRPE per day across gym + water, for the last N days."""
    rows = conn.execute(
        "SELECT session_date, SUM(training_load) as total_load "
        "FROM daily_training_load "
        "WHERE session_date >= date('now', ? || ' days') "
        "GROUP BY session_date ORDER BY session_date",
        (f"-{days}",),
    ).fetchall()
    return [
        (date.fromisoformat(r["session_date"]), r["total_load"])
        for r in rows
    ]


def get_volume_by_muscle_group(
    conn: sqlite3.Connection, hours: int = 72
) -> list[dict]:
    """Volume distribution across muscle groups for the trailing N hours."""
    rows = conn.execute(
        """
        SELECT muscle_group, label, is_front, SUM(max_weighted_volume) AS weighted_volume
        FROM (
            SELECT mg.name AS muscle_group, mg.label, mg.is_front,
                   MAX(gs.volume_load * em.coefficient) AS max_weighted_volume
            FROM gym_sets gs
            JOIN gym_sessions s ON gs.session_id = s.id
            JOIN exercise_muscles em ON gs.exercise_id = em.exercise_id
            JOIN muscles m ON em.muscle_id = m.id
            JOIN muscle_groups mg ON m.muscle_group_id = mg.id
            WHERE s.session_date >= date('now', ? || ' hours')
            GROUP BY gs.id, mg.id
        )
        GROUP BY muscle_group
        ORDER BY weighted_volume DESC
        """,
        (f"-{hours}",),
    ).fetchall()
    return [dict(r) for r in rows]


def get_fatigue_breakdown_by_muscle(
    conn: sqlite3.Connection,
    muscle_pattern: str,
    hours: int = 72,
) -> tuple[list[dict], float, str | None]:
    """
    Per-set breakdown of weighted volume for a muscle group (match by name or label).
    Returns (rows, total_weighted_volume, matched_muscle_group_label).
    Each row: exercise_name, raw_volume, coefficient, role, weighted_volume.
    """
    pattern = f"%{muscle_pattern}%"
    rows = conn.execute(
        """
        SELECT e.name AS exercise_name,
               gs.volume_load AS raw_volume,
               MAX(em.coefficient) AS coefficient,
               em.role,
               (gs.volume_load * MAX(em.coefficient)) AS weighted_volume
        FROM gym_sets gs
        JOIN gym_sessions s ON gs.session_id = s.id
        JOIN exercises e ON gs.exercise_id = e.id
        JOIN exercise_muscles em ON gs.exercise_id = em.exercise_id
        JOIN muscles m ON em.muscle_id = m.id
        JOIN muscle_groups mg ON m.muscle_group_id = mg.id
        WHERE s.session_date >= date('now', ? || ' hours')
          AND (mg.name LIKE ? OR mg.label LIKE ?)
        GROUP BY gs.id, mg.id
        ORDER BY e.name, gs.set_order
        """,
        (f"-{hours}", pattern, pattern),
    ).fetchall()
    if not rows:
        return [], 0.0, None
    total = sum(r["weighted_volume"] for r in rows)
    label_row = conn.execute(
        "SELECT mg.label FROM muscle_groups mg WHERE mg.name LIKE ? OR mg.label LIKE ? LIMIT 1",
        (pattern, pattern),
    ).fetchone()
    label = label_row["label"] if label_row else muscle_pattern
    return [dict(r) for r in rows], total, label


def get_strength_speed_data(conn: sqlite3.Connection, exercise_id: int) -> list[dict]:
    """
    Pair gym e1RM for a specific exercise with the nearest water split
    within a +/- 7 day window, for the correlation scatter plot.
    """
    rows = conn.execute(
        """
        SELECT
            gs.estimated_1rm,
            s.session_date AS gym_date,
            wp.avg_split_per_500m,
            ws.session_date AS water_date,
            wp.distance_m
        FROM gym_sets gs
        JOIN gym_sessions s ON gs.session_id = s.id
        JOIN water_pieces wp ON 1=1
        JOIN water_sessions ws ON wp.session_id = ws.id
        WHERE gs.exercise_id = ?
          AND gs.estimated_1rm IS NOT NULL
          AND wp.avg_split_per_500m IS NOT NULL
          AND ABS(julianday(s.session_date) - julianday(ws.session_date)) <= 7
        ORDER BY s.session_date
        """,
        (exercise_id,),
    ).fetchall()
    return [dict(r) for r in rows]

def get_time_based_data(conn: sqlite3.Connection, exercise_id: int) -> list[dict]:
    """Retrieve historical Max and Total Time Under Tension (TUT) for an exercise per session."""
    rows = conn.execute(
        """
        SELECT 
            sess.session_date,
            MAX(gs.time_seconds) as max_tut,
            SUM(gs.time_seconds) as total_tut,
            COUNT(gs.id) as set_count
        FROM gym_sets gs
        JOIN gym_sessions sess ON gs.session_id = sess.id
        WHERE gs.exercise_id = ? AND gs.time_seconds IS NOT NULL
        GROUP BY sess.session_date
        ORDER BY sess.session_date ASC
        """,
        (exercise_id,)
    ).fetchall()
    return [dict(r) for r in rows]
