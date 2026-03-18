"""Explain command group — mathematical transparency and sports-science context."""

from __future__ import annotations

from datetime import datetime, timedelta

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from powerglide.core.config import settings
from powerglide.core.math_engine import compute_ewma_acwr, explain_1rm, fill_rest_days
from powerglide.database.db import get_connection, init_db
from powerglide.database.queries_analytics import (
    get_daily_training_loads,
    get_fatigue_breakdown_by_muscle,
    get_volume_by_muscle_group,
)
from powerglide.database.queries_gym import (
    get_gym_session_by_id,
    get_gym_sessions,
    get_gym_sets_for_session,
)

explain_app = typer.Typer(
    name="explain",
    help="Step-by-step breakdown of the math and sports science behind core calculations.",
    rich_markup_mode="rich",
)
console = Console()


@explain_app.callback(invoke_without_command=True)
def explain_callback(ctx: typer.Context) -> None:
    """Mathematical transparency and sports-science context."""
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        raise typer.Exit(0)


@explain_app.command("help", hidden=True)
def explain_help(ctx: typer.Context) -> None:
    """Show this help message and exit."""
    # Try to find the explain app context
    current = ctx
    while current and current.info_name != "explain":
        current = current.parent
    
    if current:
        console.print(current.get_help())
    else:
        console.print(ctx.parent.get_help())


@explain_app.command("1rm")
def explain_1rm_cmd(
    weight: float = typer.Option(..., "--weight", "-w", help="Weight lifted (kg). E.g., 100"),
    reps: int = typer.Option(..., "--reps", "-r", help="Number of reps performed. E.g., 5"),
) -> None:
    """
    Break down the 1RM (One-Rep Max) prediction.
    
    Shows whether Brzycki (best for <10 reps) or Epley (better for high reps) was used.
    """
    info = explain_1rm(weight, reps)
    if info is None:
        console.print("[red]Invalid inputs: weight must be > 0 and reps ≥ 1.[/red]")
        raise typer.Exit(1)

    body = (
        f"[bold]Inputs:[/bold] {weight} kg @ {reps} rep{'s' if reps != 1 else ''}\n\n"
        f"[bold]Formula:[/bold] {info['formula']}\n"
        f"[bold]Math:[/bold]    {info['math']}\n"
        f"[bold]Result:[/bold]  [cyan]{info['result']} kg[/cyan]\n\n"
        f"[dim]Citation:[/dim] {info['citation']}\n"
        f"[dim]Note:[/dim] {info['note']}"
    )
    console.print(
        Panel(
            body,
            title="[bold cyan]1RM Explanation[/bold cyan]",
            border_style="cyan",
        )
    )
    console.print(
        "\n[dim]Sports Science Context:[/dim] Splitting at 10 reps (Brzycki ≤10, Epley >10) "
        "matches the literature: Brzycki accuracy drops above 10 reps; Epley reduces over-estimation of max force."
    )


