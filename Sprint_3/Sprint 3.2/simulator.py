"""
Sprint 3 — Transit Equity Simulation Engine (v1)
=================================================

Clean, importable module for Sprint 4 dashboard integration.
No Jupyter dependencies. Requires: pandas, numpy, xgboost, joblib.

Architecture
------------
User adjusts transit-service levers (4 parameters) →
XGBoost v3 re-predicts service_deficit per tract →
Proportional-change ratio (new / baseline) →
Apply ratio to Sprint 2a composite_access_deficit →
Multiply by composite_need (static) →
Updated equity_priority_score → tier via fixed cutoffs.

Key Design Decisions
--------------------
1. **Re-prediction approach**: The simulator re-predicts BOTH baseline and
   scenario deficit from scratch using the same XGBoost model pipeline.
   The proportional ratio (scenario / baseline) is perfectly self-consistent
   regardless of any minor numerical differences between the pkl model's
   predictions and the stored deficit_predicted values. The stored values
   came from a 507-tract training context; we operate on 504 tracts.
   See Sprint3_1_Summary.pdf §Scale Mismatch for full rationale.

2. **Unscaled features**: XGBoost v3 was trained on raw (unscaled) features.
   The StandardScaler (Sprint2b_Scaler_v3.pkl) was for Ridge regression only.
   Simulator does NOT apply scaling before XGBoost prediction.

3. **Headway auto-derived**: headway = 60 / frequency. Not user-facing.
   When freq ≤ 0, headway caps at 120 min (matching training data convention).

4. **Need side is static**: composite_need from Sprint 2a is held fixed.
   Demographic stress-tests deferred to v2 (see Sprint 3/future/).

5. **Tier assignment**: Uses Sprint 2a fixed quartile cutoffs from the
   baseline equity_priority_score distribution.

Usage
-----
    from simulator import Simulator

    sim = Simulator()  # loads from relative paths by default
    result = sim.run(
        access_deltas={'freq_peak_am_tph': 2.0},
        tract_filter='all',
        label='S1: Peak Freq +2 tph'
    )
    print(result.summary)
    print(result.tract_df.head())
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Union

import joblib
import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FEATURE_NAMES = [
    "headway_early_min",
    "headway_peak_am_min",
    "freq_early_tph",
    "freq_peak_am_tph",
    "weekend_weekday_ratio",
    "rail_trip_share",
    "neighbor_mean_equity_score",
    "neighbor_mean_headway_peak",
    "n_neighbors",
    "trend_commute_public_transit_pct",
    "trend_commute_drove_alone_pct",
    "trend_commute_wfh_pct",
    "trend_mean_commute_time_min",
]

# Frequency → headway derivation pairs
FREQ_HEADWAY_PAIRS = {
    "freq_peak_am_tph": "headway_peak_am_min",
    "freq_early_tph": "headway_early_min",
}

HEADWAY_CAP = 120.0  # minutes, applied when freq ≤ 0 (matches training data)

TIER_LABELS = ["Low", "Moderate", "High", "Critical"]


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

@dataclass
class SimulationResult:
    """Immutable container returned by Simulator.run()."""

    tract_df: pd.DataFrame
    """Per-tract DataFrame: tract_geoid, deficit_before, deficit_after,
    equity_before, equity_after, tier_before, tier_after, equity_delta."""

    tier_shifts: pd.DataFrame
    """4×4 matrix (rows = tier_before, cols = tier_after, values = tract counts)."""

    summary: Dict[str, float]
    """Aggregate stats: n_tracts, n_improved, n_worsened, n_tier_upgrades,
    n_tier_downgrades, avg_deficit_delta, avg_equity_delta."""

    label: str = ""
    """Scenario name for display."""


# ---------------------------------------------------------------------------
# Simulator
# ---------------------------------------------------------------------------

class Simulator:
    """
    Transit equity simulation engine.

    Loads the Sprint 3 baseline state, XGBoost v3 model, and lever catalog.
    Exposes a single public method ``run()`` that accepts access-side deltas
    and returns a SimulationResult.

    Parameters
    ----------
    baseline_path : path to Sprint3_Baseline_State.csv
    model_path : path to Sprint2b_XGBoost_v3.pkl
    lever_catalog_path : path to Sprint3_Lever_Catalog.json
    """

    def __init__(
        self,
        baseline_path: Optional[str] = None,
        model_path: Optional[str] = None,
        lever_catalog_path: Optional[str] = None,
    ):
        # Resolve default paths relative to this file's directory
        here = Path(__file__).resolve().parent
        sprint2 = here.parent / "Sprint 2 "

        self._baseline_path = Path(baseline_path) if baseline_path else here / "Sprint3_Baseline_State.csv"
        self._model_path = Path(model_path) if model_path else sprint2 / "Sprint2b_XGBoost_v3.pkl"
        self._lever_path = Path(lever_catalog_path) if lever_catalog_path else here / "Sprint3_Lever_Catalog.json"

        # Load assets
        self._baseline = pd.read_csv(self._baseline_path)
        self._model = joblib.load(self._model_path)
        with open(self._lever_path) as f:
            self._lever_catalog = json.load(f)

        # Pre-compute baseline predictions (re-predicted for self-consistency)
        self._features_base = self._baseline[FEATURE_NAMES].copy()
        self._deficit_base = self._model.predict(self._features_base)

        # Extract static columns
        self._composite_need = self._baseline["composite_need"].values
        self._composite_access_deficit = self._baseline["composite_access_deficit"].values
        self._equity_base = self._baseline["equity_priority_score"].values
        self._tract_geoids = self._baseline["tract_geoid"].values

        # Compute tier cutoffs from baseline equity distribution (Sprint 2a quartiles)
        self._tier_cutoffs = self._compute_tier_cutoffs()

        # Build lever lookup for validation
        self._lever_features = {
            lv["feature"]: lv for lv in self._lever_catalog["levers"]
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(
        self,
        access_deltas: Optional[Dict[str, float]] = None,
        tract_filter: Union[str, List[int]] = "all",
        label: str = "scenario",
    ) -> SimulationResult:
        """
        Run a simulation scenario.

        Parameters
        ----------
        access_deltas : dict
            Mapping of lever feature names to delta values.
            Example: {'freq_peak_am_tph': 2.0, 'weekend_weekday_ratio': 0.1}
        tract_filter : 'all' or list of tract_geoid ints
            Which tracts to apply the deltas to. Unaffected tracts keep
            baseline values unchanged.
        label : str
            Human-readable scenario name.

        Returns
        -------
        SimulationResult
        """
        if access_deltas is None:
            access_deltas = {}

        # Validate deltas against lever catalog
        self._validate_deltas(access_deltas)

        # Step 1: Apply deltas to feature matrix
        features_scenario = self._apply_access_deltas(access_deltas, tract_filter)

        # Step 2: Re-predict deficit for scenario
        deficit_scenario = self._model.predict(features_scenario)

        # Step 3: Compute updated equity via proportional-change
        equity_scenario, tier_scenario = self._compute_equity(deficit_scenario)

        # Step 4: Build result
        tier_base = self._assign_tiers(self._equity_base)
        return self._build_result(
            deficit_scenario, equity_scenario, tier_base, tier_scenario, label
        )

    @property
    def n_tracts(self) -> int:
        return len(self._baseline)

    @property
    def lever_names(self) -> List[str]:
        return list(self._lever_features.keys())

    @property
    def baseline_df(self) -> pd.DataFrame:
        """Read-only copy of the baseline state."""
        return self._baseline.copy()

    # ------------------------------------------------------------------
    # Internal pipeline
    # ------------------------------------------------------------------

    def _apply_access_deltas(
        self, deltas: Dict[str, float], tract_filter: Union[str, List[int]]
    ) -> pd.DataFrame:
        """
        Copy the baseline feature matrix, apply deltas to specified tracts,
        auto-derive headways, and clamp to valid ranges.
        """
        features = self._features_base.copy()
        mask = self._resolve_tract_mask(tract_filter)

        for feat, delta in deltas.items():
            features.loc[mask, feat] = features.loc[mask, feat] + delta

        # Auto-derive headways from updated frequencies (only affected tracts)
        for freq_feat, hw_feat in FREQ_HEADWAY_PAIRS.items():
            if freq_feat in deltas:
                freq_vals = features.loc[mask, freq_feat].values
                features.loc[mask, hw_feat] = np.where(
                    freq_vals > 0, 60.0 / freq_vals, HEADWAY_CAP
                )

        # Clamp all lever features (and their derived features) to data_range
        for lever_info in self._lever_catalog["levers"]:
            feat = lever_info["feature"]
            lo, hi = lever_info["data_range"]
            features[feat] = features[feat].clip(lo, hi)

        # Clamp derived headways to their observed ranges
        # headway_peak_am_min: [0.26, 120] (from 60/227.67 to cap)
        # headway_early_min: [2.18, 120] (from 60/27.5 to cap)
        features["headway_peak_am_min"] = features["headway_peak_am_min"].clip(0.0, HEADWAY_CAP)
        features["headway_early_min"] = features["headway_early_min"].clip(0.0, HEADWAY_CAP)

        return features

    def _compute_equity(
        self, deficit_scenario: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Proportional-change approach:
          ratio = deficit_scenario / deficit_baseline
          new_access_deficit = composite_access_deficit × ratio
          new_equity = composite_need × new_access_deficit
        """
        # Guard against division by zero (tracts with zero baseline deficit)
        safe_base = np.maximum(self._deficit_base, 1e-10)
        ratio = deficit_scenario / safe_base

        new_access_deficit = self._composite_access_deficit * ratio
        new_equity = self._composite_need * new_access_deficit

        # Clamp equity to [0, 1] (composites are both 0-1)
        new_equity = np.clip(new_equity, 0.0, 1.0)

        tiers = self._assign_tiers(new_equity)
        return new_equity, tiers

    def _assign_tiers(self, equity_scores: np.ndarray) -> np.ndarray:
        """Assign tier labels using Sprint 2a fixed cutoffs."""
        tiers = np.full(len(equity_scores), "", dtype=object)
        for i, label in enumerate(TIER_LABELS):
            lo = self._tier_cutoffs[i]
            hi = self._tier_cutoffs[i + 1]
            if i < len(TIER_LABELS) - 1:
                mask = (equity_scores >= lo) & (equity_scores < hi)
            else:
                mask = equity_scores >= lo  # Critical: includes upper bound
            tiers[mask] = label
        return tiers

    def _compute_tier_cutoffs(self) -> List[float]:
        """
        Derive tier cutoffs from baseline equity distribution.
        Sprint 2a used quartile-based tiers, so we reconstruct the boundaries
        from the baseline tier assignments + equity scores.
        """
        df = self._baseline[["equity_priority_score", "equity_tier"]].copy()
        cutoffs = [0.0]
        for tier in TIER_LABELS:
            tier_max = df.loc[df["equity_tier"] == tier, "equity_priority_score"].max()
            cutoffs.append(tier_max)
        # Extend the Critical upper bound to capture any scenario-inflated scores
        cutoffs[-1] = max(cutoffs[-1], 1.0)
        return cutoffs

    def _build_result(
        self,
        deficit_scenario: np.ndarray,
        equity_scenario: np.ndarray,
        tier_base: np.ndarray,
        tier_scenario: np.ndarray,
        label: str,
    ) -> SimulationResult:
        """Assemble the SimulationResult from arrays."""

        tract_df = pd.DataFrame({
            "tract_geoid": self._tract_geoids,
            "deficit_before": self._deficit_base,
            "deficit_after": deficit_scenario,
            "deficit_delta": deficit_scenario - self._deficit_base,
            "equity_before": self._equity_base,
            "equity_after": equity_scenario,
            "equity_delta": equity_scenario - self._equity_base,
            "tier_before": tier_base,
            "tier_after": tier_scenario,
            "composite_need": self._composite_need,
            "composite_access_deficit": self._composite_access_deficit,
            "is_fragile": self._baseline["flag_fragile"].values,
            "is_worsening": self._baseline["flag_worsening"].values,
        })

        # Tier shift matrix (4×4)
        tier_shifts = pd.crosstab(
            pd.Categorical(tier_base, categories=TIER_LABELS),
            pd.Categorical(tier_scenario, categories=TIER_LABELS),
            rownames=["tier_before"],
            colnames=["tier_after"],
        )

        # Summary stats
        n_improved = int((equity_scenario < self._equity_base - 1e-8).sum())
        n_worsened = int((equity_scenario > self._equity_base + 1e-8).sum())

        tier_order = {t: i for i, t in enumerate(TIER_LABELS)}
        tier_base_idx = np.array([tier_order.get(t, -1) for t in tier_base])
        tier_scen_idx = np.array([tier_order.get(t, -1) for t in tier_scenario])
        n_upgrades = int((tier_scen_idx < tier_base_idx).sum())     # moved to lower tier
        n_downgrades = int((tier_scen_idx > tier_base_idx).sum())   # moved to higher tier

        summary = {
            "n_tracts": len(self._baseline),
            "n_improved": n_improved,
            "n_worsened": n_worsened,
            "n_unchanged": len(self._baseline) - n_improved - n_worsened,
            "n_tier_upgrades": n_upgrades,
            "n_tier_downgrades": n_downgrades,
            "avg_deficit_delta": float(np.mean(deficit_scenario - self._deficit_base)),
            "avg_equity_delta": float(np.mean(equity_scenario - self._equity_base)),
            "max_equity_improvement": float(np.min(equity_scenario - self._equity_base)),
        }

        return SimulationResult(
            tract_df=tract_df,
            tier_shifts=tier_shifts,
            summary=summary,
            label=label,
        )

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    def _validate_deltas(self, deltas: Dict[str, float]) -> None:
        """Ensure all deltas reference valid lever features."""
        for feat in deltas:
            if feat not in self._lever_features:
                valid = ", ".join(self._lever_features.keys())
                raise ValueError(
                    f"'{feat}' is not an adjustable lever. "
                    f"Valid levers: {valid}"
                )

    def _resolve_tract_mask(self, tract_filter: Union[str, List[int]]) -> np.ndarray:
        """Return a boolean mask over the 504-tract baseline."""
        if isinstance(tract_filter, str) and tract_filter.lower() == "all":
            return np.ones(len(self._baseline), dtype=bool)

        if isinstance(tract_filter, (list, np.ndarray)):
            return self._baseline["tract_geoid"].isin(tract_filter).values

        raise ValueError(
            f"tract_filter must be 'all' or a list of tract_geoid ints, "
            f"got {type(tract_filter)}"
        )
