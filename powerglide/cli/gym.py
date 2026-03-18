"""Gym logging CLI sub-commands."""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from powerglide.core.constants import BORG_CR10_TABLE

gym_app = typer.Typer(no_args_is_help=True)
console = Console()


@gym_app.command("log")
def gym_log(
    exercise: str = typer.Argument(..., help="Exercise name (fuzzy matched)."),
    weight: float = typer.Argument(..., help="Weight in kg."),
    sets_reps: str = typer.Argument(
        ..., help="Sets notation: '4x8' (4 sets of 8), '8,8,6', or time-based '3x60s'."
    ),
    rpe: Optional[int] = typer.Option(None, "--rpe", "-r", help="RPE (1-10). See 'powerglide rpe'."),
    tags: Optional[str] = typer.Option(
        None, "--tags", "-t", help="Comma-separated tags: 'feet up,paused'."
    ),
    date_str: Optional[str] = typer.Option(
        None, "--date", "-d",
        help="Session date (DD/MM/YY or YYYY-MM-DD). Defaults to today.",
    ),
) -> None:
    """Log gym sets for a single exercise (quick-entry). e.g. log "Bench Press" 50 4x8 [--rpe 8] or log "Plank" 0 3x60s."""
    from powerglide.core.parser import expand_quick_sets
    from powerglide.database.db import get_connection, init_db
    from powerglide.database.queries_gym import (
        add_gym_set,
        get_next_set_order,
        get_or_create_today_gym_session,
    )
    from powerglide.database.queries_exercises import get_exercise_by_name
    from powerglide.cli.utils import select_exercise_interactively

    parsed_sets = expand_quick_sets(sets_reps)
    if isinstance(parsed_sets, str):
        console.print(f"[red]{parsed_sets}[/red]")
        raise typer.Exit(1)

    conn = get_connection()
    init_db(conn)

    ex_row = get_exercise_by_name(conn, exercise)
    if ex_row is None:
        ex_row = select_exercise_interactively(conn, exercise, threshold=50, limit=5)

    session_date = _resolve_date(date_str)
    sid = get_or_create_today_gym_session(conn, session_date)
    set_order = get_next_set_order(conn, sid)

    tag_list = [t.strip() for t in tags.split(",")] if tags else None

    for s in parsed_sets:
        # Use per-set weight when notation includes it (e.g. 50x8,60x8); else use argument
        weight_kg = s.weight_kg if s.weight_kg > 0 else weight
        add_gym_set(
            conn,
            session_id=sid,
            exercise_id=ex_row["id"],
            set_order=set_order,
            weight_kg=weight_kg,
            reps=s.reps,
            rpe=s.rpe or rpe,
            tags=tag_list,
            time_seconds=s.time_seconds,
        )
        set_order += 1

    n = len(parsed_sets)
    console.print(
        f"[green]  [OK] {ex_row['name']}: {n} set(s) logged to session {session_date}.[/green]"
    )
    conn.close()


@gym_app.command("history")
def gym_history(
    limit: int = typer.Option(5, "--limit", "-n"),
    exercise_name: Optional[str] = typer.Option(None, "--exercise", "-e", help="Filter by exercise."),
) -> None:
    """View recent gym sessions and sets."""
    from powerglide.database.db import get_connection, init_db
    from powerglide.database.queries_gym import get_gym_sessions, get_gym_sets_for_session

    conn = get_connection()
    init_db(conn)
    sessions = get_gym_sessions(conn, limit=limit)

    if not sessions:
        console.print("[dim]No gym sessions found.[/dim]")
        conn.close()
        return

    for session in sessions:
        sets = get_gym_sets_for_session(conn, session["id"])

        if exercise_name:
            sets = [s for s in sets if exercise_name.lower() in s["exercise_name"].lower()]
            if not sets:
                continue

        header = f"{session['session_date']}"
        if session["duration_minutes"]:
            header += f"  |  {session['duration_minutes']}min"
        if session["session_rpe"]:
            header += f"  |  RPE {session['session_rpe']}"
        if session["srpe"]:
            header += f"  |  sRPE {session['srpe']:.0f}"
        
        header += f"  |  ID {session['id']}"

        table = Table(title=header, show_lines=False)
        table.add_column("Set ID", style="dim", width=6)
        table.add_column("#", style="dim", width=3)
        table.add_column("Exercise", style="cyan")
        table.add_column("Weight", style="green", justify="right")
        table.add_column("Reps", justify="right")
        table.add_column("e1RM", style="magenta", justify="right")
        table.add_column("Tags", style="yellow")

        for s in sets:
            import json as _json
            tags_display = ", ".join(_json.loads(s["tags"])) if s["tags"] else "-"
            table.add_row(
                f"set_{s['id']}",
                str(s["set_order"]),
                s["exercise_name"],
                f"{s['weight_kg']}kg",
                f"{s['time_seconds']}s" if (s["time_seconds"] is not None and s["reps"] == 0) else str(s["reps"]),
                f"{s['estimated_1rm']}kg" if s["estimated_1rm"] else "-",
                tags_display,
            )

        console.print(table)
        console.print()

    conn.close()


