-- PowerGlide Schema v1 — Research-driven architecture for C1 sprint paddlers.

CREATE TABLE IF NOT EXISTS schema_version (
    version     INTEGER PRIMARY KEY,
    applied_at  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS muscle_groups (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    label       TEXT NOT NULL,
    is_front    BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS muscles (
    id              INTEGER PRIMARY KEY,
    muscle_group_id INTEGER NOT NULL REFERENCES muscle_groups(id),
    name            TEXT NOT NULL UNIQUE,
    label           TEXT NOT NULL,
    c1_relevance    INTEGER DEFAULT 0 CHECK(c1_relevance BETWEEN 0 AND 5)
);

CREATE TABLE IF NOT EXISTS exercises (
    id                  INTEGER PRIMARY KEY,
    name                TEXT NOT NULL UNIQUE,
    category            TEXT NOT NULL,
    equipment           TEXT,
    force_type          TEXT,
    movement_pattern    TEXT,
    exercise_type       TEXT,
    level               TEXT,
    c1_relevance        INTEGER DEFAULT 0 CHECK(c1_relevance BETWEEN 0 AND 5),
    c1_force_analog     TEXT,
    instructions        TEXT,
    source              TEXT DEFAULT 'free-exercise-db',
    created_at          TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS exercise_muscles (
    exercise_id     INTEGER NOT NULL REFERENCES exercises(id) ON DELETE CASCADE,
    muscle_id       INTEGER NOT NULL REFERENCES muscles(id) ON DELETE CASCADE,
    role            TEXT NOT NULL CHECK(role IN ('primary','secondary','stabilizer')),
    coefficient     REAL NOT NULL DEFAULT 1.0 CHECK(coefficient >= 0.0 AND coefficient <= 1.0),
    PRIMARY KEY (exercise_id, muscle_id)
);

CREATE TABLE IF NOT EXISTS athlete_constraints (
    id              INTEGER PRIMARY KEY,
    name            TEXT NOT NULL,
    description     TEXT,
    affected_muscles TEXT,
    date_start      TEXT NOT NULL,
    date_end        TEXT,
    is_active       BOOLEAN GENERATED ALWAYS AS (date_end IS NULL) STORED
);

CREATE TABLE IF NOT EXISTS gym_sessions (
    id                      INTEGER PRIMARY KEY,
    session_date            TEXT NOT NULL,
    start_time              TEXT,
    duration_minutes        INTEGER,
    session_rpe             INTEGER CHECK(session_rpe BETWEEN 1 AND 10),
    srpe                    REAL GENERATED ALWAYS AS (duration_minutes * session_rpe) STORED,
    external_load_source    TEXT,
    garmin_activity_id      TEXT,
    notes                   TEXT,
    created_at              TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS gym_sets (
    id              INTEGER PRIMARY KEY,
    session_id      INTEGER NOT NULL REFERENCES gym_sessions(id) ON DELETE CASCADE,
    exercise_id     INTEGER NOT NULL REFERENCES exercises(id),
    set_order       INTEGER NOT NULL,
    weight_kg       REAL NOT NULL,
    reps            INTEGER NOT NULL CHECK(reps >= 0),
    rpe             INTEGER CHECK(rpe BETWEEN 1 AND 10),
    tempo           TEXT,
    is_warmup       BOOLEAN DEFAULT 0,
    is_amrap        BOOLEAN DEFAULT 0,
    tags            TEXT,
    estimated_1rm   REAL GENERATED ALWAYS AS (
        CASE
            WHEN reps = 0 THEN NULL
            WHEN reps = 1 THEN weight_kg
            WHEN reps >= 2 AND reps <= 10 THEN ROUND(weight_kg * 36.0 / (37.0 - reps), 1)
            WHEN reps > 10 THEN ROUND(weight_kg * (1.0 + reps / 30.0), 1)
            ELSE NULL
        END
    ) STORED,
    volume_load     REAL GENERATED ALWAYS AS (weight_kg * reps) STORED,
    created_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS water_sessions (
    id                      INTEGER PRIMARY KEY,
    session_date            TEXT NOT NULL,
    start_time              TEXT,
    duration_minutes        INTEGER,
    session_rpe             INTEGER CHECK(session_rpe BETWEEN 1 AND 10),
    srpe                    REAL GENERATED ALWAYS AS (duration_minutes * session_rpe) STORED,
    water_condition         TEXT,
    wind_condition          TEXT,
    wind_speed_kmh          REAL,
    temperature_c           REAL,
    boat_type               TEXT DEFAULT 'C1',
    location                TEXT,
    external_load_source    TEXT,
    garmin_activity_id      TEXT,
    notes                   TEXT,
    created_at              TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS water_pieces (
    id                  INTEGER PRIMARY KEY,
    session_id          INTEGER NOT NULL REFERENCES water_sessions(id) ON DELETE CASCADE,
    piece_order         INTEGER NOT NULL,
    distance_m          INTEGER NOT NULL,
    time_seconds        REAL NOT NULL,
    avg_spm             REAL,
    peak_spm            REAL,
    avg_split_per_500m  REAL GENERATED ALWAYS AS (
        CASE WHEN distance_m > 0 THEN ROUND((time_seconds / distance_m) * 500.0, 2)
             ELSE NULL END
    ) STORED,
    avg_velocity_ms     REAL GENERATED ALWAYS AS (
        CASE WHEN time_seconds > 0 THEN ROUND(distance_m * 1.0 / time_seconds, 3)
             ELSE NULL END
    ) STORED,
    stroke_count        INTEGER,
    distance_per_stroke REAL GENERATED ALWAYS AS (
        CASE WHEN stroke_count > 0 THEN ROUND(distance_m * 1.0 / stroke_count, 2)
             ELSE NULL END
    ) STORED,
    leg_drive_rpe       INTEGER CHECK(leg_drive_rpe BETWEEN 0 AND 10),
    perceived_power     INTEGER CHECK(perceived_power BETWEEN 1 AND 10),
    piece_rpe           INTEGER CHECK(piece_rpe BETWEEN 1 AND 10),
    notes               TEXT,
    created_at          TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS body_composition (
    id                      INTEGER PRIMARY KEY,
    measured_date           TEXT NOT NULL,
    total_weight_kg         REAL,
    muscle_mass_kg          REAL,
    body_fat_pct            REAL,
    total_body_water_pct    REAL,
    visceral_fat_level      INTEGER,
    bmr_kcal                INTEGER,
    notes                   TEXT,
    created_at              TEXT DEFAULT (datetime('now'))
);

CREATE VIEW IF NOT EXISTS daily_training_load AS
SELECT
    session_date,
    'gym' AS session_type,
    srpe AS training_load
FROM gym_sessions
WHERE duration_minutes IS NOT NULL AND session_rpe IS NOT NULL
UNION ALL
SELECT
    session_date,
    'water' AS session_type,
    srpe AS training_load
FROM water_sessions
WHERE duration_minutes IS NOT NULL AND session_rpe IS NOT NULL;

INSERT OR IGNORE INTO schema_version (version) VALUES (1);
