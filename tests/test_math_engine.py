"""Unit tests for powerglide.core.math_engine."""

from datetime import date, timedelta

import pytest

from powerglide.core.math_engine import compute_ewma_acwr, estimate_1rm, explain_1rm


class TestEstimate1rm:
    """Tests for estimate_1rm (Brzycki reps 2-10, Epley reps > 10)."""

    def test_one_rep_returns_weight(self) -> None:
        assert estimate_1rm(100.0, 1) == 100.0
        assert estimate_1rm(87.5, 1) == 87.5

    def test_five_reps_brzycki(self) -> None:
        # Brzycki: weight * 36 / (37 - reps) = 100 * 36 / 32 = 112.5
        assert estimate_1rm(100.0, 5) == 112.5

    def test_ten_reps_brzycki(self) -> None:
        # 100 * 36 / (37 - 10) = 3600 / 27 ≈ 133.3
        assert estimate_1rm(100.0, 10) == 133.3

    def test_twelve_reps_epley(self) -> None:
        # Epley: weight * (1 + reps/30) = 100 * (1 + 12/30) = 100 * 1.4 = 140.0
        assert estimate_1rm(100.0, 12) == 140.0

    def test_invalid_reps_returns_none(self) -> None:
        assert estimate_1rm(100.0, 0) is None
        assert estimate_1rm(100.0, -1) is None

    def test_zero_weight_returns_none(self) -> None:
        assert estimate_1rm(0.0, 5) is None


class TestExplain1rm:
    """Tests for explain_1rm (formula metadata for transparency)."""

    def test_epley_for_twelve_reps(self) -> None:
        info = explain_1rm(120.0, 12)
        assert info is not None
        assert "Epley" in info["formula"]
        assert info["result"] == 168.0
        assert "120" in info["math"] and "12" in info["math"]

    def test_brzycki_for_five_reps(self) -> None:
        info = explain_1rm(100.0, 5)
        assert info is not None
        assert "Brzycki" in info["formula"]
        assert info["result"] == 112.5

    def test_invalid_returns_none(self) -> None:
        assert explain_1rm(0.0, 5) is None
        assert explain_1rm(100.0, 0) is None


class TestComputeEwmaAcwr:
    """Tests for compute_ewma_acwr (EWMA-based ACWR)."""

    def test_empty_loads_returns_empty(self) -> None:
        assert compute_ewma_acwr([]) == []

    def test_single_day_has_acwr_one(self) -> None:
        loads = [(date(2026, 1, 1), 100.0)]
        result = compute_ewma_acwr(loads, acute_window=7, chronic_window=28)
        assert len(result) == 1
        assert result[0]["date"] == date(2026, 1, 1)
        assert result[0]["acute"] == 100.0
        assert result[0]["chronic"] == 100.0
        assert result[0]["acwr"] == 1.0
        assert result[0]["mature"] is False

    def test_constant_load_acwr_converges_to_one(self) -> None:
        start = date(2026, 1, 1)
        loads = [(start + timedelta(days=i), 50.0) for i in range(35)]
        result = compute_ewma_acwr(loads, acute_window=7, chronic_window=28)
        assert len(result) == 35
        last = result[-1]
        assert last["mature"] is True
        assert 0.95 <= last["acwr"] <= 1.05
        assert last["zone"] == "optimal"
