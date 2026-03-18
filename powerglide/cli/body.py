"""Body composition logging CLI sub-commands."""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

body_app = typer.Typer(no_args_is_help=True)
console = Console()


@body_app.command("log")
def body_log(
    weight: Optional[float] = typer.Option(None, "--weight", "-w", help="Total weight in kg."),
    body_fat: Optional[float] = typer.Option(None, "--bf", help="Body fat percentage."),
    muscle_mass: Optional[float] = typer.Option(None, "--mm", help="Muscle mass in kg."),
    body_water: Optional[float] = typer.Option(None, "--water", help="Total body water percentage."),
    visceral: Optional[int] = typer.Option(None, "--visceral", help="Visceral fat level (integer)."),
    bmr: Optional[int] = typer.Option(None, "--bmr", help="Basal metabolic rate in kcal."),
    date_str: Optional[str] = typer.Option(None, "--date", "-d", help="Measurement date (DD/MM/YY or YYYY-MM-DD)."),
    notes: Optional[str] = typer.Option(None, "--notes", help="Notes."),
) -> None:
    """Log a body composition measurement."""
    from powerglide.database.db import get_connection, init_db
    from powerglide.database.queries_body import add_body_composition

    if all(v is None for v in (weight, body_fat, muscle_mass, body_water, visceral, bmr)):
        console.print("[red]Provide at least one measurement (--weight, --bf, --mm, etc.).[/red]")
        raise typer.Exit(1)

    session_date = _resolve_date(date_str)

    conn = get_connection()
    init_db(conn)

    add_body_composition(
        conn,
        measured_date=session_date,
        total_weight_kg=weight,
        body_fat_pct=body_fat,
        muscle_mass_kg=muscle_mass,
        total_body_water_pct=body_water,
        visceral_fat_level=visceral,
        bmr_kcal=bmr,
        notes=notes,
    )

    parts = []
    if weight is not None:
        parts.append(f"{weight}kg")
    if body_fat is not None:
        parts.append(f"BF {body_fat}%")
    if muscle_mass is not None:
        parts.append(f"MM {muscle_mass}kg")

    console.print(f"[green]  [OK] Body comp logged for {session_date}: {', '.join(parts) or 'recorded'}.[/green]")
    conn.close()


@body_app.command("history")
def body_history(
    limit: int = typer.Option(10, "--limit", "-n"),
) -> None:
    """View body composition history."""
    from powerglide.database.db import get_connection, init_db
    from powerglide.database.queries_body import get_body_compositions

    conn = get_connection()
    init_db(conn)
    records = get_body_compositions(conn, limit=limit)

    if not records:
        console.print("[dim]No body composition records yet.[/dim]")
        conn.close()
        return

    table = Table(title="Body Composition History")
    table.add_column("Date", style="cyan")
    table.add_column("Weight", style="green", justify="right")
    table.add_column("Body Fat", style="yellow", justify="right")
    table.add_column("Muscle Mass", style="magenta", justify="right")
    table.add_column("Body Water", justify="right")
    table.add_column("Notes", style="dim")

    for r in records:
        table.add_row(
            r["measured_date"],
            f"{r['total_weight_kg']}kg" if r["total_weight_kg"] else "-",
            f"{r['body_fat_pct']}%" if r["body_fat_pct"] else "-",
            f"{r['muscle_mass_kg']}kg" if r["muscle_mass_kg"] else "-",
            f"{r['total_body_water_pct']}%" if r["total_body_water_pct"] else "-",
            r["notes"] or "",
        )

    console.print(table)
    conn.close()


@body_app.command("delete")
def body_delete(
    record_id: Optional[int] = typer.Option(None, "--id", "-i", help="Delete a body composition record by ID."),
) -> None:
    """Delete a body composition record."""
    from powerglide.database.db import get_connection, init_db
    from powerglide.database.queries_body import delete_body_composition, get_body_compositions

    conn = get_connection()
    init_db(conn)

    if record_id is None:
        records = get_body_compositions(conn, limit=10)
        if not records:
            console.print("[dim]No body composition records to delete.[/dim]")
            conn.close()
            return

        console.print("[yellow]Recent body composition records:[/yellow]")
        for r in records:
            w = f"{r['total_weight_kg']}kg" if r["total_weight_kg"] else "?"
            console.print(f"  ID {r['id']:>4}  |  {r['measured_date']}  |  {w}")
        try:
            raw = Prompt.ask(
                "\nEnter an ID to delete, or [bold]cancel[/bold] to abort",
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
        try:
            record_id = int(raw)
        except ValueError:
            console.print(f"[red]Invalid input: '{raw}'. Use a record ID or 'cancel'.[/red]")
            conn.close()
            return

    if delete_body_composition(conn, record_id):
        console.print(f"[green]Deleted body composition record {record_id}.[/green]")
    else:
        console.print(f"[red]Record {record_id} not found.[/red]")
    conn.close()


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
