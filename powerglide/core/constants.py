"""Centralized constants derived from sports science research."""

from __future__ import annotations

BORG_CR10_SCALE: dict[int, tuple[str, str]] = {
    1:  ("Very Light",    "Barely any exertion. Easy walking pace."),
    2:  ("Light",         "Comfortable effort. Could sustain for hours."),
    3:  ("Moderate",      "Breathing harder but can hold conversation."),
    4:  ("Somewhat Hard", "Starting to sweat. Conversation becomes choppy."),
    5:  ("Hard",          "Deep breathing. Can speak only in short phrases."),
    6:  ("Hard+",         "Sustained high effort. Speech limited to single words."),
    7:  ("Very Hard",     "Difficult to maintain. Approaching muscular burn."),
    8:  ("Very Hard+",    "Extreme effort. Only a few minutes sustainable."),
    9:  ("Near Maximal",  "Cannot maintain longer than 30-60 seconds."),
    10: ("Maximal",       "All-out. Impossible to continue. Complete exhaustion."),
}

BORG_CR10_TABLE = (
    "RPE | Descriptor     | What it feels like\n"
    "----|----------------|-------------------------------------------\n"
    + "\n".join(
        f" {k:>2} | {v[0]:<14} | {v[1]}"
        for k, v in BORG_CR10_SCALE.items()
    )
)

# ACWR risk zones (defaults; user-tunable via powerglide.toml [acwr]).
# Qin et al. (2025) BMC Sports Sci Med Rehabil: 0.8–1.3 low-risk, >1.5 higher risk (Research Papers/ACWR.pdf).
ACWR_ZONES = {
    "undertrained":  (0.0, 0.80),
    "optimal":       (0.80, 1.30),
    "caution":       (1.30, 1.50),
    "danger":        (1.50, float("inf")),
}

FORCE_TYPES = ("push", "pull", "static")

MOVEMENT_PATTERNS = (
    "horizontal_push", "horizontal_pull",
    "vertical_push", "vertical_pull",
    "squat", "hinge", "lunge", "carry",
    "rotation", "anti_rotation",
    "flexion", "extension",
    "isolation", "abduction", "adduction",
)

EXERCISE_TYPES = ("compound", "isolation", "isometric")

C1_FORCE_ANALOGS = (
    "top_arm_push",
    "bottom_arm_pull",
    "trunk_rotation",
    "hip_drive",
    "stabilization",
)

# Seed data for muscle_groups table.
# (name, label, is_front)
MUSCLE_GROUPS_SEED: list[tuple[str, str, bool]] = [
    ("chest",        "Chest",        True),
    ("back",         "Back",         False),
    ("shoulders",    "Shoulders",    True),
    ("biceps",       "Biceps",       True),
    ("triceps",      "Triceps",      False),
    ("forearms",     "Forearms",     True),
    ("core",         "Core",         True),
    ("quadriceps",   "Quadriceps",   True),
    ("hamstrings",   "Hamstrings",   False),
    ("glutes",       "Glutes",       False),
    ("calves",       "Calves",       False),
    ("hip_flexors",  "Hip Flexors",  True),
    ("adductors",    "Adductors",    True),
    ("abductors",    "Abductors",    False),
    ("neck",         "Neck",         True),
]

