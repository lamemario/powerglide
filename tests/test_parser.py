"""Unit tests for powerglide.core.parser (parse_gym_log, expand_quick_sets)."""

from datetime import date

from powerglide.core.parser import parse_gym_log


RAW_NOTE = """
19/02/26
Incline Barbell Bench [feet up]
50 x 8,8,8
Lat Pulldown
63x8, 58.9x8
"""


class TestParseGymLog:
    """Tests for parse_gym_log with raw note format."""

    def test_parses_single_session_date(self) -> None:
        sessions = parse_gym_log(RAW_NOTE)
        assert len(sessions) == 1
        assert sessions[0].session_date == date(2026, 2, 19)

    def test_parses_exercises_and_names(self) -> None:
        sessions = parse_gym_log(RAW_NOTE)
        exs = sessions[0].exercises
        assert len(exs) >= 2
        assert exs[0].name == "Incline Barbell Bench"
        assert exs[1].name == "Lat Pulldown"

    def test_parses_tags(self) -> None:
        sessions = parse_gym_log(RAW_NOTE)
        assert "feet up" in sessions[0].exercises[0].tags

    def test_parses_uniform_weight_sets(self) -> None:
        sessions = parse_gym_log(RAW_NOTE)
        bench = sessions[0].exercises[0]
        assert len(bench.sets) == 3
        for s in bench.sets:
            assert s.weight_kg == 50.0
            assert s.reps == 8

    def test_parses_varying_weight_sets(self) -> None:
        sessions = parse_gym_log(RAW_NOTE)
        lat = sessions[0].exercises[1]
        assert len(lat.sets) == 2
        assert lat.sets[0].weight_kg == 63.0
        assert lat.sets[0].reps == 8
        assert lat.sets[1].weight_kg == 58.9
        assert lat.sets[1].reps == 8

    def test_dnf_recorded_as_zero_weight_reps_is_dnf_true(self) -> None:
        """DNF in a set line is recorded as 0 weight, 0 reps, is_dnf=True."""
        raw = """
19/02/26
Bench Press
50 x 5
dnf
"""
        sessions = parse_gym_log(raw)
        assert len(sessions) == 1
        assert len(sessions[0].exercises) == 1
        bench = sessions[0].exercises[0]
        assert len(bench.sets) == 2
        assert bench.sets[0].weight_kg == 50.0 and bench.sets[0].reps == 5
        assert bench.sets[1].weight_kg == 0 and bench.sets[1].reps == 0
        assert bench.sets[1].is_dnf is True

    def test_mobile_artifacts_smart_quotes_and_dashes(self) -> None:
        """Parser handles smart quotes and non-ASCII hyphens without crashing."""
        # Smart quotes normalized to ASCII; parser succeeds and sets parse correctly
        raw = "19/02/26\n\u201cBench Press\u201d\n50 x 8,8"
        sessions = parse_gym_log(raw)
        assert len(sessions) == 1
        assert sessions[0].exercises[0].name == "Bench Press"
        assert len(sessions[0].exercises[0].sets) == 2
        assert sessions[0].exercises[0].sets[0].weight_kg == 50.0

    def test_mobile_artifacts_emojis_stripped(self) -> None:
        """Parser strips emojis and does not crash."""
        raw = "19/02/26\nIncline Bench \U0001f4aa\n50 x 8,8"
        sessions = parse_gym_log(raw)
        assert len(sessions) == 1
        assert "Incline Bench" in sessions[0].exercises[0].name
        assert len(sessions[0].exercises[0].sets) == 2

    def test_parses_time_based_uniform_sets(self) -> None:
        """Parser correctly parses the 's' suffix to time_seconds and sets reps to 0."""
        raw = "19/02/26\nPlank\n0 x 60s, 45s, 30s"
        sessions = parse_gym_log(raw)
        sets = sessions[0].exercises[0].sets
        assert len(sets) == 3
        # First set
        assert sets[0].weight_kg == 0.0
        assert sets[0].reps == 0
        assert sets[0].time_seconds == 60
        # Second set
        assert sets[1].time_seconds == 45
        # Third set
        assert sets[2].time_seconds == 30

    def test_parses_time_based_varying_pairs(self) -> None:
        raw = "19/02/26\nWeighted Plank\n10kg x 60s, 15kg x 45s"
        sessions = parse_gym_log(raw)
        sets = sessions[0].exercises[0].sets
        assert len(sets) == 2
        assert sets[0].weight_kg == 10.0
        assert sets[0].time_seconds == 60
        assert sets[0].reps == 0
        assert sets[1].weight_kg == 15.0
        assert sets[1].time_seconds == 45
        assert sets[1].reps == 0

    def test_parses_time_based_bodyweight(self) -> None:
        raw = "19/02/26\nPlank\n60s, 60s"
        sets = parse_gym_log(raw)[0].exercises[0].sets
        assert len(sets) == 2
        assert sets[0].weight_kg == 0
        assert sets[0].time_seconds == 60
        assert sets[1].time_seconds == 60

    def test_parses_single_time_bodyweight(self) -> None:
        raw = "19/02/26\nPlank\n60s"
        sets = parse_gym_log(raw)[0].exercises[0].sets
        assert len(sets) == 1
        assert sets[0].weight_kg == 0
        assert sets[0].reps == 0
        assert sets[0].time_seconds == 60

    def test_failsafe_rejects_absurd_input(self) -> None:
        raw = "19/02/26\nPlank\n10kg x 60s x 10" # weight x time x reps is nonsense
        session = parse_gym_log(raw)[0]
        assert len(session.errors) == 1
        assert "couldn't be parsed" in session.errors[0].message

from powerglide.core.parser import expand_quick_sets

class TestExpandQuickSets:
    def test_multiplier_regex_collision(self) -> None:
        """3x60s should expand to 3 sets of 60 seconds (reps=0), NOT reps=60s."""
        sets = expand_quick_sets("3x60s")
        assert not isinstance(sets, str)
        assert len(sets) == 3
        for s in sets:
            assert s.reps == 0
            assert s.time_seconds == 60

    def test_time_varying_pairs(self) -> None:
        sets = expand_quick_sets("10x60s, 20x45s")
        assert not isinstance(sets, str)
        assert len(sets) == 2
        assert sets[0].weight_kg == 10.0
        assert sets[0].time_seconds == 60
        assert sets[1].weight_kg == 20.0
        assert sets[1].time_seconds == 45
