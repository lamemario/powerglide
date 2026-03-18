"""Pure math functions — 1RM estimation, ACWR via EWMA, volume distribution."""

from __future__ import annotations

from datetime import date, timedelta
# Default ACWR risk-zone boundaries (user-overridable via powerglide.toml).
# Validated against Qin et al. (2025) BMC Sports Sci Med Rehabil: EWMA γ = 2/(N+1);
# 0.8–1.3 low-risk band, >1.5 higher injury risk (Research Papers/Acute to chronic workload ratio (ACWR).pdf).
_DEFAULT_ACWR_UNDERTRAINED_MAX = 0.80
_DEFAULT_ACWR_OPTIMAL_MAX = 1.30
_DEFAULT_ACWR_CAUTION_MAX = 1.50


def estimate_1rm(weight_kg: float, reps: int) -> float | None:
    """
    Estimate one-rep max from a submaximal set.

    reps == 1  → actual single, return weight as-is
    reps 2-10  → Brzycki  (weight × 36 / (37 − reps)); validated for 1–10 reps (Brzycki, 1993).
    reps > 10  → Epley    (weight × (1 + reps / 30)); better accuracy above 10 reps (Epley, 1985).
    reps < 1   → invalid

    Literature supports splitting at 10 reps: Brzycki most accurate 1–10; Epley preferred for >10.
    """
    if reps < 1 or weight_kg <= 0:
        return None
    if reps == 1:
        return round(weight_kg, 1)
    if reps <= 10:
        return round(weight_kg * 36.0 / (37.0 - reps), 1)
    return round(weight_kg * (1.0 + reps / 30.0), 1)


def explain_1rm(weight_kg: float, reps: int) -> dict | None:
    """
    Return step-by-step 1RM explanation for transparency (formula, math string, result, citation).
    Returns None if inputs are invalid.
    """
    if reps < 1 or weight_kg <= 0:
        return None
    if reps == 1:
        return {
            "formula": "Actual single",
            "math": f"{weight_kg} (weight as-is)",
            "result": round(weight_kg, 1),
            "citation": "Direct measurement; no prediction equation.",
            "note": "For 1 rep, your 1RM equals the weight lifted.",
        }
    if reps <= 10:
        result = round(weight_kg * 36.0 / (37.0 - reps), 1)
        return {
            "formula": "Brzycki (Preferred for 1–10 reps)",
            "math": f"{weight_kg} × 36 / (37 − {reps})",
            "result": result,
            "citation": "Brzycki (1993). Equation for 1RM prediction.",
            "note": "Brzycki is most accurate for 1–10 reps; accuracy drops above 10 reps.",
        }
    result = round(weight_kg * (1.0 + reps / 30.0), 1)
    return {
        "formula": "Epley (Preferred for reps > 10)",
        "math": f"{weight_kg} × (1 + {reps} / 30)",
        "result": result,
        "citation": "Epley (1985). Equation for 1RM prediction.",
        "note": "Brzycki is more accurate for 1–10 reps; Epley is used for higher rep ranges to avoid over-estimation of max force.",
    }


def compute_ewma_acwr(
    daily_loads: list[tuple[date, float]],
    acute_window: int = 7,
    chronic_window: int = 28,
    acwr_thresholds: dict[str, float] | None = None,
) -> list[dict]:
    """
    Compute ACWR using Exponentially Weighted Moving Averages.

    EWMA decay λ = 2 / (N + 1) per Qin et al. (2025) and cited refs (Research Papers/ACWR.pdf),
    providing a more sensitive indicator of injury likelihood than rolling averages.
    Standard windows: acute = 7 days, chronic = 28 days.

    Parameters
    ----------
    daily_loads : sorted list of (date, total_training_load) pairs.
                  Rest days should be included as (date, 0.0).
    acute_window : days for the acute period (default 7).
    chronic_window : days for the chronic period (default 28).
    acwr_thresholds : optional dict with undertrained_max, optimal_max, caution_max
                      (defaults: 0.80, 1.30, 1.50). Override from powerglide.toml for user tuning.

    Returns
    -------
    List of dicts with keys: date, acute, chronic, acwr, zone, mature.
    ACWR is only meaningful after chronic_window days of data.
    """
    if not daily_loads:
        return []

    lambda_a = 2.0 / (acute_window + 1)
    lambda_c = 2.0 / (chronic_window + 1)

    thresholds = acwr_thresholds or {}
    ut = thresholds.get("undertrained_max", _DEFAULT_ACWR_UNDERTRAINED_MAX)
    opt = thresholds.get("optimal_max", _DEFAULT_ACWR_OPTIMAL_MAX)
    cau = thresholds.get("caution_max", _DEFAULT_ACWR_CAUTION_MAX)

    results: list[dict] = []
    ewma_a: float | None = None
    ewma_c: float | None = None

    for i, (d, load) in enumerate(daily_loads):
        if i == 0:
            ewma_a = load
            ewma_c = load
        else:
            ewma_a = load * lambda_a + (1 - lambda_a) * ewma_a  # type: ignore[operator]
            ewma_c = load * lambda_c + (1 - lambda_c) * ewma_c  # type: ignore[operator]

        acwr = ewma_a / ewma_c if ewma_c and ewma_c > 0 else None  # type: ignore[operator]

        zone = _classify_acwr(acwr, undertrained_max=ut, optimal_max=opt, caution_max=cau)

        results.append({
            "date": d,
            "acute": round(ewma_a, 2),  # type: ignore[arg-type]
            "chronic": round(ewma_c, 2),  # type: ignore[arg-type]
            "acwr": round(acwr, 3) if acwr is not None else None,
            "zone": zone,
            "mature": i >= chronic_window,
        })

    return results


def _classify_acwr(
    acwr: float | None,
    undertrained_max: float = _DEFAULT_ACWR_UNDERTRAINED_MAX,
    optimal_max: float = _DEFAULT_ACWR_OPTIMAL_MAX,
    caution_max: float = _DEFAULT_ACWR_CAUTION_MAX,
) -> str:
    if acwr is None:
        return "insufficient_data"
    if acwr < undertrained_max:
        return "undertrained"
    if acwr <= optimal_max:
        return "optimal"
    if acwr <= caution_max:
        return "caution"
    return "danger"


def compute_volume_distribution(
    sets_with_muscles: list[dict],
) -> dict[str, float]:
    """
    Compute volume distribution across muscle groups from a list of sets.

    Each dict in sets_with_muscles must have:
        weight_kg, reps, muscle_group, coefficient

    Returns {muscle_group_name: total_weighted_volume}.
    """
    dist: dict[str, float] = {}
    for s in sets_with_muscles:
        vol = s["weight_kg"] * s["reps"] * s["coefficient"]
        group = s["muscle_group"]
        dist[group] = dist.get(group, 0.0) + vol
    return {k: round(v, 1) for k, v in sorted(dist.items(), key=lambda x: -x[1])}


def fill_rest_days(
    sparse_loads: list[tuple[date, float]],
) -> list[tuple[date, float]]:
    """Fill gaps in a sparse daily load series with 0.0 for rest days."""
    if not sparse_loads:
        return []

    filled: list[tuple[date, float]] = []
    load_map = dict(sparse_loads)
    start = min(d for d, _ in sparse_loads)
    end = max(d for d, _ in sparse_loads)

    current = start
    while current <= end:
        filled.append((current, load_map.get(current, 0.0)))
        current += timedelta(days=1)

    return filled