# Seed data for muscles table.
# (muscle_group_name, muscle_name, muscle_label, c1_relevance 0-5)
MUSCLES_SEED: list[tuple[str, str, str, int]] = [
    ("chest",      "pectoralis_major",          "Pectoralis Major",           3),
    ("chest",      "pectoralis_minor",          "Pectoralis Minor",           2),
    ("back",       "latissimus_dorsi",          "Latissimus Dorsi",           5),
    ("back",       "trapezius",                 "Trapezius",                  3),
    ("back",       "rhomboids",                 "Rhomboids",                  3),
    ("back",       "erector_spinae",            "Erector Spinae",             4),
    ("back",       "teres_major",               "Teres Major",                3),
    ("shoulders",  "anterior_deltoid",          "Anterior Deltoid",           4),
    ("shoulders",  "lateral_deltoid",           "Lateral Deltoid",            2),
    ("shoulders",  "posterior_deltoid",         "Posterior Deltoid",           3),
    ("shoulders",  "rotator_cuff",             "Rotator Cuff",                4),
    ("biceps",     "biceps_brachii",            "Biceps Brachii",             4),
    ("biceps",     "brachialis",                "Brachialis",                  2),
    ("triceps",    "triceps_brachii",           "Triceps Brachii",            4),
    ("forearms",   "wrist_flexors",             "Wrist Flexors",              3),
    ("forearms",   "wrist_extensors",           "Wrist Extensors",            2),
    ("forearms",   "brachioradialis",           "Brachioradialis",            2),
    ("core",       "rectus_abdominis",          "Rectus Abdominis",           5),
    ("core",       "external_obliques",         "External Obliques",          5),
    ("core",       "internal_obliques",         "Internal Obliques",          4),
    ("core",       "transverse_abdominis",      "Transverse Abdominis",       3),
    ("quadriceps", "rectus_femoris",            "Rectus Femoris",             2),
    ("quadriceps", "vastus_lateralis",          "Vastus Lateralis",           1),
    ("quadriceps", "vastus_medialis",           "Vastus Medialis",            1),
    ("hamstrings", "biceps_femoris",            "Biceps Femoris",             1),
    ("hamstrings", "semitendinosus",            "Semitendinosus",             1),
    ("glutes",     "gluteus_maximus",           "Gluteus Maximus",            2),
    ("glutes",     "gluteus_medius",            "Gluteus Medius",             2),
    ("calves",     "gastrocnemius",             "Gastrocnemius",              1),
    ("calves",     "soleus",                    "Soleus",                     1),
    ("hip_flexors","iliopsoas",                 "Iliopsoas",                  4),
    ("adductors",  "hip_adductors",             "Hip Adductors",              1),
    ("abductors",  "hip_abductors",             "Hip Abductors",              1),
    ("neck",       "sternocleidomastoid",       "Sternocleidomastoid",        1),
]

# Maps the informal muscle names from yuhonas/free-exercise-db
# to the canonical muscle name in our schema.
YUHONAS_MUSCLE_MAP: dict[str, str] = {
    "abdominals":   "rectus_abdominis",
    "abductors":    "hip_abductors",
    "adductors":    "hip_adductors",
    "biceps":       "biceps_brachii",
    "calves":       "gastrocnemius",
    "chest":        "pectoralis_major",
    "forearms":     "wrist_flexors",
    "glutes":       "gluteus_maximus",
    "hamstrings":   "biceps_femoris",
    "lats":         "latissimus_dorsi",
    "lower back":   "erector_spinae",
    "middle back":  "rhomboids",
    "neck":         "sternocleidomastoid",
    "quadriceps":   "rectus_femoris",
    "shoulders":    "anterior_deltoid",
    "traps":        "trapezius",
    "triceps":      "triceps_brachii",
}

