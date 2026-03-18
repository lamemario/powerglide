"""Chart builder functions for the Streamlit dashboard using Plotly."""

from __future__ import annotations

import sqlite3
from datetime import date

import plotly.graph_objects as go
import streamlit as st


def render_acwr_timeline(conn: sqlite3.Connection) -> None:
    from powerglide.core.config import settings
    from powerglide.core.math_engine import compute_ewma_acwr, fill_rest_days
    from powerglide.database.queries_analytics import get_daily_training_loads

    raw = get_daily_training_loads(conn, days=120)
    if len(raw) < 7:
        st.info("Need at least 7 days of training data for ACWR calculation.")
        return

    filled = fill_rest_days(raw)
    acwr_data = compute_ewma_acwr(
        filled,
        acute_window=settings.acute_window,
        chronic_window=settings.chronic_window,
        acwr_thresholds={
            "undertrained_max": settings.acwr_undertrained_max,
            "optimal_max": settings.acwr_optimal_max,
            "caution_max": settings.acwr_caution_max,
        },
    )

    dates = [d["date"] for d in acwr_data if d["mature"]]
    acwr_vals = [d["acwr"] for d in acwr_data if d["mature"]]
    zones = [d["zone"] for d in acwr_data if d["mature"]]

    if not dates:
        st.info(f"Need at least {settings.chronic_window} days of data for a mature ACWR reading.")
        return

    zone_colors = {
        "optimal": "green",
        "undertrained": "orange",
        "caution": "goldenrod",
        "danger": "red",
    }
    colors = [zone_colors.get(z, "gray") for z in zones]

    fig = go.Figure()
    fig.add_hrect(y0=0.8, y1=1.3, fillcolor="green", opacity=0.08,
                  annotation_text="Optimal (0.8–1.3)", annotation_position="top left")
    fig.add_hrect(y0=1.5, y1=3.0, fillcolor="red", opacity=0.06,
                  annotation_text="Danger (>1.5)", annotation_position="top left")

    fig.add_trace(go.Scatter(
        x=dates, y=acwr_vals, mode="lines+markers",
        marker=dict(color=colors, size=6),
        line=dict(color="steelblue", width=2),
        name="ACWR",
        hovertemplate="Date: %{x}<br>ACWR: %{y:.2f}<extra></extra>",
    ))
    fig.update_layout(
        yaxis_title="ACWR", xaxis_title="Date",
        height=400, margin=dict(l=40, r=20, t=20, b=40),
    )
    st.plotly_chart(fig, width="stretch")


def render_volume_heatmap(conn: sqlite3.Connection, hours: int = 72) -> None:
    from powerglide.database.queries_analytics import get_volume_by_muscle_group

    data = get_volume_by_muscle_group(conn, hours=hours)
    if not data:
        st.info(f"No gym data in the last {hours} hours.")
        return

    groups = [d["label"] for d in data]
    volumes = [d["weighted_volume"] for d in data]

    fig = go.Figure(go.Bar(
        x=volumes, y=groups, orientation="h",
        marker=dict(
            color=volumes,
            colorscale="YlOrRd",
            showscale=True,
            colorbar=dict(title="Volume"),
        ),
        hovertemplate="%{y}: %{x:.0f} AU<extra></extra>",
    ))
    fig.update_layout(
        xaxis_title="Weighted Volume (kg × reps × coefficient)",
        height=max(300, len(groups) * 35),
        margin=dict(l=120, r=20, t=10, b=40),
        yaxis=dict(autorange="reversed"),
    )
    st.plotly_chart(fig, width="stretch")


def render_training_volume_by_force_vector(conn: sqlite3.Connection, hours: int = 72) -> None:
    """Weekly volume breakdown by C1 force vector."""
    rows = conn.execute(
        """
        SELECT e.c1_force_analog, SUM(gs.volume_load) AS total_volume
        FROM gym_sets gs
        JOIN gym_sessions s ON gs.session_id = s.id
        JOIN exercises e ON gs.exercise_id = e.id
        WHERE e.c1_force_analog IS NOT NULL
          AND s.session_date >= date('now', ? || ' hours')
        GROUP BY e.c1_force_analog
        ORDER BY total_volume DESC
        """,
        (f"-{hours}",),
    ).fetchall()

    if not rows:
        st.info("No C1-tagged exercises in the selected window.")
        return

    labels = [r["c1_force_analog"].replace("_", " ").title() for r in rows]
    values = [r["total_volume"] for r in rows]

    fig = go.Figure(go.Pie(labels=labels, values=values, hole=0.4))
    fig.update_layout(
        title_text="Volume by C1 Force Vector",
        height=350, margin=dict(l=20, r=20, t=40, b=20),
    )
    st.plotly_chart(fig, width="stretch")


