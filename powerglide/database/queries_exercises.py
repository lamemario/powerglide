"""Exercise-related data access operations including fuzzy matching."""

from __future__ import annotations
import sqlite3

_ABBREVIATIONS = {
    "db": "dumbbell",
    "bb": "barbell",
    "kb": "kettlebell",
    "ohp": "overhead press",
    "rdl": "romanian deadlift",
    "sldl": "stiff-legged deadlift",
    "ez": "ez-bar",
    "btn": "behind the neck",
    "cg": "close-grip",
    "wg": "wide-grip",
    "inc": "incline",
    "dec": "decline",
}

def search_exercises(conn: sqlite3.Connection, query: str, limit: int = 10) -> list[dict]:
    rows = conn.execute(
        "SELECT id, name, category, equipment, force_type, exercise_type "
        "FROM exercises WHERE name LIKE ? ORDER BY name LIMIT ?",
        (f"%{query}%", limit),
    ).fetchall()
    return [dict(r) for r in rows]


def get_exercise_by_id(conn: sqlite3.Connection, exercise_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM exercises WHERE id = ?", (exercise_id,)).fetchone()
    return dict(row) if row else None


def get_exercise_by_name(conn: sqlite3.Connection, name: str) -> dict | None:
    row = conn.execute(
        "SELECT * FROM exercises WHERE LOWER(name) = LOWER(?)", (name,)
    ).fetchone()
    if row:
        return dict(row)
    expanded = _expand_abbreviations(name)
    if expanded != name.lower():
        row = conn.execute(
            "SELECT * FROM exercises WHERE LOWER(name) = LOWER(?)", (expanded,)
        ).fetchone()
    return dict(row) if row else None


def get_all_exercise_names(conn: sqlite3.Connection) -> list[tuple[int, str]]:
    rows = conn.execute("SELECT id, name FROM exercises ORDER BY name").fetchall()
    return [(r["id"], r["name"]) for r in rows]


def _expand_abbreviations(text: str) -> str:
    words = text.lower().split()
    return " ".join(_ABBREVIATIONS.get(w, w) for w in words)


def fuzzy_match_exercise(
    conn: sqlite3.Connection,
    query: str,
    threshold: int = 50,
    limit: int = 5,
) -> list[tuple[dict, int]]:
    """Return exercises matching query by fuzzy score, above threshold."""
    from thefuzz import fuzz

    all_exercises = conn.execute(
        "SELECT id, name, category, equipment, force_type, exercise_type FROM exercises"
    ).fetchall()

    query_expanded = _expand_abbreviations(query)

    scored: list[tuple[dict, int]] = []
    for row in all_exercises:
        name_lower = row["name"].lower()
        score = max(
            fuzz.ratio(query_expanded, name_lower),
            fuzz.token_sort_ratio(query_expanded, name_lower),
            fuzz.token_set_ratio(query_expanded, name_lower),
        )
        if score >= threshold:
            scored.append((dict(row), score))

    scored.sort(key=lambda x: -x[1])
    return scored[:limit]
