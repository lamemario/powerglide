"""PowerGlide CLI - Typer application root."""

from __future__ import annotations

import csv
import json
import math
import sys
import time
from datetime import date
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from prompt_toolkit import prompt

from powerglide.cli.gym import gym_app
from powerglide.cli.water import water_app
from powerglide.cli.body import body_app
from powerglide.cli.explain import explain_app
from powerglide.core.config import settings
from powerglide.core.constants import BORG_CR10_TABLE
from powerglide.database.db import get_connection, init_db

app = typer.Typer(
    name="powerglide",
    help="""Local-only performance tracker for sprint paddlers.

Run [bold cyan]powerglide[/bold cyan] with no arguments to enter the interactive shell.
Inside the shell, type commands without the 'powerglide' prefix (e.g. [bold]gym log ...[/bold]).
Type [bold]help[/bold] for this list, [bold]quit[/bold] to exit.""",
    invoke_without_command=True,
    rich_markup_mode="rich",
)
console = Console()

# Terminal width: below MIN we show compact layout / hint; full banner needs BANNER_FULL_WIDTH
MIN_TERMINAL_WIDTH = 50
BANNER_FULL_WIDTH = 72

app.add_typer(gym_app, name="gym", help="Gym session logging & history.")
app.add_typer(water_app, name="water", help="Water session logging & history.")
app.add_typer(body_app, name="body", help="Body composition logging & history.")

manage_app = typer.Typer(help="Data and app management.")
app.add_typer(manage_app, name="manage", help="Data and app management.")

app.add_typer(explain_app, name="explain", help="Step-by-step breakdown of math and sports science.")

# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------

_BANNER = [
    "██████╗  ██████╗ ██╗    ██╗███████╗██████╗  ██████╗ ██╗     ██╗██████╗ ███████╗",
    "██╔══██╗██╔═══██╗██║    ██║██╔════╝██╔══██╗██╔════╝ ██║     ██║██╔══██╗██╔════╝",
    "██████╔╝██║   ██║██║ █╗ ██║█████╗  ██████╔╝██║  ███╗██║     ██║██║  ██║█████╗  ",
    "██╔═══╝ ██║   ██║██║███╗██║██╔══╝  ██╔══██╗██║   ██║██║     ██║██║  ██║██╔══╝  ",
    "██║     ╚██████╔╝╚███╔███╔╝███████╗██║  ██║╚██████╔╝███████╗██║██████╔╝███████╗",
    "╚═╝      ╚═════╝  ╚══╝╚══╝ ╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝╚═════╝ ╚══════╝",
]


def _gradient(t: float) -> str:
    """Interpolate hot-pink -> violet -> cyan for t in [0, 1]."""
    stops = [(255, 107, 157), (168, 85, 247), (34, 211, 238)]
    if t <= 0.5:
        f = t * 2
        a, b = stops[0], stops[1]
    else:
        f = (t - 0.5) * 2
        a, b = stops[1], stops[2]
    r = int(a[0] + (b[0] - a[0]) * f)
    g = int(a[1] + (b[1] - a[1]) * f)
    bl = int(a[2] + (b[2] - a[2]) * f)
    return f"#{r:02x}{g:02x}{bl:02x}"


def _root_prompt() -> Text:
    """Root prompt 'powerglide > ' with gradient on the name (matches banner)."""
    t = Text()
    word = "powerglide"
    for i, ch in enumerate(word):
        t.append(ch, style=_gradient(i / max(len(word) - 1, 1)))
    t.append(" > ", style="bold cyan")
    return t


_in_repl = False