@explain_app.command("acwr")
def explain_acwr_cmd() -> None:
    """
    Explain the Acute:Chronic Workload Ratio (ACWR).
    
    Shows the EWMA formula, decay constants (lambda), and your current risk zone.
    """
    acute = settings.acute_window
    chronic = settings.chronic_window
    lambda_a = 2.0 / (acute + 1)
    lambda_c = 2.0 / (chronic + 1)

    body_lines = [
        f"[bold]Acute Window:[/bold] {acute} days  [bold]|[/bold]  [bold]Chronic Window:[/bold] {chronic} days",
        "",
        "[bold]Decay Constants (λ):[/bold]",
        f"  • Acute λ:   [cyan]{lambda_a:.3f}[/cyan] (current day ≈ {lambda_a*100:.1f}% of the average)",
        f"  • Chronic λ: [cyan]{lambda_c:.3f}[/cyan] (current day ≈ {lambda_c*100:.1f}% of the average)",
        "",
        "[bold]Formula:[/bold] EWMA_today = (Load_today × λ) + (Previous_EWMA × (1 − λ))",
        "",
    ]

    conn = get_connection()
    init_db(conn)
    raw = get_daily_training_loads(conn, days=120)
    conn.close()

    if len(raw) >= 7:
        filled = fill_rest_days(raw)
        acwr_thresholds = {
            "undertrained_max": settings.acwr_undertrained_max,
            "optimal_max": settings.acwr_optimal_max,
            "caution_max": settings.acwr_caution_max,
        }
        acwr_data = compute_ewma_acwr(
            filled,
            acute_window=acute,
            chronic_window=chronic,
            acwr_thresholds=acwr_thresholds,
        )
        mature = [d for d in acwr_data if d["mature"]]
        if mature:
            latest = mature[-1]
            acwr_val = latest["acwr"]
            zone = latest["zone"]
            zone_style = {"optimal": "green", "undertrained": "yellow", "caution": "orange1", "danger": "red"}.get(
                zone, "white"
            )
            body_lines.append(f"[bold]Current Zone:[/bold] [bold {zone_style}]{acwr_val} ({zone})[/bold {zone_style}]")
            body_lines.append("")
            body_lines.append(
                "[dim]Citation:[/dim] Qin et al. (2025). ACWR for predicting sports injury risk. BMC Sports Sci Med Rehabil."
            )
            if zone == "optimal":
                body_lines.append(
                    "[dim]Analysis:[/dim] Your ratio is within the 0.8–1.3 sweet spot, indicating positive adaptation with low injury risk."
                )
            elif zone == "undertrained":
                body_lines.append("[dim]Analysis:[/dim] Below 0.8 suggests insufficient acute load relative to chronic capacity.")
            elif zone == "caution":
                body_lines.append("[dim]Analysis:[/dim] Above 1.3; consider moderating load progression to reduce injury risk.")
            else:
                body_lines.append("[dim]Analysis:[/dim] Above 1.5 is associated with higher injury risk in the literature.")
        else:
            body_lines.append(f"[dim]Need {chronic} days of data for a mature ACWR reading.[/dim]")
            body_lines.append("[dim]Citation:[/dim] Qin et al. (2025). Research Papers/Acute to chronic workload ratio (ACWR).pdf")
    else:
        body_lines.append("[dim]Need at least 7 days of training data for ACWR.[/dim]")
        body_lines.append("[dim]Citation:[/dim] Qin et al. (2025). Research Papers/Acute to chronic workload ratio (ACWR).pdf")

    console.print(
        Panel(
            "\n".join(body_lines),
            title="[bold cyan]ACWR Explanation[/bold cyan]",
            border_style="cyan",
        )
    )
    console.print(
        "\n[dim]Sports Science Context:[/dim] EWMA (λ = 2/(N+1)) gives more weight to recent load than rolling averages, "
        "providing a more sensitive indicator of injury likelihood (Qin et al. 2025)."
    )


