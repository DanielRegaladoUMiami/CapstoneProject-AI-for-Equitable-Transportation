"""
Sprint 3 — Simulator Validation Gates
======================================

Three mandatory gates that must pass before any scenario analysis:

1. **Zero-delta gate**: run() with no deltas → equity unchanged (< 1e-8).
2. **Isolation gate**: apply delta to a tract subset → unaffected tracts
   have exactly zero equity change.
3. **Direction gate**: increasing frequency / weekend ratio / rail share
   → average deficit falls (consistent with SHAP rankings from 2b.5).

Run with:  pytest Sprint\ 3/test_simulator.py -v
"""

import numpy as np
import pytest
from simulator import Simulator


# ---------------------------------------------------------------------------
# Fixture: shared simulator instance (loaded once per session)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def sim():
    """Load the simulator once for all tests in this module."""
    return Simulator()


# ===========================================================================
# Gate 1 — Zero-delta
# ===========================================================================

class TestZeroDelta:
    """No deltas applied → equity scores must match baseline exactly."""

    def test_equity_unchanged(self, sim):
        """Per-tract equity delta must be < 1e-8 with no deltas."""
        result = sim.run(access_deltas={}, label="zero-delta")
        max_diff = np.abs(result.tract_df["equity_delta"]).max()
        assert max_diff < 1e-8, (
            f"Zero-delta equity drift: max |delta| = {max_diff:.2e} (threshold: 1e-8)"
        )

    def test_deficit_unchanged(self, sim):
        """Per-tract deficit delta must be < 1e-8 with no deltas."""
        result = sim.run(access_deltas={}, label="zero-delta")
        max_diff = np.abs(result.tract_df["deficit_delta"]).max()
        assert max_diff < 1e-8, (
            f"Zero-delta deficit drift: max |delta| = {max_diff:.2e}"
        )

    def test_no_tier_shifts(self, sim):
        """No tracts should change tier at zero delta."""
        result = sim.run(access_deltas={}, label="zero-delta")
        changed = (result.tract_df["tier_before"] != result.tract_df["tier_after"]).sum()
        assert changed == 0, f"{changed} tracts changed tier at zero delta"

    def test_summary_zeros(self, sim):
        """Summary stats should all be zero at zero delta."""
        result = sim.run(access_deltas={}, label="zero-delta")
        assert result.summary["n_improved"] == 0
        assert result.summary["n_worsened"] == 0
        assert result.summary["n_tier_upgrades"] == 0
        assert result.summary["n_tier_downgrades"] == 0


# ===========================================================================
# Gate 2 — Isolation
# ===========================================================================

class TestIsolation:
    """Deltas applied to a subset → unaffected tracts must be unchanged."""

    def test_unaffected_tracts_unchanged(self, sim):
        """Apply delta to Critical tracts only; other tracts must have zero change."""
        # Pick Critical tracts from baseline
        baseline = sim.baseline_df
        critical_tracts = baseline.loc[
            baseline["equity_tier"] == "Critical", "tract_geoid"
        ].tolist()

        assert len(critical_tracts) > 0, "No Critical tracts found in baseline"

        result = sim.run(
            access_deltas={"freq_peak_am_tph": 2.0},
            tract_filter=critical_tracts,
            label="isolation-test",
        )

        # Unaffected tracts: those NOT in critical_tracts
        unaffected = result.tract_df[
            ~result.tract_df["tract_geoid"].isin(critical_tracts)
        ]
        max_eq_diff = np.abs(unaffected["equity_delta"]).max()
        max_def_diff = np.abs(unaffected["deficit_delta"]).max()

        assert max_eq_diff < 1e-8, (
            f"Unaffected tract equity changed: max |delta| = {max_eq_diff:.2e}"
        )
        assert max_def_diff < 1e-8, (
            f"Unaffected tract deficit changed: max |delta| = {max_def_diff:.2e}"
        )

    def test_affected_tracts_did_change(self, sim):
        """The targeted tracts should actually change (delta is meaningful)."""
        baseline = sim.baseline_df
        critical_tracts = baseline.loc[
            baseline["equity_tier"] == "Critical", "tract_geoid"
        ].tolist()

        result = sim.run(
            access_deltas={"freq_peak_am_tph": 2.0},
            tract_filter=critical_tracts,
            label="isolation-check",
        )

        affected = result.tract_df[
            result.tract_df["tract_geoid"].isin(critical_tracts)
        ]
        n_changed = (np.abs(affected["deficit_delta"]) > 1e-8).sum()
        assert n_changed > 0, "No Critical tracts changed despite +2 tph delta"


# ===========================================================================
# Gate 3 — Direction
# ===========================================================================

