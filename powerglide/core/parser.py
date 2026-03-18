"""
Stateful line-by-line parser for PowerGlide shorthand gym/water logs.

Gym format
----------
DD/MM/YY [Xmin] [@RPE]

Exercise Name [tag1, tag2]
weight x r1,r2,r3,r4 [@RPE] [// note]
  or
w1xr1, w2xr2, w3xr3 [@RPE] [// note]
  or
r1,r2,r3,r4  (bodyweight, weight = 0)

Water format
------------
DD/MM/YY [Xmin] [@RPE] [wind] [condition]

dist time [Xspm] [@RPE]
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date


# ---------------------------------------------------------------------------
# Data classes for parse results
# ---------------------------------------------------------------------------

@dataclass
class ParsedSet:
    weight_kg: float
    reps: int
    rpe: int | None = None
    note: str | None = None
    is_dnf: bool = False
    time_seconds: int | None = None


@dataclass
class ParsedExercise:
    name: str
    tags: list[str] = field(default_factory=list)
    sets: list[ParsedSet] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass
class ParsedSession:
    session_date: date
    session_type: str = "gym"
    duration_minutes: int | None = None
    session_rpe: int | None = None
    wind_condition: str | None = None
    water_condition: str | None = None
    exercises: list[ParsedExercise] = field(default_factory=list)
    errors: list[ParseError] = field(default_factory=list)
    warnings: list[ParseWarning] = field(default_factory=list)


@dataclass
class ParseError:
    line_number: int
    line_content: str
    message: str
    suggestion: str | None = None


@dataclass
class ParseWarning:
    line_number: int
    line_content: str
    message: str


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

_DATE_RE = re.compile(
    r"^\s*(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})"
    r"(?:\s+(\d+)\s*min)?"
    r"(?:\s+@\s*(\d+))?"
    r"(?:\s+(headwind|tailwind|crosswind|none))?"
    r"(?:\s+(calm|choppy|wavy))?"
    r"\s*$",
    re.IGNORECASE,
)

_TAGS_RE = re.compile(r"\[([^\]]+)\]")

_UNIFORM_SET_RE = re.compile(
    r"^\s*(\d+\.?\d*)\s*(?:kg)?\s*x\s*"
    r"(\d+s?(?:\s*,\s*\d+s?)*)"
    r"(?:\s*@\s*(\d+))?"
    r"(?:\s*//\s*(.*))?$",
    re.IGNORECASE,
)

_VARYING_PAIR_RE = re.compile(
    r"(\d+\.?\d*)\s*(?:kg)?\s*x\s*(\d+)(s)?(?:\s*@\s*(\d+))?",
    re.IGNORECASE,
)

_BODYWEIGHT_REPS_RE = re.compile(
    r"^\s*(\d+s?(?:\s*,\s*\d+s?)+)\s*(?:@\s*(\d+))?\s*(?://\s*(.*))?$",
    re.IGNORECASE,
)

_SINGLE_TIME_RE = re.compile(
    r"^\s*(\d+)s\s*(?:@\s*(\d+))?\s*(?://\s*(.*))?$",
    re.IGNORECASE,
)

_DNF_RE = re.compile(r"^\s*dnf\s*$", re.IGNORECASE)

_EXERCISE_NUMBER_PREFIX_RE = re.compile(r"^\s*\d+[a-z]?\s*[.)]\s*")

_COMMENT_RE = re.compile(r"^\s*(#|//)")

# Mobile/paste artifacts: smart quotes, non-ASCII dashes, emoji (remove so parsing doesn't crash).
_SMART_QUOTE_MAP = str.maketrans({"\u201c": '"', "\u201d": '"', "\u2018": "'", "\u2019": "'"})
_EMOJI_PATTERN = re.compile(
    "[\U0001F300-\U0001F9FF\U0001FA00-\U0001FAFF\U00002702-\U000027B0\U0001F000-\U0001F02F]",
    re.UNICODE,
)


def _normalize_mobile_artifacts(s: str) -> str:
    """Replace smart quotes/dashes and strip emojis so pasted phone notes parse reliably."""
    s = s.translate(_SMART_QUOTE_MAP)
    s = s.replace("\u2013", "-").replace("\u2014", "-")
    return _EMOJI_PATTERN.sub("", s)


# ---------------------------------------------------------------------------
# Main parse function
# ---------------------------------------------------------------------------

def parse_gym_log(text: str) -> list[ParsedSession]:
    """
    Parse a multi-session gym log from raw text (e.g. pasted from phone notes).
    Normalizes smart quotes, en/em dashes, and strips emojis so mobile paste doesn't break parsing.
    Returns a list of ParsedSession objects, one per date header found.
    """
    lines = text.splitlines()
    sessions: list[ParsedSession] = []
    current_session: ParsedSession | None = None
    current_exercise: ParsedExercise | None = None

    for line_num, raw_line in enumerate(lines, start=1):
        line = _normalize_mobile_artifacts(raw_line.strip())

        if not line or _COMMENT_RE.match(line):
            if current_exercise and current_exercise.sets:
                current_exercise = None
            continue

        date_match = _DATE_RE.match(line)
        if date_match:
            if current_session:
                _finalize_exercise(current_session, current_exercise)
                sessions.append(current_session)

            parsed_date = _parse_date(date_match, line_num, line)
            if isinstance(parsed_date, ParseError):
                if current_session:
                    current_session.errors.append(parsed_date)
                else:
                    sessions.append(ParsedSession(
                        session_date=date.today(),
                        errors=[parsed_date],
                    ))
                continue

            current_session = ParsedSession(
                session_date=parsed_date,
                duration_minutes=int(date_match.group(4)) if date_match.group(4) else None,
                session_rpe=int(date_match.group(5)) if date_match.group(5) else None,
                wind_condition=date_match.group(6),
                water_condition=date_match.group(7),
            )
            current_exercise = None
            continue

        if current_session is None:
            current_session = ParsedSession(
                session_date=date.today(),
                warnings=[ParseWarning(line_num, line, "No date header found. Using today's date.")],
            )

        set_result = _try_parse_set_line(line, line_num)
        if set_result is not None:
            if isinstance(set_result, ParseError):
                current_session.errors.append(set_result)
                continue

            if current_exercise is None:
                current_session.errors.append(ParseError(
                    line_num, line,
                    "Set data found but no exercise name precedes it.",
                    "Add an exercise name line before the set data.",
                ))
                continue

            current_exercise.sets.extend(set_result)
            continue

        _finalize_exercise(current_session, current_exercise)
        current_exercise = _parse_exercise_line(line, line_num)
        current_session.exercises.append(current_exercise)

    if current_session:
        _finalize_exercise(current_session, current_exercise)
        sessions.append(current_session)

    return sessions


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _finalize_exercise(session: ParsedSession, exercise: ParsedExercise | None) -> None:
    """Emit a warning if an exercise has zero sets."""
    if exercise is not None and not exercise.sets:
        session.warnings.append(ParseWarning(
            0, exercise.name,
            f"Exercise '{exercise.name}' has no sets logged.",
        ))


def _parse_date(match: re.Match, line_num: int, line: str) -> date | ParseError:
    day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
    if year < 100:
        year += 2000
    try:
        return date(year, month, day)
    except ValueError:
        return ParseError(
            line_num, line,
            f"Invalid date: day={day}, month={month}, year={year}.",
            "Use DD/MM/YY format (e.g. 21/02/26).",
        )


def _parse_exercise_line(line: str, line_num: int) -> ParsedExercise:
    cleaned = _EXERCISE_NUMBER_PREFIX_RE.sub("", line)

    tags: list[str] = []
    tag_match = _TAGS_RE.search(cleaned)
    if tag_match:
        raw_tags = tag_match.group(1)
        tags = [t.strip() for t in raw_tags.split(",") if t.strip()]
        cleaned = _TAGS_RE.sub("", cleaned).strip()

    paren_tags = re.findall(r"\(([^)]+)\)", cleaned)
    for pt in paren_tags:
        lower = pt.lower().strip()
        is_tag = any(kw in lower for kw in (
            "feet up", "wide grip", "close grip", "narrow grip", "v grip",
            "v-grip", "rope", "bar", "ez bar", "overhand", "underhand",
            "two arms", "single arm", "seated", "standing", "incline",
            "decline", "pause", "tempo", "slow",
        ))
        if is_tag:
            tags.append(lower)
            cleaned = cleaned.replace(f"({pt})", "").strip()

    name = re.sub(r"\s+", " ", cleaned).strip()
    name = name.rstrip(":-").strip()
    name = name.strip('"').strip("'").strip()  # mobile smart-quotes often become ASCII quotes

    return ParsedExercise(name=name, tags=tags)


def _try_parse_set_line(
    line: str, line_num: int
) -> list[ParsedSet] | ParseError | None:
    """
    Try to parse a line as set data. Returns:
    - list[ParsedSet] on success
    - ParseError if the line looks like set data but is malformed
    - None if the line is not set data at all
    """
    if _DNF_RE.match(line):
        return [ParsedSet(weight_kg=0, reps=0, is_dnf=True)]

    inline_note: str | None = None
    if "//" in line:
        line, _, inline_note = line.partition("//")
        line = line.strip()
        inline_note = inline_note.strip()

    rpe_from_line: int | None = None
    rpe_match = re.search(r"@\s*(\d+)\s*$", line)
    if rpe_match:
        rpe_from_line = int(rpe_match.group(1))
        line = line[:rpe_match.start()].strip()

    uniform_match = _UNIFORM_SET_RE.match(line)
    if uniform_match:
        weight = float(uniform_match.group(1))
        rpe = int(uniform_match.group(3)) if uniform_match.group(3) else rpe_from_line
        note = uniform_match.group(4) or inline_note
        sets = []
        for r_raw in uniform_match.group(2).split(","):
            r_str = r_raw.strip().lower()
            if r_str.endswith("s"):
                sets.append(ParsedSet(weight_kg=weight, reps=0, rpe=rpe, note=note, time_seconds=int(r_str[:-1])))
            else:
                sets.append(ParsedSet(weight_kg=weight, reps=int(r_str), rpe=rpe, note=note))
        return sets

    varying_pairs = _VARYING_PAIR_RE.findall(line)
    if len(varying_pairs) >= 2:
        sets: list[ParsedSet] = []
        for weight_s, val_s, is_time_s, rpe_s in varying_pairs:
            rpe = int(rpe_s) if rpe_s else rpe_from_line
            if is_time_s:
                sets.append(ParsedSet(
                    weight_kg=float(weight_s),
                    reps=0,
                    rpe=rpe,
                    note=inline_note,
                    time_seconds=int(val_s)
                ))
            else:
                sets.append(ParsedSet(
                    weight_kg=float(weight_s),
                    reps=int(val_s),
                    rpe=rpe,
                    note=inline_note,
                ))
        return sets

    bw_match = _BODYWEIGHT_REPS_RE.match(line)
    if bw_match:
        rpe = int(bw_match.group(2)) if bw_match.group(2) else rpe_from_line
        note = bw_match.group(3) or inline_note
        sets = []
        for r_raw in bw_match.group(1).split(","):
            r_str = r_raw.strip().lower()
            if r_str.endswith("s"):
                sets.append(ParsedSet(weight_kg=0.0, reps=0, rpe=rpe, note=note, time_seconds=int(r_str[:-1])))
            else:
                sets.append(ParsedSet(weight_kg=0.0, reps=int(r_str), rpe=rpe, note=note))
        return sets

    single_time_match = _SINGLE_TIME_RE.match(line)
    if single_time_match:
        time_s = int(single_time_match.group(1))
        rpe = int(single_time_match.group(2)) if single_time_match.group(2) else rpe_from_line
        note = single_time_match.group(3) or inline_note
        return [ParsedSet(weight_kg=0.0, reps=0, rpe=rpe, note=note, time_seconds=time_s)]

    if re.search(r"\d", line) and ("x" in line.lower() or "," in line):
        return ParseError(
            line_num, line,
            "This looks like set data but couldn't be parsed.",
            "Use: 'weight x r1,r2,r3' or 'w1xr1, w2xr2, w3xr3' or just 'r1,r2,r3' for bodyweight.",
        )

    return None


# ---------------------------------------------------------------------------
# Water log parser
# ---------------------------------------------------------------------------

_WATER_PIECE_RE = re.compile(
    r"^\s*(\d+)\s*(?:m)?\s+"
    r"(\d+):(\d{2}(?:\.\d+)?)\s*"
    r"(?:(\d+)\s*spm)?\s*"
    r"(?:@\s*(\d+))?\s*"
    r"(?://\s*(.*))?$",
    re.IGNORECASE,
)


def parse_water_log(text: str) -> list[ParsedSession]:
    """Parse multi-session water log from raw text."""
    lines = text.splitlines()
    sessions: list[ParsedSession] = []
    current_session: ParsedSession | None = None
    piece_order = 0

    for line_num, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()

        if not line or _COMMENT_RE.match(line):
            continue

        date_match = _DATE_RE.match(line)
        if date_match:
            if current_session:
                sessions.append(current_session)

            parsed_date = _parse_date(date_match, line_num, line)
            if isinstance(parsed_date, ParseError):
                err_session = ParsedSession(session_date=date.today(), session_type="water")
                err_session.errors.append(parsed_date)
                sessions.append(err_session)
                continue

            current_session = ParsedSession(
                session_date=parsed_date,
                session_type="water",
                duration_minutes=int(date_match.group(4)) if date_match.group(4) else None,
                session_rpe=int(date_match.group(5)) if date_match.group(5) else None,
                wind_condition=date_match.group(6),
                water_condition=date_match.group(7),
            )
            piece_order = 0
            continue

        if current_session is None:
            current_session = ParsedSession(
                session_date=date.today(),
                session_type="water",
                warnings=[ParseWarning(line_num, line, "No date header. Using today.")],
            )

        piece_match = _WATER_PIECE_RE.match(line)
        if piece_match:
            piece_order += 1
            dist = int(piece_match.group(1))
            minutes = int(piece_match.group(2))
            seconds = float(piece_match.group(3))
            time_s = minutes * 60.0 + seconds
            spm = float(piece_match.group(4)) if piece_match.group(4) else None
            rpe = int(piece_match.group(5)) if piece_match.group(5) else None
            note = piece_match.group(6)

            ex = ParsedExercise(
                name=f"{dist}m",
                tags=[],
                sets=[ParsedSet(weight_kg=dist, reps=piece_order, rpe=rpe, note=note)],
            )
            ex._water_data = {  # type: ignore[attr-defined]
                "distance_m": dist,
                "time_seconds": time_s,
                "avg_spm": spm,
                "piece_rpe": rpe,
                "piece_order": piece_order,
                "notes": note,
            }
            current_session.exercises.append(ex)
        else:
            current_session.warnings.append(ParseWarning(
                line_num, line,
                "Could not parse water piece. Expected: 'distance time [Xspm] [@RPE]' "
                "(e.g. '500 2:15 45spm @8').",
            ))

    if current_session:
        sessions.append(current_session)

    return sessions


# ---------------------------------------------------------------------------
# CLI quick-log helpers
# ---------------------------------------------------------------------------

_QUICK_SETS_RE = re.compile(r"^(\d+)\s*x\s*(\d+)(s)?$", re.IGNORECASE)


def expand_quick_sets(sets_str: str) -> list[ParsedSet] | str:
    """
    Parse quick-log set notation.
    '4x8'       → 4 sets of 8 reps
    '3x60s'     → 3 sets of 60 seconds
    '50x8,60x8' → varying-weight sets
    '8,8,8,8'   → bodyweight reps
    '60s,45s'   → bodyweight time sets
    Returns list of ParsedSet (weight_kg=0 as placeholder) or error string.
    """
    sets_str = sets_str.strip()

    quick_match = _QUICK_SETS_RE.match(sets_str)
    if quick_match:
        n_sets = int(quick_match.group(1))
        val = int(quick_match.group(2))
        is_time = bool(quick_match.group(3))
        if n_sets > 20:
            return f"Suspiciously high set count ({n_sets}). Did you mean {val}x{n_sets}?"
        if is_time:
            return [ParsedSet(weight_kg=0, reps=0, time_seconds=val) for _ in range(n_sets)]
        else:
            return [ParsedSet(weight_kg=0, reps=val) for _ in range(n_sets)]

    pairs = _VARYING_PAIR_RE.findall(sets_str)
    if pairs:
        sets = []
        for w, r, is_time, rp in pairs:
            if is_time:
                sets.append(ParsedSet(weight_kg=float(w), reps=0, time_seconds=int(r), rpe=int(rp) if rp else None))
            else:
                sets.append(ParsedSet(weight_kg=float(w), reps=int(r), rpe=int(rp) if rp else None))
        return sets

    parts = [p.strip().lower() for p in sets_str.split(",")]
    if all(p.isdigit() or (p.endswith("s") and p[:-1].isdigit()) for p in parts):
        sets = []
        for p in parts:
            if p.endswith("s"):
                sets.append(ParsedSet(weight_kg=0, reps=0, time_seconds=int(p[:-1])))
            else:
                sets.append(ParsedSet(weight_kg=0, reps=int(p)))
        return sets

    return (
        f"Could not parse '{sets_str}'. "
        "Use: '4x8' (4 sets of 8), '50x8,60x8' (varying), or '8,8,8' (bodyweight)."
    )