@explain_app.command("fatigue")
def explain_fatigue_cmd(
    muscle: str = typer.Option(..., "--muscle", "-m", help="Muscle group to check (e.g., 'Triceps', 'Back')."),
    hours: int = typer.Option(72, "--hours", "-h", help="Lookback window (default: 72 hours)."),
) -> None:
    """
    Show which specific sets caused fatigue in a muscle group.
    
    Lists exercises, their coefficients (e.g., 0.3 for triceps during OHP), and weighted volume.
    """
    conn = get_connection()
    init_db(conn)

    rows, total, label = get_fatigue_breakdown_by_muscle(conn, muscle, hours=hours)

    if not rows or label is None:
        # Show valid muscle groups
        all_muscles = get_volume_by_muscle_group(conn, hours=168)
        console.print(f"[yellow]No sets found for muscle matching '{muscle}' in the last {hours} hours.[/yellow]")
        if all_muscles:
            console.print("[dim]Valid muscle groups (from recent data):[/dim]")
            for m in all_muscles[:12]:
                console.print(f"  • {m.get('label') or m.get('muscle_group', '?')}")
        conn.close()
        raise typer.Exit(1)

    # Aggregate by exercise (sum raw, show coefficient/role, sum weighted)
    by_exercise: dict[str, dict] = {}
    for r in rows:
        name = r["exercise_name"]
        raw = r["raw_volume"] or 0
        coef = r["coefficient"] or 0
        role = (r.get("role") or "primary").lower()
        weighted = r["weighted_volume"] or 0
        if name not in by_exercise:
            by_exercise[name] = {"raw": 0.0, "coefficient": coef, "role": role, "weighted": 0.0}
        by_exercise[name]["raw"] += raw
        by_exercise[name]["weighted"] += weighted

    now = datetime.now()
    window_start = now - timedelta(hours=hours)
    window_str = f"{window_start.strftime('%b %d, %H:%M')} to {now.strftime('%b %d, %H:%M')}"

    table = Table(show_header=True, header_style="bold cyan", border_style="dim")
    table.add_column("Exercise", style="cyan")
    table.add_column("Raw Vol (kg)", justify="right")
    table.add_column("Coefficient", justify="center")
    table.add_column("Weighted Vol (kg)", justify="right")
    role_short = {"primary": "Prime", "secondary": "Assis", "stabilizer": "Stab"}
    for name, data in sorted(by_exercise.items(), key=lambda x: -x[1]["weighted"]):
        role_label = role_short.get(data["role"], data["role"])
        table.add_row(
            name,
            f"{data['raw']:,.0f}",
            f"{data['coefficient']:.1f} ({role_label})",
            f"{data['weighted']:,.0f}",
        )

    console.print(
        Panel(
            f"[bold]Total Weighted Volume:[/bold] [cyan]{total:,.0f} kg[/cyan]\n"
            f"[bold]Window:[/bold] {window_str}",
            title=f"[bold cyan]{label} Fatigue ({hours}h)[/bold cyan]",
            border_style="cyan",
        )
    )
    console.print(table)
    console.print(
        Panel(
            "72 hours represents the typical window for Muscle Protein Synthesis (MPS) to return to baseline "
            "and for Central Nervous System (CNS) recovery in high-power athletes (C1 Sprinters).",
            title="[dim]Science Context[/dim]",
            border_style="dim",
        )
    )
    conn.close()


@explain_app.command("workout")
def explain_workout_cmd(
    id: int = typer.Option(..., "--id", help="Session ID from 'gym history' or 'stats'."),
) -> None:
    """
    Break down a specific session's internal and external load.
    
    Internal load = RPE x Duration. External load = Sum(weight x reps).
    """
    conn = get_connection()
    init_db(conn)

    session = get_gym_session_by_id(conn, id)
    if not session:
        sessions = get_gym_sessions(conn, limit=10)
        console.print(f"[red]No gym session with id {id}.[/red]")
        if sessions:
            console.print("[dim]Recent sessions (use --id):[/dim]")
            for s in sessions[:5]:
                console.print(f"  • id={s['id']}  date={s['session_date']}  duration={s.get('duration_minutes') or '?'}min")
        conn.close()
        raise typer.Exit(1)

    sets = get_gym_sets_for_session(conn, id)
    conn.close()

    duration = session.get("duration_minutes") or 0
    rpe = session.get("session_rpe")
    if rpe is not None and duration is not None:
        srpe = duration * rpe
        internal_line = f"[bold]Internal Load (sRPE):[/bold] {duration} min × RPE {rpe} = [cyan]{srpe} AU[/cyan] (Arbitrary Units)"
    else:
        internal_line = "[bold]Internal Load (sRPE):[/bold] [dim]No duration or RPE recorded.[/dim]"

    external_vol = sum((s.get("volume_load") or 0) for s in sets)
    external_line = f"[bold]External Volume:[/bold] Sum of all set volume_load = [cyan]{external_vol:,.0f} kg[/cyan] ({len(sets)} sets)"

    body = (
        f"Session [bold]{session['session_date']}[/bold] (id={id})\n\n"
        f"{internal_line}\n\n"
        f"{external_line}\n\n"
        "[dim]Citation:[/dim] Foster et al. (2001). A new approach to monitoring exercise training. "
        "Session-RPE (duration × RPE) quantifies internal load; external volume (weight × reps) quantifies mechanical work."
    )
    console.print(
        Panel(
            body,
            title="[bold cyan]Workout Explanation[/bold cyan]",
            border_style="cyan",
        )
    )
    console.print(
        "\n[dim]Sports Science Context:[/dim] Internal load (sRPE) reflects physiological and perceptual stress; "
        "external volume reflects mechanical stimulus. Both are used in ACWR and load management."
    )
