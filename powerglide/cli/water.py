"""Water (canoeing) logging CLI sub-commands."""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

water_app = typer.Typer(no_args_is_help=True)
console = Console()


@water_app.command("log")
def water_log(
    distance: int = typer.Argument(..., help="Distance in meters (e.g. 500)."),
    time: str = typer.Argument(..., help="Time as M:SS or M:SS.ms (e.g. 2:15 or 0:52.3)."),
    spm: Optional[float] = typer.Option(None, "--spm", help="Average strokes per minute."),
    rpe: Optional[int] = typer.Option(None, "--rpe", "-r", help="Piece RPE (1-10)."),
    wind: Optional[str] = typer.Option(None, "--wind", help="Wind: headwind, tailwind, crosswind, none."),
    condition: Optional[str] = typer.Option(None, "--condition", help="Water: calm, choppy, wavy."),
    leg_drive: Optional[int] = typer.Option(
        None, "--leg-drive-rpe", help="Leg drive RPE (0=none, 10=full). Track rehab progress."
    ),
    date_str: Optional[str] = typer.Option(None, "--date", "-d", help="Date (DD/MM/YY or YYYY-MM-DD)."),
    notes: Optional[str] = typer.Option(None, "--notes", help="Piece notes."),
) -> None:
    """Log a single water piece (distance + time)."""
    from powerglide.database.db import get_connection, init_db
    from powerglide.database.queries_water import add_water_piece, create_water_session, get_water_sessions

    time_seconds = _parse_time(time)
    if time_seconds is None:
        console.print(f"[red]Could not parse time '{time}'. Use M:SS or M:SS.ms (e.g. 2:15).[/red]")
        raise typer.Exit(1)

    session_date = _resolve_date(date_str)

    conn = get_connection()
    init_db(conn)

    row = conn.execute(
        "SELECT id FROM water_sessions WHERE session_date = ? ORDER BY id DESC LIMIT 1",
        (session_date,),
    ).fetchone()

    if row:
        sid = row["id"]
    else:
        sid = create_water_session(
            conn, session_date,
            wind_condition=wind,
            water_condition=condition,
        )

    piece_order_row = conn.execute(
        "SELECT COALESCE(MAX(piece_order), 0) + 1 AS next_order "
        "FROM water_pieces WHERE session_id = ?",
        (sid,),
    ).fetchone()
    piece_order = piece_order_row["next_order"]

    add_water_piece(
        conn,
        session_id=sid,
        piece_order=piece_order,
        distance_m=distance,
        time_seconds=time_seconds,
        avg_spm=spm,
        leg_drive_rpe=leg_drive,
        piece_rpe=rpe,
        notes=notes,
    )

    split = (time_seconds / distance) * 500 if distance > 0 else 0
    velocity = distance / time_seconds if time_seconds > 0 else 0

    console.print(
        f"[green]  [OK] {distance}m in {_format_time(time_seconds)} "
        f"(split {_format_time(split)}/500m, {velocity:.2f} m/s) "
        f"logged to {session_date}.[/green]"
    )
    conn.close()


@water_app.command("history")
def water_history(
    limit: int = typer.Option(5, "--limit", "-n"),
) -> None:
    """View recent water sessions and pieces."""
    from powerglide.database.db import get_connection, init_db
    from powerglide.database.queries_water import get_water_pieces, get_water_sessions

    conn = get_connection()
    init_db(conn)
    sessions = get_water_sessions(conn, limit=limit)

    if not sessions:
        console.print("[dim]No water sessions found.[/dim]")
        conn.close()
        return

    for session in sessions:
        pieces = get_water_pieces(conn, session["id"])
        header = f"{session['session_date']}"
        if session["wind_condition"]:
            header += f"  |  {session['wind_condition']}"
        if session["session_rpe"]:
            header += f"  |  RPE {session['session_rpe']}"

        table = Table(title=header)
        table.add_column("#", style="dim", width=3)
        table.add_column("Distance", style="cyan", justify="right")
        table.add_column("Time", style="green", justify="right")
        table.add_column("Split/500m", style="magenta", justify="right")
        table.add_column("m/s", justify="right")
        table.add_column("SPM", justify="right")
        table.add_column("DPS", justify="right")

        for p in pieces:
            table.add_row(
                str(p["piece_order"]),
                f"{p['distance_m']}m",
                _format_time(p["time_seconds"]),
                _format_time(p["avg_split_per_500m"]) if p["avg_split_per_500m"] else "-",
                f"{p['avg_velocity_ms']}" if p["avg_velocity_ms"] else "-",
                str(p["avg_spm"] or "-"),
                str(p["distance_per_stroke"] or "-"),
            )

        console.print(table)
        console.print()

    conn.close()


@water_app.command("delete")
def water_delete(
    session_id: Optional[int] = typer.Option(None, "--session", "-s", help="Delete a water session by ID."),
    piece_id: Optional[int] = typer.Option(None, "--piece", help="Delete a single piece by ID."),
    all_data: bool = typer.Option(False, "--all", help="Delete ALL water sessions and pieces."),
) -> None:
    """Delete water sessions, individual pieces, or all water data."""
    from powerglide.database.db import get_connection, init_db
    from powerglide.database.queries_water import (
        delete_all_water_data,
        delete_water_piece,
        delete_water_session,
        get_water_pieces,
        get_water_sessions,
    )

    if not any([session_id, piece_id, all_data]):
        conn = get_connection()
        init_db(conn)
        sessions = get_water_sessions(conn, limit=10)
        if not sessions:
            console.print("[dim]No water sessions to delete.[/dim]")
            conn.close()
            return

        console.print("[yellow]Recent water sessions:[/yellow]")
        for s in sessions:
            pieces_count = len(get_water_pieces(conn, s["id"]))
            console.print(
                f"  ID {s['id']:>4}  |  {s['session_date']}  |  "
                f"{pieces_count} piece(s)  |  {s['wind_condition'] or 'no wind'}"
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
        confirm = typer.confirm("This will delete ALL water sessions and pieces. Are you sure?")
        if not confirm:
            console.print("[dim]Cancelled.[/dim]")
            conn.close()
            return
        sessions, pieces = delete_all_water_data(conn)
        console.print(f"[green]Deleted {sessions} session(s) and {pieces} piece(s).[/green]")
    elif session_id is not None:
        pieces_count = delete_water_session(conn, session_id)
        console.print(f"[green]Deleted water session {session_id} ({pieces_count} pieces).[/green]")
    elif piece_id is not None:
        if delete_water_piece(conn, piece_id):
            console.print(f"[green]Deleted piece {piece_id}.[/green]")
        else:
            console.print(f"[red]Piece {piece_id} not found.[/red]")

    conn.close()


def _parse_time(time_str: str) -> float | None:
    """Parse M:SS or M:SS.ms to total seconds."""
    import re
    match = re.match(r"^(\d+):(\d{2}(?:\.\d+)?)$", time_str.strip())
    if not match:
        return None
    minutes = int(match.group(1))
    seconds = float(match.group(2))
    return minutes * 60.0 + seconds


def _format_time(seconds: float | None) -> str:
    if seconds is None:
        return "-"
    m = int(seconds // 60)
    s = seconds % 60
    return f"{m}:{s:05.2f}"


def _resolve_date(date_str: str | None) -> str:
    from datetime import date, datetime
    if not date_str:
        return date.today().isoformat()
    for fmt in ("%d/%m/%y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str, fmt).date().isoformat()
        except ValueError:
            continue
    console.print(f"[red]Could not parse date '{date_str}'.[/red]")
    raise typer.Exit(1)