@gym_app.command("update")
def gym_update(
    session_id: int = typer.Argument(..., help="ID of the gym session to update."),
    duration: Optional[int] = typer.Option(None, "--duration", "-min", help="New duration in minutes."),
    rpe: Optional[int] = typer.Option(None, "--rpe", "-r", help="New session RPE (1-10)."),
) -> None:
    """Update a gym session's duration or RPE. e.g. update 4 --duration 60."""
    from powerglide.database.db import get_connection, init_db
    from powerglide.database.queries_gym import get_gym_session_by_id, update_gym_session

    if duration is None and rpe is None:
        console.print("[red]Provide either --duration or --rpe to update.[/red]")
        raise typer.Exit(1)

    conn = get_connection()
    init_db(conn)

    session = get_gym_session_by_id(conn, session_id)
    if not session:
        console.print(f"[red]Gym session {session_id} not found.[/red]")
        conn.close()
        raise typer.Exit(1)

    update_gym_session(conn, session_id, duration_minutes=duration, session_rpe=rpe)
    
    parts = []
    if duration is not None:
        parts.append(f"duration={duration}min")
    if rpe is not None:
        parts.append(f"RPE={rpe}")

    console.print(f"[green]  [OK] Updated session {session_id} ({session['session_date']}): {', '.join(parts)}.[/green]")
    conn.close()


@gym_app.command("delete")
def gym_delete(
    session_id: Optional[int] = typer.Option(None, "--session", "-s", help="Delete an entire gym session by ID."),
    set_id: Optional[int] = typer.Option(None, "--set", help="Delete a single set by ID."),
    all_data: bool = typer.Option(False, "--all", help="Delete ALL gym sessions and sets."),
) -> None:
    """Delete gym sessions, individual sets, or all gym data."""
    from powerglide.database.db import get_connection, init_db
    from powerglide.database.queries_gym import (
        delete_all_gym_data,
        delete_gym_session,
        delete_gym_set,
        get_gym_sessions,
        get_gym_sets_for_session,
    )

    if not any([session_id, set_id, all_data]):
        conn = get_connection()
        init_db(conn)
        sessions = get_gym_sessions(conn, limit=10)
        if not sessions:
            console.print("[dim]No gym sessions to delete.[/dim]")
            conn.close()
            return

        console.print("[yellow]Recent gym sessions:[/yellow]")
        for s in sessions:
            sets_count = len(get_gym_sets_for_session(conn, s["id"]))
            console.print(
                f"  ID {s['id']:>4}  |  {s['session_date']}  |  "
                f"{sets_count} sets  |  {s['duration_minutes'] or '?'}min"
            )
        try:
            raw = Prompt.ask(
                "\nEnter an ID to delete, type [bold]all[/bold] to clear everything, or [bold]cancel[/bold] to abort",
                default="cancel",
            )
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Cancelled.[/dim]")
            conn.close()
            return

        raw = raw.strip().lower()
        if raw == "cancel" or not raw:
            console.print("[dim]Cancelled.[/dim]")
            conn.close()
            return
        if raw == "all":
            all_data = True
        else:
            try:
                session_id = int(raw)
            except ValueError:
                console.print(f"[red]Invalid input: '{raw}'. Use a session ID, 'all', or 'cancel'.[/red]")
                conn.close()
                return
    else:
        conn = get_connection()
        init_db(conn)

    if all_data:
        confirm = typer.confirm("This will delete ALL gym sessions and sets. Are you sure?")
        if not confirm:
            console.print("[dim]Cancelled.[/dim]")
            conn.close()
            return
        sessions, sets = delete_all_gym_data(conn)
        console.print(f"[green]Deleted {sessions} session(s) and {sets} set(s).[/green]")
    elif session_id is not None:
        sets_count = delete_gym_session(conn, session_id)
        console.print(f"[green]Deleted gym session {session_id} ({sets_count} sets).[/green]")
    elif set_id is not None:
        if delete_gym_set(conn, set_id):
            console.print(f"[green]Deleted set {set_id}.[/green]")
        else:
            console.print(f"[red]Set {set_id} not found.[/red]")

    conn.close()


def _resolve_date(date_str: str | None) -> str:
    """Parse DD/MM/YY or YYYY-MM-DD to ISO format. Defaults to today."""
    from datetime import date, datetime

    if not date_str:
        return date.today().isoformat()

    for fmt in ("%d/%m/%y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d-%m-%y"):
        try:
            return datetime.strptime(date_str, fmt).date().isoformat()
        except ValueError:
            continue

    console.print(f"[red]Could not parse date '{date_str}'. Use DD/MM/YY or YYYY-MM-DD.[/red]")
    raise typer.Exit(1)
