"""
Extended outcome metrics for the simulator — plug into the SimulationResult
to answer Deloitte's business questions directly:

  1. Wait-time savings per trip, per tract, in minutes
     E[wait | uniform arrivals] = headway / 2
     wait_saved = (headway_before - headway_after) / 2

  2. Ridership-change proxy (cited service elasticity)
     Transit ridership has documented elasticity to frequency in the
     0.5-0.8 range for peak-hour service improvements (see APTA
     "Understanding Transit Ridership Dynamics"; TCRP Report 95,
     chapter 9; Taylor et al. 2009). We use the midpoint 0.65.

     pct_ridership_change ≈ elasticity * pct_frequency_change
     absolute_delta ≈ pct_ridership_change * baseline_trips
     We express this per-tract as an index scaled by the tract's
     current peak AM trips/hr (our best per-tract supply signal).

Both metrics are reported per-tract AND aggregated county-wide. They use
only data already in the simulator — no new datasets required.

Honesty caveat (surfaced in the app About page):
  - Wait savings math is exact for uniform arrivals, deterministic.
  - Ridership change is an elasticity *proxy*, not a boardings model.
    Without APC/farebox data per-stop, this is the defensible ceiling.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# Literature defaults (APTA / TCRP mid-range)
FREQUENCY_ELASTICITY = 0.65      # short-run, peak AM
RAIL_SUBSTITUTION_FACTOR = 1.2   # rail trips are longer, higher ridership impact
WEEKEND_WEEKDAY_ELASTICITY = 0.4 # weekend service has lower elasticity


def wait_time_saved_min(
    baseline_headway_peak: pd.Series,
    scenario_headway_peak: pd.Series,
) -> pd.Series:
    """
    Per-tract expected wait time saved per trip at AM peak.
    Positive values = time saved.
    """
    before = baseline_headway_peak.clip(lower=0)
    after = scenario_headway_peak.clip(lower=0)
    return ((before - after) / 2.0).round(2)


def _pct(series_after, series_before, min_denom=1.0, max_change=2.0):
    """
    Safe percentage change with a physical denominator floor.

    Tracts with near-zero baseline service shouldn't yield "infinite %"
    when a bus is added. We floor the denominator at `min_denom`
    (e.g., 1 trip/hr = 60 min headway, the effective lower bound for
    meaningful frequency) and cap the result at `max_change` (+200%).
    """
    denom = np.maximum(series_before, min_denom)
    raw = (series_after - series_before) / denom
    return raw.clip(-1.0, max_change)


def ridership_change_pct(
    baseline_features: pd.DataFrame,
    scenario_features: pd.DataFrame,
) -> pd.Series:
    """
    Percent change in ridership per tract via service elasticity.

    Combines three lever effects with their respective elasticities,
    then returns a single % change per tract.
    """
    # Physically grounded denominator floors:
    #   peak freq: 1 trip/hr (60-min headway is the service-cap in training data)
    #   weekend ratio: 0.1 (any meaningful service; max is 1.0 so % bounded)
    #   rail share: 0.01 (1% rail share is the floor where adding trips makes sense)
    pct_peak = _pct(
        scenario_features["freq_peak_am_tph"],
        baseline_features["freq_peak_am_tph"],
        min_denom=1.0,
    )
    pct_weekend = _pct(
        scenario_features["weekend_weekday_ratio"],
        baseline_features["weekend_weekday_ratio"],
        min_denom=0.1,
    )
    pct_rail = _pct(
        scenario_features["rail_trip_share"],
        baseline_features["rail_trip_share"],
        min_denom=0.01,
    )

    total = (
        FREQUENCY_ELASTICITY * pct_peak
        + WEEKEND_WEEKDAY_ELASTICITY * pct_weekend
        + RAIL_SUBSTITUTION_FACTOR * pct_rail
    )
    # Final cap on combined per-tract ridership change. Even the most
    # aggressive real-world interventions (BRT launches, rail extensions)
    # rarely produce >100% ridership in a single tract. -50% floor is a
    # realistic lower bound for cut-service scenarios.
    total = total.clip(-0.5, 1.0)
    return (total * 100).round(2)


def extended_summary(
    result,
    baseline_features: pd.DataFrame,
    scenario_features: pd.DataFrame,
) -> dict:
    """
    Produce a dict of business-impact metrics from a SimulationResult.

    Keys:
      avg_wait_saved_min     : average per-tract wait-time savings (min/trip)
      max_wait_saved_min     : best-case tract
      avg_ridership_pct      : average % ridership increase across tracts
      n_tracts_ridership_up  : count of tracts with positive ridership response
      affected_headway_hist  : histogram of headway changes for chart
    """
    wait_saved = wait_time_saved_min(
        baseline_features["headway_peak_am_min"],
        scenario_features["headway_peak_am_min"],
    )
    pct_change = ridership_change_pct(baseline_features, scenario_features)

    return {
        "avg_wait_saved_min": float(wait_saved.mean()),
        "max_wait_saved_min": float(wait_saved.max()),
        "n_tracts_wait_improved": int((wait_saved > 0.01).sum()),
        "avg_ridership_pct": float(pct_change.mean()),
        "n_tracts_ridership_up": int((pct_change > 0.5).sum()),
        "max_ridership_pct": float(pct_change.max()),
        "wait_saved_series": wait_saved,
        "ridership_pct_series": pct_change,
    }