def render_strength_speed_scatter(conn: sqlite3.Connection) -> None:
    exercises = conn.execute(
        "SELECT id, name FROM exercises WHERE c1_force_analog IS NOT NULL ORDER BY c1_relevance DESC"
    ).fetchall()

    if not exercises:
        st.info("No C1-relevant exercises found. Run 'powerglide seed' first.")
        return

    ex_names = [e["name"] for e in exercises]
    selected = st.selectbox("Select gym exercise (X-axis: e1RM)", ex_names)

    ex = next((e for e in exercises if e["name"] == selected), None)
    if not ex:
        return

    from powerglide.database.queries_analytics import get_strength_speed_data
    data = get_strength_speed_data(conn, ex["id"])

    if len(data) < 3:
        st.info("Need at least 3 paired gym/water data points for a meaningful scatter.")
        return

    e1rms = [d["estimated_1rm"] for d in data]
    splits = [d["avg_split_per_500m"] for d in data]
    labels = [f"Gym: {d['gym_date']}, Water: {d['water_date']}" for d in data]

    fig = go.Figure(go.Scatter(
        x=e1rms, y=splits, mode="markers",
        marker=dict(size=10, color="steelblue"),
        text=labels,
        hovertemplate="e1RM: %{x:.1f}kg<br>Split: %{y:.1f}s/500m<br>%{text}<extra></extra>",
    ))
    fig.update_layout(
        xaxis_title=f"{selected} — Estimated 1RM (kg)",
        yaxis_title="500m Split (seconds)",
        yaxis=dict(autorange="reversed"),
        height=400, margin=dict(l=60, r=20, t=20, b=60),
    )
    st.plotly_chart(fig, width="stretch")


def render_exercise_1rm_trend(conn: sqlite3.Connection) -> None:
    """Plot e1RM over time for a selected exercise, with tag-based coloring."""
    exercises = conn.execute(
        "SELECT DISTINCT e.id, e.name FROM exercises e "
        "JOIN gym_sets gs ON e.id = gs.exercise_id ORDER BY e.name"
    ).fetchall()

    if not exercises:
        st.info("No gym sets logged yet.")
        return

    ex_names = [e["name"] for e in exercises]
    selected = st.selectbox("Select exercise", ex_names, key="e1rm_exercise")
    ex = next((e for e in exercises if e["name"] == selected), None)
    if not ex:
        return

    from powerglide.database.queries_gym import get_exercise_history
    history = get_exercise_history(conn, ex["id"], limit=200)

    if not history:
        st.info(f"No sets recorded for {selected}.")
        return

    import json

    dates = [h["session_date"] for h in history]
    e1rms = [h["estimated_1rm"] for h in history if h["estimated_1rm"]]
    e1rm_dates = [h["session_date"] for h in history if h["estimated_1rm"]]

    tags_per_set = []
    for h in history:
        if h["estimated_1rm"]:
            t = json.loads(h["tags"]) if h.get("tags") else []
            tags_per_set.append(", ".join(t) if t else "none")

    has_constraint = any(t != "none" for t in tags_per_set)
    colors = ["orange" if t != "none" else "steelblue" for t in tags_per_set]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=e1rm_dates, y=e1rms, mode="lines+markers",
        marker=dict(color=colors, size=7),
        line=dict(color="steelblue", width=2),
        text=tags_per_set,
        hovertemplate="Date: %{x}<br>e1RM: %{y:.1f}kg<br>Tags: %{text}<extra></extra>",
        name="e1RM",
    ))

    if has_constraint:
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode="markers",
            marker=dict(color="orange", size=8),
            name="Constrained (e.g. feet up)",
        ))

    fig.update_layout(
        yaxis_title="Estimated 1RM (kg)", xaxis_title="Date",
        height=400, margin=dict(l=40, r=20, t=20, b=40),
    )
    st.plotly_chart(fig, width="stretch")


def render_body_composition(conn: sqlite3.Connection) -> None:
    from powerglide.database.queries_body import get_body_compositions

    records = get_body_compositions(conn, limit=100)
    if not records:
        st.info("No body composition data. Use 'powerglide body log' to add measurements.")
        return

    records = list(reversed(records))
    dates = [r["measured_date"] for r in records]

    fig = go.Figure()
    metrics = [
        ("total_weight_kg", "Weight (kg)", "steelblue"),
        ("muscle_mass_kg", "Muscle Mass (kg)", "green"),
        ("body_fat_pct", "Body Fat (%)", "orange"),
        ("total_body_water_pct", "Body Water (%)", "cyan"),
    ]

    for key, label, color in metrics:
        vals = [r[key] for r in records]
        if any(v is not None for v in vals):
            fig.add_trace(go.Scatter(
                x=dates, y=vals, mode="lines+markers",
                name=label, line=dict(color=color, width=2),
                marker=dict(size=5),
            ))

    fig.update_layout(
        yaxis_title="Value", xaxis_title="Date",
        height=400, margin=dict(l=40, r=20, t=20, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig, width="stretch")
