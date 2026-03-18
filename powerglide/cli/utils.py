"""Shared CLI helpers — exercise selection, prompts, etc."""

from __future__ import annotations

import sqlite3
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

console = Console()


def select_exercise_interactively(
    conn: sqlite3.Connection,
    query: str,
    threshold: int = 50,
    limit: int = 5,
    allow_skip: bool = False,
) -> Optional[dict]:
    """
    Run fuzzy match on query, show choices in a Rich table, prompt user.
    Returns selected exercise dict, or None if allow_skip and user chose skip.
    Raises typer.Exit(0) on cancel, typer.Exit(1) on no matches or invalid choice.
    """
    from powerglide.database.queries_exercises import fuzzy_match_exercise

    matches = fuzzy_match_exercise(conn, query, threshold=threshold, limit=limit)
    if not matches:
        console.print(f"[red]No exercise matching '{query}' found.[/red]")
        console.print("[dim]Tip: Run 'powerglide seed' first to populate the exercise database.[/dim]")
        raise typer.Exit(1)

    table = Table(title=f"'{query}' not found — pick a match")
    table.add_column("#", style="dim", width=3)
    table.add_column("Exercise", style="cyan")
    table.add_column("Score", justify="right", style="green")
    table.add_column("Force", style="yellow")
    table.add_column("Type", style="magenta")
    for i, (row, score) in enumerate(matches, 1):
        table.add_row(
            str(i),
            row["name"],
            str(score),
            row.get("force_type") or "—",
            row.get("exercise_type") or "—",
        )
    console.print(table)

    skip_hint = " or 's' to skip" if allow_skip else " or 'q' to cancel"
    choice = typer.prompt(f"Select [1-{limit}]{skip_hint}", default="1")
    choice_lower = choice.strip().lower()

    if choice_lower == "q":
        if allow_skip:
            return None
        console.print("[dim]Cancelled.[/dim]")
        raise typer.Exit(0)
    if allow_skip and choice_lower == "s":
        return None

    try:
        idx = int(choice)
        if 1 <= idx <= len(matches):
            return matches[idx - 1][0]
    except ValueError:
        pass
    console.print("[red]Invalid choice.[/red]")
    raise typer.Exit(1)