def _print_banner() -> None:
    width = console.width
    if width < BANNER_FULL_WIDTH:
        # Compact one-line banner so layout doesn't break when terminal is narrow
        compact = Text()
        compact.append("\n  ")
        word = "PowerGlide"
        for i, ch in enumerate(word):
            compact.append(ch, style=_gradient(i / max(len(word) - 1, 1)))
        compact.append(" — Performance Tracker for Sprint Canoeist\n", style="dim italic")
        console.print(compact)
        if width < MIN_TERMINAL_WIDTH:
            console.print("  [dim]Widen terminal (≥50 cols) for full layout.[/dim]\n")
    else:
        art = Text()
        art.append("\n")
        for row_idx, line in enumerate(_BANNER):
            w = len(line)
            for col_idx, ch in enumerate(line):
                if ch == " ":
                    art.append(ch)
                elif ch == "░":
                    art.append(ch, style="dim")
                else:
                    art.append(ch, style=_gradient(col_idx / max(w - 1, 1)))
            art.append("\n")
        console.print(art)
        console.print(
            "  [dim italic]Performance Tracker for Sprint Canoeist[/dim italic]\n"
        )

    # Getting Started Guide (skip when very narrow to keep integrity)
    if width >= MIN_TERMINAL_WIDTH:
        if width >= 68:
            guide = Table.grid(expand=True)
            guide.add_column(style="bold cyan", width=15)
            guide.add_column()
            guide.add_row("1. INITIALIZE", "Run [bold]seed[/bold] to load 800+ exercises and C1-specific data.")
            guide.add_row("2. LOG DATA", "Use [bold]import[/bold] to paste phone notes or [bold]gym log[/bold] for single sets.")
            guide.add_row("3. ANALYZE", "Run [bold]stats[/bold] for your ACWR/Fatigue or [bold]explain[/bold] for the math.")
            guide.add_row("4. VISUALIZE", "Run [bold]dashboard[/bold] to launch the interactive browser analytics.")
            console.print(Panel(guide, title="[bold white]Getting Started[/bold white]", border_style="dim", padding=(1, 2)))
        else:
            # Narrow: single-column lines so layout doesn't break (no mid-word wrap)
            compact = [
                "1. [bold cyan]INITIALIZE[/]  Run [bold]seed[/bold] for 800+ exercises.",
                "2. [bold cyan]LOG DATA[/]  [bold]import[/] or [bold]gym log[/] for sets.",
                "3. [bold cyan]ANALYZE[/]  [bold]stats[/] (ACWR/Fatigue) or [bold]explain[/].",
                "4. [bold cyan]VISUALIZE[/]  [bold]dashboard[/] for browser analytics.",
            ]
            console.print(Panel("\n".join(compact), title="[bold white]Getting Started[/bold white]", border_style="dim", padding=(1, 2)))
    console.print("\n  [dim]Quick commands: [bold]gym[/bold], [bold]water[/bold], [bold]history[/bold], [bold]help[/bold], [bold]quit[/bold][/dim]\n")


_SUBCONTEXT_PROMPTS = {
    "gym": " [bold red]gym[/bold red] [bold cyan]>[/bold cyan] ",
    "water": " [bold blue]water[/bold blue] [bold cyan]>[/bold cyan] ",
    "body": " [bold green]body[/bold green] [bold cyan]>[/bold cyan] ",
}

_FORMAT_HELP = {
    "gym": (
        "log \"Exercise Name\" WEIGHT SETS  [--rpe N] [--tags \"a,b\"]\n"
        "  Example:  log \"Bench Press\" 50 4x8 --rpe 8"
    ),
    "water": (
        "log DISTANCE TIME  [--spm N] [--rpe N] [--wind headwind]\n"
        "  Example:  log 500 2:15 --spm 45 --rpe 8"
    ),
    "body": (
        "log  [--weight KG] [--bf %] [--mm KG] [--date DD/MM/YY]\n"
        "  Example:  log --weight 75.2 --bf 14.5 --mm 35"
    ),
}


def _print_format_help(context: str) -> None:
    """Print quick-entry format help for gym, water, or body."""
    text = _FORMAT_HELP.get(context)
    if text:
        console.print(Panel(text, title="Quick-entry format", border_style="dim", padding=(0, 1)))


