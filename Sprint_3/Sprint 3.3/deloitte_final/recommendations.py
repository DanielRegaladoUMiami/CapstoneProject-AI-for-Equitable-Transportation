"""
Per-tract recommendations engine.

Given a target tract (typically Critical or High), evaluates candidate
intervention levers and ranks them by expected equity improvement using
the existing simulator. Returns top-N concrete actions with expected
wait-time savings, ridership change, and tier-shift outcome.

Designed to make the Gradio 'Recommendations' tab actionable:
  "For tract 12086000220, the highest-impact intervention is
   +2 tph on peak AM, which would:
     • Cut wait time by 7 min per trip
     • Increase ridership by ~9.1%
     • Move the tract from Critical to High"

Works on top of Simulator.run() — no retraining, no new data.
"""
from __future__ import annotations

from typing import List, Dict

import numpy as np
import pandas as pd

from extended_metrics import wait_time_saved_min, ridership_change_pct


# Candidate interventions. Each row = single-lever change that a
# planner can actually execute with a work order.
CANDIDATES = [
    {"key": "peak_1",   "lever": "freq_peak_am_tph",       "delta": 1.0,   "label": "+1 bus/hr AM peak"},
    {"key": "peak_2",   "lever": "freq_peak_am_tph",       "delta": 2.0,   "label": "+2 buses/hr AM peak"},
    {"key": "peak_4",   "lever": "freq_peak_am_tph",       "delta": 4.0,   "label": "+4 buses/hr AM peak"},
    {"key": "wknd_10",  "lever": "weekend_weekday_ratio",  "delta": 0.10,  "label": "+10pp weekend service"},
    {"key": "wknd_20",  "lever": "weekend_weekday_ratio",  "delta": 0.20,  "label": "+20pp weekend service"},
    {"key": "early_1",  "lever": "freq_early_tph",         "delta": 1.0,   "label": "+1 bus/hr 5–7am"},
    {"key": "rail_5",   "lever": "rail_trip_share",        "delta": 0.05,  "label": "+5pp rail modal share"},
    {"key": "rail_10",  "lever": "rail_trip_share",        "delta": 0.10,  "label": "+10pp rail modal share"},
]


def evaluate_single_lever(sim, run_fn, tract_geoid: int, lever: str, delta: float):
    """Run the simulator with a uniform delta applied only to the target tract."""
    result = run_fn(deltas={lever: delta}, tract_filter=[tract_geoid], label=f"{lever}{delta:+g}")
    # pull row for that tract
    row = result.tract_df.loc[result.tract_df["tract_geoid"] == tract_geoid].iloc[0]
    return result, row


def recommend_for_tract(
    sim,
    run_fn,
    tract_geoid: int,
    baseline: pd.DataFrame,
    top_n: int = 3,
) -> List[Dict]:
    """
    Return top-N candidate interventions for a single tract, ranked by
    equity improvement magnitude.
    """
    bl_row = baseline.loc[baseline["tract_geoid"].astype(int) == int(tract_geoid)].iloc[0]
    base_headway = bl_row["headway_peak_am_min"]
    base_peak_freq = bl_row["freq_peak_am_tph"]

    results = []
    for cand in CANDIDATES:
        try:
            res, row = evaluate_single_lever(sim, run_fn, int(tract_geoid), cand["lever"], cand["delta"])
        except Exception:
            continue

        delta_equity = float(row["equity_after"] - row["equity_before"])
        delta_deficit = float(row["deficit_after"] - row["deficit_before"])
        tier_before = row["tier_before"]
        tier_after = row["tier_after"]

        # Extended metrics per-tract
        scenario_features = sim._features_base.copy()
        mask = sim._resolve_tract_mask([int(tract_geoid)])
        scenario_features.loc[mask, cand["lever"]] = (
            scenario_features.loc[mask, cand["lever"]] + cand["delta"]
        )
        # Derive headway consistently with simulator internals (60/freq).
        # The stored headway_peak_am_min field can disagree with
        # freq_peak_am_tph (it's a cross-route average), which creates
        # spurious "wait saved" when only the frequency is changed.
        # Use freq-derived headway on both sides for self-consistency.
        if cand["lever"] == "freq_peak_am_tph":
            base_freq = max(base_peak_freq, 0.001)
            new_freq = max(base_peak_freq + cand["delta"], 0.001)
            base_hdy = min(60.0 / base_freq, 120.0)
            new_hdy = min(60.0 / new_freq, 120.0)
            wait_saved = (base_hdy - new_hdy) / 2.0
        elif cand["lever"] == "freq_early_tph":
            early_base_freq = max(bl_row["freq_early_tph"], 0.001)
            early_new_freq = max(bl_row["freq_early_tph"] + cand["delta"], 0.001)
            base_hdy = min(60.0 / early_base_freq, 120.0)
            new_hdy = min(60.0 / early_new_freq, 120.0)
            wait_saved = (base_hdy - new_hdy) / 2.0
        else:
            wait_saved = 0.0

        ridership_pct = float(ridership_change_pct(
            sim._features_base.loc[mask],
            scenario_features.loc[mask],
        ).iloc[0])

        results.append({
            "lever_key": cand["key"],
            "lever": cand["lever"],
            "delta": cand["delta"],
            "label": cand["label"],
            "delta_equity": delta_equity,
            "delta_deficit": delta_deficit,
            "tier_before": tier_before,
            "tier_after": tier_after,
            "tier_changed": tier_before != tier_after,
            "wait_saved_min": round(wait_saved, 2),
            "ridership_pct": round(ridership_pct, 1),
        })

    # Rank by magnitude of equity improvement (smaller = better, since
    # equity score is risk-like)
    results.sort(key=lambda r: r["delta_equity"])
    return results[:top_n]


def recommend_countywide_top_levers(
    sim,
    run_fn,
    critical_tracts: List[int],
    top_n: int = 5,
) -> pd.DataFrame:
    """
    Aggregate: for each candidate intervention applied county-wide,
    how many Critical tracts move to High or better?
    """
    rows = []
    for cand in CANDIDATES:
        res = run_fn(
            deltas={cand["lever"]: cand["delta"]},
            tract_filter=critical_tracts,
            label=f"countywide_{cand['key']}",
        )
        df = res.tract_df
        crit_df = df[df["tract_geoid"].astype(int).isin(critical_tracts)]
        moved_out = int((crit_df["tier_after"] != "Critical").sum())
        avg_def = float(crit_df["deficit_delta"].mean())
        rows.append({
            "intervention": cand["label"],
            "lever": cand["lever"],
            "delta": cand["delta"],
            "critical_tracts_moved_out": moved_out,
            "avg_deficit_change": round(avg_def, 4),
        })
    out = pd.DataFrame(rows).sort_values("critical_tracts_moved_out", ascending=False).head(top_n)
    return out.reset_index(drop=True)
