"""
Seed the exercises, muscles, and muscle_groups tables from:
1. Internal constants (muscle taxonomy)
2. yuhonas/free-exercise-db (bundled JSON)
3. C1 enrichment overlay (curated sport-specific metadata)

Idempotent — safe to re-run. Existing rows are skipped via INSERT OR IGNORE.
"""

from __future__ import annotations

import json
import sqlite3
import urllib.request
from pathlib import Path

from powerglide.core.constants import (
    C1_ENRICHMENT,
    MUSCLE_GROUPS_SEED,
    MUSCLES_SEED,
    YUHONAS_MUSCLE_MAP,
)
from powerglide.database.db import get_connection, init_db

EXERCISES_JSON_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "exercises.json"
EXERCISES_URL = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/dist/exercises.json"


def _download_exercises(dest: Path) -> None:
    """Download exercises.json from GitHub if not already cached."""
    if dest.exists() and dest.stat().st_size > 1000:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"  Downloading exercise database from GitHub -> {dest.name} ...")
    urllib.request.urlretrieve(EXERCISES_URL, str(dest))
    print(f"  Downloaded ({dest.stat().st_size / 1024:.0f} KB).")


def seed_muscle_groups(conn: sqlite3.Connection) -> dict[str, int]:
    """Insert muscle groups, return {name: id} mapping."""
    for name, label, is_front in MUSCLE_GROUPS_SEED:
        conn.execute(
            "INSERT OR IGNORE INTO muscle_groups (name, label, is_front) VALUES (?, ?, ?)",
            (name, label, int(is_front)),
        )
    conn.commit()
    rows = conn.execute("SELECT id, name FROM muscle_groups").fetchall()
    return {r["name"]: r["id"] for r in rows}


def seed_muscles(conn: sqlite3.Connection, group_map: dict[str, int]) -> dict[str, int]:
    """Insert individual muscles, return {muscle_name: id} mapping."""
    for group_name, muscle_name, label, c1_rel in MUSCLES_SEED:
        gid = group_map.get(group_name)
        if gid is None:
            continue
        conn.execute(
            "INSERT OR IGNORE INTO muscles (muscle_group_id, name, label, c1_relevance) "
            "VALUES (?, ?, ?, ?)",
            (gid, muscle_name, label, c1_rel),
        )
    conn.commit()
    rows = conn.execute("SELECT id, name FROM muscles").fetchall()
    return {r["name"]: r["id"] for r in rows}


def seed_exercises(
    conn: sqlite3.Connection,
    muscle_map: dict[str, int],
    exercises_path: Path | None = None,
) -> int:
    """Load exercises from JSON, apply C1 enrichment, insert into DB. Returns count."""
    path = exercises_path or EXERCISES_JSON_PATH
    _download_exercises(path)

    with open(path, encoding="utf-8") as f:
        raw_exercises: list[dict] = json.load(f)

    count = 0
    for ex in raw_exercises:
        name = ex.get("name", "").strip()
        if not name:
            continue

        force_type = ex.get("force")
        exercise_type = ex.get("mechanic")
        category = ex.get("category", "strength")
        equipment = ex.get("equipment")
        level = ex.get("level")
        instructions = json.dumps(ex.get("instructions", []))

        enrichment = C1_ENRICHMENT.get(name.lower(), {})
        movement_pattern = enrichment.get("movement_pattern")
        c1_relevance = enrichment.get("c1_relevance", 0)
        c1_force_analog = enrichment.get("c1_force_analog")

        try:
            conn.execute(
                "INSERT OR IGNORE INTO exercises "
                "(name, category, equipment, force_type, movement_pattern, exercise_type, "
                "level, c1_relevance, c1_force_analog, instructions) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (name, category, equipment, force_type, movement_pattern,
                 exercise_type, level, c1_relevance, c1_force_analog, instructions),
            )
        except sqlite3.IntegrityError:
            continue

        row = conn.execute(
            "SELECT id FROM exercises WHERE name = ?", (name,)
        ).fetchone()
        if row is None:
            continue
        ex_id = row["id"]

        for pm in ex.get("primaryMuscles", []):
            canonical = YUHONAS_MUSCLE_MAP.get(pm.lower())
            if canonical and canonical in muscle_map:
                conn.execute(
                    "INSERT OR IGNORE INTO exercise_muscles (exercise_id, muscle_id, role, coefficient) "
                    "VALUES (?, ?, 'primary', 1.0)",
                    (ex_id, muscle_map[canonical]),
                )

        for sm in ex.get("secondaryMuscles", []):
            canonical = YUHONAS_MUSCLE_MAP.get(sm.lower())
            if canonical and canonical in muscle_map:
                conn.execute(
                    "INSERT OR IGNORE INTO exercise_muscles (exercise_id, muscle_id, role, coefficient) "
                    "VALUES (?, ?, 'secondary', 0.5)",
                    (ex_id, muscle_map[canonical]),
                )

        count += 1

    conn.commit()
    return count


def run_seed(conn: sqlite3.Connection | None = None) -> None:
    """Full seed pipeline: muscles → exercises → C1 enrichment."""
    if conn is None:
        conn = get_connection()
        init_db(conn)

    existing = conn.execute("SELECT COUNT(*) FROM exercises").fetchone()[0]
    if existing > 0:
        print(f"  Database already seeded ({existing} exercises). Skipping.")
        print("  Use --force to re-seed (drops and re-creates exercise data).")
        return

    print("Seeding PowerGlide database...")

    print("  [1/3] Muscle groups & muscles...")
    group_map = seed_muscle_groups(conn)
    muscle_map = seed_muscles(conn, group_map)
    print(f"         {len(group_map)} groups, {len(muscle_map)} muscles.")

    print("  [2/3] Exercises from free-exercise-db...")
    count = seed_exercises(conn, muscle_map)
    print(f"         {count} exercises loaded.")

    enriched = sum(1 for v in C1_ENRICHMENT.values())
    print(f"  [3/3] C1 enrichment overlay applied ({enriched} exercises tagged).")

    print("Done.")


def force_reseed(conn: sqlite3.Connection | None = None) -> None:
    """Drop exercise data and re-seed from scratch."""
    if conn is None:
        conn = get_connection()
        init_db(conn)

    conn.execute("DELETE FROM exercise_muscles")
    conn.execute("DELETE FROM exercises")
    conn.execute("DELETE FROM muscles")
    conn.execute("DELETE FROM muscle_groups")
    conn.commit()
    print("  Cleared existing exercise data.")
    run_seed(conn)


if __name__ == "__main__":
    run_seed()
