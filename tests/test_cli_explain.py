"""Integration tests for the 'explain' CLI commands."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

pytest.importorskip("typer", reason="typer required for CLI tests")

from typer.testing import CliRunner

from powerglide.cli.main import app
from powerglide.database.db import init_db

runner = CliRunner()

# In-memory DB for CLI testing.
@pytest.fixture
def mock_conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    init_db(conn)
    return conn

def test_explain_1rm_cli() -> None:
    # weight=100, reps=5 -> Brzycki -> 112.5
    result = runner.invoke(app, ["explain", "1rm", "--weight", "100", "--reps", "5"])
    assert result.exit_code == 0
    assert "112.5 kg" in result.stdout
    assert "Brzycki" in result.stdout

def test_explain_1rm_invalid_cli() -> None:
    result = runner.invoke(app, ["explain", "1rm", "--weight", "0", "--reps", "5"])
    assert result.exit_code != 0
    assert "Invalid inputs" in result.stdout

def test_explain_acwr_no_data_cli() -> None:
    # Patch get_connection to return an empty in-memory DB.
    with patch("powerglide.cli.explain.get_connection") as mock_get:
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        init_db(conn)
        mock_get.return_value = conn
        
        result = runner.invoke(app, ["explain", "acwr"])
        assert result.exit_code == 0
        assert "ACWR Explanation" in result.stdout
        assert "Need at least 7 days" in result.stdout

def test_explain_fatigue_no_data_cli() -> None:
    with patch("powerglide.cli.explain.get_connection") as mock_get:
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        init_db(conn)
        mock_get.return_value = conn
        
        result = runner.invoke(app, ["explain", "fatigue", "--muscle", "Triceps"])
        assert result.exit_code != 0 # Should fail with 'No sets found'
        assert "No sets found for muscle matching 'Triceps'" in result.stdout

def test_explain_help_cli() -> None:
    # Testing the 'help' alias I added
    result = runner.invoke(app, ["explain", "help"])
    assert result.exit_code == 0
    assert "1rm" in result.stdout
    assert "acwr" in result.stdout
    assert "fatigue" in result.stdout
    assert "workout" in result.stdout

def test_explain_no_args_shows_help_cli() -> None:
    # Testing the callback showing help when no subcommand is provided
    result = runner.invoke(app, ["explain"])
    assert result.exit_code == 0
    assert "1rm" in result.stdout
    assert "acwr" in result.stdout