def _repl() -> None:
    """Interactive PowerGlide shell with stateful sub-contexts."""
    import shlex

    global _in_repl
    _in_repl = True

    current_context: str | None = None  # None | 'gym' | 'water' | 'body'

    _print_banner()

    while True:
        try:
            w = min(console.width - 2, 76)
            console.print(f"\n [dim cyan]{'━' * w}[/dim cyan]")
            prompt = _root_prompt() if current_context is None else _SUBCONTEXT_PROMPTS[current_context]
            line = console.input(prompt)
        except (KeyboardInterrupt, EOFError):
            console.print("\n\n [dim]Goodbye.[/dim]\n")
            break

        line = line.strip()
        if not line:
            continue

        lower = line.lower()

        # Exit sub-shell (back, .., exit) — only when in a context
        if current_context is not None:
            if lower in ("back", "..", "exit"):
                current_context = None
                console.print("\n [dim]Back to main.[/dim]\n")
                time.sleep(0.5)
                console.clear()
                _print_banner()
                continue

        # Quit REPL entirely (only at root)
        if current_context is None and lower in ("quit", "exit", "q"):
            console.print("\n [dim]Goodbye.[/dim]\n")
            break

        if lower == "clear":
            console.clear()
            _print_banner()
            continue

        if lower in ("help", "-h"):
            line = "--help"

        if lower.startswith("powerglide "):
            line = line[len("powerglide "):]

        try:
            parts = shlex.split(line)
        except ValueError as e:
            console.print(f"  [red]Parse error: {e}[/red]")
            continue

        # At root: enter context only when single word is gym/water/body (pass-through otherwise)
        if current_context is None and len(parts) == 1 and parts[0].lower() in ("gym", "water", "body"):
            current_context = parts[0].lower()
            # Show full help for this context so users see commands and options
            saved_argv = sys.argv[:]
            sys.argv = ["powerglide", current_context, "--help"]
            try:
                app()
            except SystemExit:
                pass
            finally:
                sys.argv = saved_argv
            _print_format_help(current_context)
            console.print(
                "  [dim]Type [bold]help[/bold] to see this again. "
                "Type [bold]back[/bold] or [bold]exit[/bold] to return to main.[/dim]"
            )
            continue

        # When in a context, prepend context to the command
        if current_context is not None:
            line = current_context + " " + line
            try:
                parts = shlex.split(line)
            except ValueError as e:
                console.print(f"  [red]Parse error: {e}[/red]")
                continue

        # Paste-mode import
        if parts[0] == "import" and not any(
            p for p in parts[1:] if not p.startswith("-")
        ):
            session_type = "gym"
            dry_run = False
            for i, p in enumerate(parts[1:]):
                if p in ("--type", "-t") and i + 2 < len(parts):
                    session_type = parts[i + 2]
                if p == "--dry-run":
                    dry_run = True

            console.print(
                "\n  [dim]Editor Mode: Paste your workout below. [/dim]"
                "\n  [dim italic](Esc+Enter to finish, Ctrl+C to cancel)[/dim italic]\n"
            )

            try:
                # This is your new "Word Doc" editor!
                from prompt_toolkit import prompt
                text = prompt("  ", multiline=True, mouse_support=True)
            except (KeyboardInterrupt, EOFError):
                console.print("\n  [dim]Import cancelled.[/dim]")
                continue

            if not text or not text.strip():
                console.print("  [red]No input received.[/red]")
                continue

            # No need to join lines anymore, prompt() gives us the whole string!
            _run_import(text, session_type, dry_run)
            continue

        console.print()
        saved = sys.argv[:]
        sys.argv = ["powerglide"] + parts
        try:
            app()
        except SystemExit:
            pass
        except KeyboardInterrupt:
            console.print("\n [dim]Command interrupted.[/dim]")
        except Exception as e:
            console.print(f"  [red]Error: {e}[/red]")
        finally:
            sys.argv = saved
        # If we just showed help for a sub-context, append quick-entry format
        if len(parts) >= 2 and parts[0].lower() in ("gym", "water", "body") and parts[1] in ("--help", "-h"):
            _print_format_help(parts[0].lower())