# C1 enrichment overlay: exercise names (lowered) → extra metadata.
# Applied on top of the yuhonas base data during seeding.
C1_ENRICHMENT: dict[str, dict] = {
    "barbell bench press": {
        "movement_pattern": "horizontal_push",
        "c1_relevance": 4,
        "c1_force_analog": "top_arm_push",
    },
    "dumbbell bench press": {
        "movement_pattern": "horizontal_push",
        "c1_relevance": 3,
        "c1_force_analog": "top_arm_push",
    },
    "incline barbell bench press": {
        "movement_pattern": "horizontal_push",
        "c1_relevance": 4,
        "c1_force_analog": "top_arm_push",
    },
    "incline dumbbell bench press": {
        "movement_pattern": "horizontal_push",
        "c1_relevance": 3,
        "c1_force_analog": "top_arm_push",
    },
    "flat bench press": {
        "movement_pattern": "horizontal_push",
        "c1_relevance": 4,
        "c1_force_analog": "top_arm_push",
    },
    "seated cable rows": {
        "movement_pattern": "horizontal_pull",
        "c1_relevance": 5,
        "c1_force_analog": "bottom_arm_pull",
    },
    "bent over barbell row": {
        "movement_pattern": "horizontal_pull",
        "c1_relevance": 5,
        "c1_force_analog": "bottom_arm_pull",
    },
    "seated row": {
        "movement_pattern": "horizontal_pull",
        "c1_relevance": 5,
        "c1_force_analog": "bottom_arm_pull",
    },
    "one-arm dumbbell row": {
        "movement_pattern": "horizontal_pull",
        "c1_relevance": 4,
        "c1_force_analog": "bottom_arm_pull",
    },
    "t-bar row": {
        "movement_pattern": "horizontal_pull",
        "c1_relevance": 4,
        "c1_force_analog": "bottom_arm_pull",
    },
    "lat pulldown": {
        "movement_pattern": "vertical_pull",
        "c1_relevance": 5,
        "c1_force_analog": "bottom_arm_pull",
    },
    "wide-grip lat pulldown": {
        "movement_pattern": "vertical_pull",
        "c1_relevance": 5,
        "c1_force_analog": "bottom_arm_pull",
    },
    "pullups": {
        "movement_pattern": "vertical_pull",
        "c1_relevance": 5,
        "c1_force_analog": "bottom_arm_pull",
    },
    "chin-up": {
        "movement_pattern": "vertical_pull",
        "c1_relevance": 4,
        "c1_force_analog": "bottom_arm_pull",
    },
    "standing military press": {
        "movement_pattern": "vertical_push",
        "c1_relevance": 4,
        "c1_force_analog": "top_arm_push",
    },
    "dumbbell shoulder press": {
        "movement_pattern": "vertical_push",
        "c1_relevance": 4,
        "c1_force_analog": "top_arm_push",
    },
    "seated dumbbell press": {
        "movement_pattern": "vertical_push",
        "c1_relevance": 4,
        "c1_force_analog": "top_arm_push",
    },
    "arnold dumbbell press": {
        "movement_pattern": "vertical_push",
        "c1_relevance": 3,
        "c1_force_analog": "top_arm_push",
    },
    "cable woodchoppers": {
        "movement_pattern": "rotation",
        "c1_relevance": 5,
        "c1_force_analog": "trunk_rotation",
    },
    "russian twist": {
        "movement_pattern": "rotation",
        "c1_relevance": 5,
        "c1_force_analog": "trunk_rotation",
    },
    "pallof press": {
        "movement_pattern": "anti_rotation",
        "c1_relevance": 5,
        "c1_force_analog": "trunk_rotation",
    },
    "landmine twist": {
        "movement_pattern": "rotation",
        "c1_relevance": 5,
        "c1_force_analog": "trunk_rotation",
    },
    "barbell deadlift": {
        "movement_pattern": "hinge",
        "c1_relevance": 3,
        "c1_force_analog": "hip_drive",
    },
    "barbell squat": {
        "movement_pattern": "squat",
        "c1_relevance": 2,
        "c1_force_analog": "hip_drive",
    },
    "barbell hip thrust": {
        "movement_pattern": "hinge",
        "c1_relevance": 3,
        "c1_force_analog": "hip_drive",
    },
    "plank": {
        "movement_pattern": "anti_rotation",
        "c1_relevance": 4,
        "c1_force_analog": "stabilization",
    },
    "dead bug": {
        "movement_pattern": "anti_rotation",
        "c1_relevance": 4,
        "c1_force_analog": "stabilization",
    },
    "face pull": {
        "movement_pattern": "horizontal_pull",
        "c1_relevance": 3,
        "c1_force_analog": "stabilization",
    },
    "reverse flyes": {
        "movement_pattern": "horizontal_pull",
        "c1_relevance": 3,
        "c1_force_analog": "stabilization",
    },
    "hammer curls": {
        "movement_pattern": "flexion",
        "c1_relevance": 2,
        "c1_force_analog": "bottom_arm_pull",
    },
    "barbell curl": {
        "movement_pattern": "flexion",
        "c1_relevance": 2,
        "c1_force_analog": "bottom_arm_pull",
    },
    "tricep pushdown": {
        "movement_pattern": "extension",
        "c1_relevance": 2,
        "c1_force_analog": "top_arm_push",
    },
    "triceps pushdown - rope attachment": {
        "movement_pattern": "extension",
        "c1_relevance": 2,
        "c1_force_analog": "top_arm_push",
    },
}
