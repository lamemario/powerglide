"""PowerGlide Streamlit Dashboard — Scientific visualization for C1 sprint paddlers."""

from __future__ import annotations

import streamlit as st

from powerglide.core.constants import BORG_CR10_SCALE
from powerglide.database.db import get_connection, init_db
from powerglide.dashboard.charts import (
    render_acwr_timeline,
    render_body_composition,
    render_strength_speed_scatter,
    render_volume_heatmap,
    render_training_volume_by_force_vector,
    render_exercise_1rm_trend,
)

st.set_page_config(
    page_title="PowerGlide",
    page_icon="🏋️",
    layout="wide",
)

st.title("PowerGlide")
st.caption("Local-only scientific dashboard for C1 sprint paddlers")


@st.cache_resource
def _get_conn():
    conn = get_connection()
    init_db(conn)
    return conn


conn = _get_conn()

tab_acwr, tab_volume, tab_strength, tab_e1rm, tab_body = st.tabs([
    "ACWR Timeline",
    "Volume Distribution",
    "Strength ↔ Speed",
    "Exercise e1RM Trend",
    "Body Composition",
])

with tab_acwr:
    st.subheader("Acute:Chronic Workload Ratio (EWMA)")
    st.caption(
        "Based on session RPE × duration. The EWMA method (λ_acute=0.25, λ_chronic=0.069) "
        "provides 84.4% injury classification accuracy (Murray et al., 2017)."
    )
    render_acwr_timeline(conn)

with tab_volume:
    st.subheader("Volume Distribution Heatmap")
    st.warning(
        "**Disclaimer:** This map visualizes mechanical volume distribution, "
        "NOT biological recovery or muscle readiness. Listen to your body.",
        icon="⚠️",
    )
    hours = st.slider("Trailing hours", 24, 168, 72, step=24)
    render_volume_heatmap(conn, hours=hours)
    render_training_volume_by_force_vector(conn, hours=hours)

with tab_strength:
    st.subheader("Strength ↔ Speed Correlation")
    st.caption(
        "Maps gym estimated 1RM to on-water split pace. "
        "Literature: Bench Pull Power ↔ Sprint Velocity r=0.80 (Arpino et al., 2022)."
    )
    render_strength_speed_scatter(conn)

with tab_e1rm:
    st.subheader("Estimated 1RM Progression")
    render_exercise_1rm_trend(conn)

with tab_body:
    st.subheader("Body Composition Over Time")
    render_body_composition(conn)

with st.sidebar:
    st.header("RPE Reference")
    for val, (label, desc) in BORG_CR10_SCALE.items():
        st.markdown(f"**{val}** — {label}: _{desc}_")

    st.divider()
    if st.button("Stop Dashboard", type="secondary"):
        st.toast("Shutting down... close this tab.")
        st.stop()