@app.callback(invoke_without_command=True)
def _main_callback(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None and not _in_repl:
        if sys.stdin.isatty():
            _repl()
        else:
            _print_banner()


def _run_import(text: str, session_type: str = "gym", dry_run: bool = False) -> None:
    """Shared import logic used by both the Typer command and the REPL."""
    from powerglide.core.parser import parse_gym_log, parse_water_log

    if not text.strip():
        console.print("[red]No input received.[/red]")
        return

    parser = parse_water_log if session_type == "water" else parse_gym_log
    sessions = parser(text)

    if not sessions:
        console.print("[red]No sessions could be parsed from the input.[/red]")
        return

    conn = get_connection()
    init_db(conn)

    for session in sessions:
        for err in session.errors:
            console.print(f"[red]  Error (line {err.line_number}):[/red] {err.message}")
            console.print(f"[dim]    -> {err.line_content}[/dim]")
            if err.suggestion:
                console.print(f"[yellow]    Suggestion: {err.suggestion}[/yellow]")

        for warn in session.warnings:
            console.print(f"[yellow]  Warning (line {warn.line_number}):[/yellow] {warn.message}")

        table = Table(title=f"Session: {session.session_date.isoformat()}", show_lines=True)
        table.add_column("Exercise", style="cyan")
        table.add_column("Tags", style="yellow")
        table.add_column("Sets", style="green")

        for ex in session.exercises:
            sets_str = ", ".join(
                f"{s.weight_kg}kg x {s.reps}" + (f" @{s.rpe}" if s.rpe else "")
                if not s.is_dnf else "DNF"
                for s in ex.sets
            )
            table.add_row(ex.name, ", ".join(ex.tags) if ex.tags else "-", sets_str or "No sets")

        console.print(table)

        if session.errors:
            console.print(f"[red]  {len(session.errors)} error(s) - fix before importing.[/red]")
            continue

        if dry_run:
            console.print("[dim]  (dry run - not saved)[/dim]")
            continue

        if session_type == "water":
            _save_water_session(conn, session)
        else:
            _save_gym_session(conn, session)

    conn.close()


@app.command("import")
def import_log(
    file: Optional[Path] = typer.Argument(
        None, help="Path to a text file. If omitted, reads from stdin (paste mode)."
    ),
    session_type: str = typer.Option(
        "gym", "--type", "-t", help="Session type: gym or water."
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Parse and show what would be imported without writing."
    ),
) -> None:
    """Parse a shorthand workout log from a file or pasted text."""
    if file:
        text = file.read_text(encoding="utf-8")
    else:
        console.print(
            "[dim]Paste your workout log below, then press Ctrl+Z (Windows) or Ctrl+D (Unix) "
            "followed by Enter. Ctrl+C to cancel.[/dim]"
        )
        try:
            text = sys.stdin.read()
        except KeyboardInterrupt:
            console.print("\n[dim]Import cancelled.[/dim]")
            raise typer.Exit(0)

    _run_import(text, session_type, dry_run)


def _save_gym_session(conn, session) -> None:
    from powerglide.database.queries_gym import (
        add_gym_set,
        create_gym_session,
    )
    from powerglide.database.queries_exercises import get_exercise_by_name
    from powerglide.cli.utils import select_exercise_interactively

    sid = create_gym_session(
        conn,
        session.session_date.isoformat(),
        duration_minutes=session.duration_minutes,
        session_rpe=session.session_rpe,
    )

    set_order = 0
    for ex in session.exercises:
        exercise = get_exercise_by_name(conn, ex.name)

        if exercise is None:
            try:
                exercise = select_exercise_interactively(
                    conn, ex.name, threshold=50, limit=3, allow_skip=True
                )
            except typer.Exit:
                raise
            if exercise is None:
                console.print(f"[dim]    Skipped '{ex.name}'.[/dim]")
                continue

        for s in ex.sets:
            if s.is_dnf:
                continue
            set_order += 1
            add_gym_set(
                conn,
                session_id=sid,
                exercise_id=exercise["id"],
                set_order=set_order,
                weight_kg=s.weight_kg,
                reps=s.reps,
                rpe=s.rpe,
                tags=ex.tags if ex.tags else None,
            )

    console.print(f"[green]  [OK] Saved gym session {session.session_date.isoformat()} "
                  f"({set_order} sets).[/green]")


def _save_water_session(conn, session) -> None:
    from powerglide.database.queries_water import add_water_piece, create_water_session

    sid = create_water_session(
        conn,
        session.session_date.isoformat(),
        duration_minutes=session.duration_minutes,
        session_rpe=session.session_rpe,
        wind_condition=session.wind_condition,
        water_condition=session.water_condition,
    )

    piece_count = 0
    for ex in session.exercises:
        wd = getattr(ex, "_water_data", None)
        if wd:
            piece_count += 1
            add_water_piece(
                conn,
                session_id=sid,
                piece_order=wd["piece_order"],
                distance_m=wd["distance_m"],
                time_seconds=wd["time_seconds"],
                avg_spm=wd["avg_spm"],
                piece_rpe=wd["piece_rpe"],
                notes=wd["notes"],
            )

    console.print(f"[green]  [OK] Saved water session {session.session_date.isoformat()} "
                  f"({piece_count} pieces).[/green]")


@app.command("format")
def show_format() -> None:
    """Print the shorthand format reference card."""
    gym_example = (
        "21/02/26 60min @7\n\n"
        "Bench Press \\[feet up]\n"
        "50 x 8,8,8,8 @8\n\n"
        "Seated Cable Row\n"
        "32x12, 36x12, 36x12 @7\n\n"
        "Pullups\n"
        "8,8,8,8\n\n"
        "Plank\n"
        "60s, 60s\n"
    )
    water_example = (
        "21/02/26 45min @8 headwind calm\n\n"
        "500 2:15 45spm @8\n"
        "200 0:52 50spm @9\n"
    )
    console.print(Panel(gym_example, title="Gym Format", border_style="cyan"))
    console.print(Panel(water_example, title="Water Format", border_style="blue"))
    console.print(
        "[dim]Uniform weight:[/dim]  weight x r1,r2,r3,r4\n"
        "[dim]Varying weight:[/dim]  w1xr1, w2xr2, w3xr3\n"
        "[dim]Bodyweight:    [/dim]  r1,r2,r3,r4\n"
        "[dim]Time-based:    [/dim]  60s, 60s, 10kgx30s\n"
        "[dim]Tags:          [/dim]  \\[feet up, paused]\n"
        "[dim]RPE:           [/dim]  @8 (end of set line or date line)\n"
        "[dim]Notes:         [/dim]  // shoulders felt off\n"
        "[dim]DNF:           [/dim]  dnf\n"
    )
    console.print(
        "[dim]How to import:[/dim]\n"
        "[dim]  From file: [/dim]  import workout.txt\n"
        "[dim]  Paste mode:[/dim]  import  [dim](then paste text, type END when done)[/dim]\n"
    )


@app.command("rpe")
def show_rpe() -> None:
    """Display the Modified Borg CR-10 RPE scale."""
    console.print(Panel(BORG_CR10_TABLE, title="Modified Borg CR-10 Scale", border_style="cyan"))


@app.command("seed")
def seed_db(
    force: bool = typer.Option(False, "--force", help="Drop and re-seed exercise data."),
) -> None:
    """Seed the exercise database from free-exercise-db."""
    from powerglide.database.seed import force_reseed, run_seed

    conn = get_connection()
    init_db(conn)
    if force:
        force_reseed(conn)
    else:
        run_seed(conn)
    conn.close()


@app.command("history")
def show_history(
    limit: int = typer.Option(5, "--limit", "-n", help="Number of sessions to show."),
) -> None:
    """Show recent gym and water sessions."""
    from powerglide.database.queries_gym import get_gym_sessions
    from powerglide.database.queries_water import get_water_sessions

    conn = get_connection()
    init_db(conn)

    gym = get_gym_sessions(conn, limit=limit)
    water = get_water_sessions(conn, limit=limit)

    if gym:
        table = Table(title="Recent Gym Sessions")
        table.add_column("ID", style="dim", width=4)
        table.add_column("Date", style="cyan")
        table.add_column("Duration", style="green")
        table.add_column("RPE", style="yellow")
        table.add_column("sRPE", style="magenta")
        for s in gym:
            table.add_row(
                str(s["id"]),
                s["session_date"],
                f"{s['duration_minutes'] or '?'}min",
                str(s["session_rpe"] or "-"),
                str(s["srpe"] or "-"),
            )
        console.print(table)
    else:
        console.print("[dim]No gym sessions yet.[/dim]")

    if water:
        table = Table(title="Recent Water Sessions")
        table.add_column("ID", style="dim", width=4)
        table.add_column("Date", style="cyan")
        table.add_column("Duration", style="green")
        table.add_column("RPE", style="yellow")
        table.add_column("Wind", style="blue")
        for s in water:
            table.add_row(
                str(s["id"]),
                s["session_date"],
                f"{s['duration_minutes'] or '?'}min",
                str(s["session_rpe"] or "-"),
                s["wind_condition"] or "-",
            )
        console.print(table)
    elif not gym:
        console.print("[dim]No water sessions yet.[/dim]")

    conn.close()


@app.command("constraint")
def manage_constraint(
    action: str = typer.Argument(..., help="'add', 'end', 'delete', or 'list'"),
    name: str = typer.Argument(None, help="Constraint name (e.g. 'double_hamstring_tear')"),
    start: Optional[str] = typer.Option(None, "--start", help="Start date (YYYY-MM-DD)."),
    end: Optional[str] = typer.Option(None, "--end", help="End date (YYYY-MM-DD)."),
    description: Optional[str] = typer.Option(None, "--desc", help="Description."),
) -> None:
    """Manage athlete constraints (injuries / modifications)."""
    from powerglide.database.queries_body import (
        add_constraint,
        end_constraint,
        get_active_constraints,
        get_all_constraints,
    )

    conn = get_connection()
    init_db(conn)

    if action == "list":
        constraints = get_all_constraints(conn)
        if not constraints:
            console.print("[dim]No constraints recorded.[/dim]")
        else:
            table = Table(title="Athlete Constraints")
            table.add_column("ID")
            table.add_column("Name", style="cyan")
            table.add_column("Start", style="green")
            table.add_column("End", style="yellow")
            table.add_column("Active", style="magenta")
            for c in constraints:
                table.add_row(
                    str(c["id"]),
                    c["name"],
                    c["date_start"],
                    c["date_end"] or "-",
                    "YES" if c["is_active"] else "no",
                )
            console.print(table)
    elif action == "add":
        if not name:
            console.print("[red]Provide a constraint name.[/red]")
            raise typer.Exit(1)
        d = start or date.today().isoformat()
        cid = add_constraint(conn, name, d, description=description)
        console.print(f"[green]Constraint '{name}' added (id={cid}, start={d}).[/green]")
    elif action == "end":
        if not name:
            console.print("[red]Provide the constraint name or ID to end.[/red]")
            raise typer.Exit(1)
        d = end or date.today().isoformat()
        active = get_active_constraints(conn)
        target = next((c for c in active if c["name"] == name or str(c["id"]) == name), None)
        if target is None:
            console.print(f"[red]No active constraint matching '{name}'.[/red]")
            raise typer.Exit(1)
        end_constraint(conn, target["id"], d)
        console.print(f"[green]Constraint '{target['name']}' ended on {d}.[/green]")
    elif action == "delete":
        from powerglide.database.queries_body import delete_constraint

        if not name:
            console.print("[red]Provide the constraint name or ID to delete.[/red]")
            raise typer.Exit(1)
        all_constraints = get_all_constraints(conn)
        target = next(
            (c for c in all_constraints if c["name"] == name or str(c["id"]) == name),
            None,
        )
        if target is None:
            console.print(f"[red]No constraint matching '{name}'.[/red]")
            raise typer.Exit(1)
        delete_constraint(conn, target["id"])
        console.print(f"[green]Constraint '{target['name']}' (id={target['id']}) deleted.[/green]")
    else:
        console.print(f"[red]Unknown action '{action}'. Use 'add', 'end', 'delete', or 'list'.[/red]")

    conn.close()


@manage_app.command("export")
def manage_export(
    format: str = typer.Option("json", "--format", "-f", help="Export format: json or csv"),
    output_dir: Optional[str] = typer.Option(None, "--output", "-o", help="Output directory (default: data/)."),
) -> None:
    """Export all gym_sessions and water_sessions to a structured file in data/."""
    from powerglide.database.queries_gym import (
        get_gym_sessions,
        get_gym_sets_for_session,
    )
    from powerglide.database.queries_water import (
        get_water_pieces,
        get_water_sessions,
    )

    conn = get_connection()
    init_db(conn)

    data_dir = Path(output_dir) if output_dir else settings.db_path.parent
    data_dir.mkdir(parents=True, exist_ok=True)

    gym_sessions = get_gym_sessions(conn, limit=999_999, offset=0)
    water_sessions = get_water_sessions(conn, limit=999_999, offset=0)

    payload = {
        "gym_sessions": [],
        "water_sessions": [],
    }

    for s in gym_sessions:
        sets = get_gym_sets_for_session(conn, s["id"])
        payload["gym_sessions"].append({
            "session": dict(s),
            "sets": [dict(r) for r in sets]
        })

    for s in water_sessions:
        pieces = get_water_pieces(conn, s["id"])
        payload["water_sessions"].append({
            "session": dict(s),
            "pieces": [dict(r) for r in pieces]
        })

    if format == "csv":
        gym_path = data_dir / "gym_export.csv"
        water_path = data_dir / "water_export.csv"
        with open(gym_path, "w", newline="", encoding="utf-8") as f:
            if payload["gym_sessions"]:
                sess_keys = list(payload["gym_sessions"][0]["session"].keys())
                set_keys = ["set_id", "exercise_id", "set_order", "weight_kg", "reps", "rpe", "exercise_name"]
                writer = csv.DictWriter(f, fieldnames=sess_keys + set_keys, extrasaction="ignore")
                writer.writeheader()
                for item in payload["gym_sessions"]:
                    sess = item["session"]
                    for row in item["sets"]:
                        out = {**sess, "set_id": row.get("id"), "exercise_id": row.get("exercise_id"), "set_order": row.get("set_order"), "weight_kg": row.get("weight_kg"), "reps": row.get("reps"), "rpe": row.get("rpe"), "exercise_name": row.get("exercise_name")}
                        writer.writerow(out)
            else:
                w = csv.writer(f)
                w.writerow(["session_id", "session_date", "sets_count"])
        with open(water_path, "w", newline="", encoding="utf-8") as f:
            if payload["water_sessions"]:
                sess_keys = list(payload["water_sessions"][0]["session"].keys())
                piece_keys = ["piece_id", "piece_order", "distance_m", "time_seconds", "avg_spm", "piece_rpe"]
                writer = csv.DictWriter(f, fieldnames=sess_keys + piece_keys, extrasaction="ignore")
                writer.writeheader()
                for item in payload["water_sessions"]:
                    sess = item["session"]
                    for row in item["pieces"]:
                        out = {**sess, "piece_id": row.get("id"), "piece_order": row.get("piece_order"), "distance_m": row.get("distance_m"), "time_seconds": row.get("time_seconds"), "avg_spm": row.get("avg_spm"), "piece_rpe": row.get("piece_rpe")}
                        writer.writerow(out)
            else:
                w = csv.writer(f)
                w.writerow(["session_id", "session_date", "pieces_count"])
        console.print(f"[green]Exported gym to {gym_path}, water to {water_path}.[/green]")
    else:
        out_path = data_dir / "export.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, default=str)
        console.print(f"[green]Exported to {out_path}.[/green]")

    conn.close()


@app.command("stats")
def show_stats(
    exercise: Optional[str] = typer.Argument(None, help="Exercise name for C1 strength–speed correlation (r)."),
) -> None:
    """Command-center view: latest ACWR, 72h fatigue bar chart, optional C1 correlation."""
    from powerglide.core.config import settings
    from powerglide.core.math_engine import compute_ewma_acwr, fill_rest_days
    from powerglide.database.queries_analytics import (
        get_daily_training_loads,
        get_strength_speed_data,
        get_volume_by_muscle_group,
    )
    from powerglide.database.queries_exercises import get_exercise_by_name

    conn = get_connection()
    init_db(conn)

    # --- Latest ACWR (colored by risk) ---
    raw = get_daily_training_loads(conn, days=120)
    if len(raw) >= 7:
        filled = fill_rest_days(raw)
        acwr_thresholds = {
            "undertrained_max": settings.acwr_undertrained_max,
            "optimal_max": settings.acwr_optimal_max,
            "caution_max": settings.acwr_caution_max,
        }
        acwr_data = compute_ewma_acwr(
            filled,
            acute_window=settings.acute_window,
            chronic_window=settings.chronic_window,
            acwr_thresholds=acwr_thresholds,
        )
        mature = [d for d in acwr_data if d["mature"]]
        if mature:
            latest = mature[-1]
            acwr = latest["acwr"]
            zone = latest["zone"]
            zone_style = {
                "optimal": "green",
                "undertrained": "yellow",
                "caution": "orange1",
                "danger": "red",
                "insufficient_data": "dim",
            }.get(zone, "white")
            console.print(Panel(
                f"[bold]Latest ACWR[/bold]  [bold {zone_style}]{acwr}[/bold {zone_style}]  ({zone})\n"
                f"Date: {latest['date']}  |  Acute: {latest['acute']}  |  Chronic: {latest['chronic']}",
                title="ACWR",
                border_style=zone_style,
            ))
        else:
            console.print(Panel(
                f"Need {settings.chronic_window} days of data for mature ACWR.",
                title="ACWR",
                border_style="dim",
            ))
    else:
        console.print(Panel("Need at least 7 days of training data for ACWR.", title="ACWR", border_style="dim"))

    # --- 72-hour fatigue: top 5 muscle groups (ASCII bar chart) ---
    volume = get_volume_by_muscle_group(conn, hours=72)
    top5 = volume[:5]
    if top5:
        max_vol = max((r["weighted_volume"] or 0) for r in top5) or 1
        width = console.width
        if width < MIN_TERMINAL_WIDTH:
            # Very narrow: one-line summary so layout stays intact
            parts = [f"{r.get('label') or r.get('muscle_group') or '?'}: {r.get('weighted_volume') or 0:.0f}" for r in top5]
            console.print(Panel(
                "  ".join(parts)[: max(10, width - 6)] + "\n  [dim]Widen terminal for bar chart.[/dim]",
                title="Fatigue (72h)",
                border_style="blue",
            ))
        else:
            # Dynamic widths so bar chart fits at any terminal size (panel padding ~4, value ~6)
            label_width = 12 if width < 70 else 16
            bar_width = max(5, min(20, width - 2 - label_width - 2 - 6 - 4))
            lines = ["[bold]72-Hour Load by Muscle Group[/bold]", ""]
            for r in top5:
                raw_label = (r.get("label") or r.get("muscle_group") or "?").replace(" ", "_")
                label = raw_label[:label_width].ljust(label_width)
                vol = r.get("weighted_volume") or 0
                filled_len = int(bar_width * vol / max_vol) if max_vol else 0
                bar = f"[#F0E6BD]{'█' * filled_len}[/][#8C8C9A]{'░' * (bar_width - filled_len)}[/]"
                lines.append(f"  [#F0E6BD]{label}[/] {bar} [#A0E0A0]{vol:.0f}[/]")
            console.print(Panel("\n".join(lines), title="Fatigue (72h)", border_style="blue"))
    else:
        console.print(Panel("No gym sets in the last 72 hours.", title="Fatigue (72h)", border_style="dim"))

    # --- Optional: C1 correlation for exercise ---
    if exercise:
        ex = get_exercise_by_name(conn, exercise)
        if not ex:
            console.print(f"[yellow]Exercise '{exercise}' not found; skipping C1 correlation.[/yellow]")
        else:
            from powerglide.database.queries_analytics import get_time_based_data, get_strength_speed_data
            
            tut_data = get_time_based_data(conn, ex["id"])
            if tut_data:
                lines = [f"  {r['session_date']}: Max {r['max_tut']}s  |  Total {r['total_tut']}s  ({r['set_count']} sets)" for r in tut_data[-5:]]
                console.print(Panel(
                    f"[bold]Time Under Tension (TUT) Progression (Last 5)[/bold]\n" + "\n".join(lines),
                    title=f"TUT: {ex['name']}",
                    border_style="cyan",
                ))

            data = get_strength_speed_data(conn, ex["id"])
            if len(data) < 3:
                console.print(Panel(
                    f"Need at least 3 paired (e1RM, split) points for correlation. Found {len(data)}.",
                    title=f"C1 Correlation: {ex['name']}",
                    border_style="dim",
                ))
            else:
                e1rms = [float(d["estimated_1rm"]) for d in data]
                splits = [float(d["avg_split_per_500m"]) for d in data]
                n = len(e1rms)
                mean_x = sum(e1rms) / n
                mean_y = sum(splits) / n
                cov = sum((e1rms[i] - mean_x) * (splits[i] - mean_y) for i in range(n)) / n
                var_x = sum((x - mean_x) ** 2 for x in e1rms) / n
                var_y = sum((y - mean_y) ** 2 for y in splits) / n
                import math
                r = cov / math.sqrt(var_x * var_y) if (var_x and var_y) else 0.0
                r_str = f"{r:.3f}"
                console.print(Panel(
                    f"r (e1RM vs 500m split) = [bold]{r_str}[/bold]\n"
                    f"(negative = stronger → faster split).  n = {n} pairs.",
                    title=f"C1 Correlation: {ex['name']}",
                    border_style="magenta",
                ))

    conn.close()


@app.command("dashboard")
def launch_dashboard() -> None:
    """Launch the Streamlit scientific dashboard. Ctrl+C to stop."""
    import signal
    import subprocess

    dashboard_path = Path(__file__).parent.parent / "dashboard" / "app.py"
    console.print("[cyan]Launching Streamlit dashboard... (Ctrl+C to stop)[/cyan]")

    proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", str(dashboard_path),
         "--server.headless", "true"],
    )
    try:
        proc.wait()
    except KeyboardInterrupt:
        console.print("\n[dim]Shutting down dashboard...[/dim]")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        console.print("[dim]Dashboard stopped.[/dim]")