class TestDirection:
    """
    Increasing transit service → deficit should decrease on average.
    Consistent with SHAP rankings and what-if analysis from Sprint 2b.5.
    """

    def test_freq_peak_am_decreases_deficit(self, sim):
        """
        +2 trips/hr peak AM → avg deficit falls.
        SHAP #1: freq_peak_am_tph (39.6% importance, higher = less deficit).
        """
        result = sim.run(
            access_deltas={"freq_peak_am_tph": 2.0},
            label="direction-freq-peak",
        )
        avg_delta = result.summary["avg_deficit_delta"]
        assert avg_delta < 0, (
            f"freq_peak_am +2 tph → avg deficit delta = {avg_delta:.6f} (expected < 0)"
        )

    def test_weekend_ratio_decreases_deficit(self, sim):
        """
        +0.1 weekend/weekday ratio → avg deficit falls.
        SHAP #2: weekend_weekday_ratio (21.7% importance).
        """
        result = sim.run(
            access_deltas={"weekend_weekday_ratio": 0.1},
            label="direction-weekend",
        )
        avg_delta = result.summary["avg_deficit_delta"]
        assert avg_delta < 0, (
            f"weekend_ratio +0.1 → avg deficit delta = {avg_delta:.6f} (expected < 0)"
        )

    def test_rail_share_decreases_deficit(self, sim):
        """
        +0.10 rail trip share → avg deficit falls.
        Largest single lever in what-if: -0.0149 deficit, 98% tracts improve.
        """
        result = sim.run(
            access_deltas={"rail_trip_share": 0.10},
            label="direction-rail",
        )
        avg_delta = result.summary["avg_deficit_delta"]
        assert avg_delta < 0, (
            f"rail_share +0.10 → avg deficit delta = {avg_delta:.6f} (expected < 0)"
        )

    def test_freq_early_decreases_deficit(self, sim):
        """
        +1 trip/hr early AM → avg deficit falls.
        SHAP #3: freq_early_tph (6.9% importance).
        """
        result = sim.run(
            access_deltas={"freq_early_tph": 1.0},
            label="direction-freq-early",
        )
        avg_delta = result.summary["avg_deficit_delta"]
        assert avg_delta < 0, (
            f"freq_early +1 tph → avg deficit delta = {avg_delta:.6f} (expected < 0)"
        )


# ===========================================================================
# Bonus — Structural validation
# ===========================================================================

class TestStructural:
    """Non-gate tests that verify the simulator's structural integrity."""

    def test_invalid_lever_raises(self, sim):
        """Passing a non-lever feature should raise ValueError."""
        with pytest.raises(ValueError, match="not an adjustable lever"):
            sim.run(access_deltas={"poverty_rate_pct": 5.0})

    def test_tract_count(self, sim):
        """Simulator should operate on exactly 504 tracts."""
        assert sim.n_tracts == 504

    def test_result_shape(self, sim):
        """Result tract_df should have 504 rows and expected columns."""
        result = sim.run(access_deltas={"freq_peak_am_tph": 1.0}, label="shape-check")
        assert len(result.tract_df) == 504
        expected_cols = {
            "tract_geoid", "deficit_before", "deficit_after", "deficit_delta",
            "equity_before", "equity_after", "equity_delta",
            "tier_before", "tier_after",
        }
        assert expected_cols.issubset(set(result.tract_df.columns))

    def test_tier_shift_matrix_shape(self, sim):
        """Tier shift matrix should be 4×4."""
        result = sim.run(access_deltas={}, label="matrix-shape")
        assert result.tier_shifts.shape == (4, 4)

    def test_equity_bounds(self, sim):
        """Equity scores should stay in [0, 1] even with large deltas."""
        result = sim.run(
            access_deltas={"freq_peak_am_tph": 10.0, "rail_trip_share": 0.3},
            label="bounds-check",
        )
        eq = result.tract_df["equity_after"].values
        assert eq.min() >= 0.0, f"Equity below 0: {eq.min()}"
        assert eq.max() <= 1.0, f"Equity above 1: {eq.max()}"

    def test_shap_ranking_consistency(self, sim):
        """
        S1 (peak freq boost) should produce larger avg deficit reduction
        than S3 (early freq boost), consistent with SHAP #1 > SHAP #3.
        """
        s1 = sim.run(access_deltas={"freq_peak_am_tph": 2.0}, label="S1")
        s3 = sim.run(access_deltas={"freq_early_tph": 1.0}, label="S3")
        assert abs(s1.summary["avg_deficit_delta"]) > abs(s3.summary["avg_deficit_delta"]), (
            f"SHAP ranking violated: S1 deficit delta ({s1.summary['avg_deficit_delta']:.6f}) "
            f"should be larger than S3 ({s3.summary['avg_deficit_delta']:.6f})"
        )
