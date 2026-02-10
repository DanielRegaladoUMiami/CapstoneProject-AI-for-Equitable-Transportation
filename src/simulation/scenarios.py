"""
What-if scenario simulation engine.

Sprint 3a: Lightweight parameter-based simulations
for evaluating proposed service changes.
"""

import pandas as pd


# ── Predefined Scenarios ──────────────────────────────────────────

SCENARIOS = {
    "increase_frequency": {
        "description": "Increase Route X frequency by 50%",
        "parameter": "route_frequency",
        "adjustment": 1.5,
    },
    "add_stop": {
        "description": "Add a new stop at Location Y",
        "parameter": "stop_count",
        "adjustment": "+1",
    },
    "extend_hours": {
        "description": "Extend service hours in Neighborhood Z",
        "parameter": "service_hours",
        "adjustment": "+4",
    },
}


def apply_scenario(baseline_df, scenario_name, **kwargs):
    """
    Apply a what-if scenario by adjusting parameters
    and recalculating accessibility/equity metrics.
    
    Args:
        baseline_df: Current state data
        scenario_name: Key from SCENARIOS dict or custom
        **kwargs: Override parameters
    
    Returns:
        Modified DataFrame with updated metrics
    """
    # TODO: Implement in Sprint 3a
    pass


def compare_scenarios(baseline_df, scenario_results):
    """
    Compare scenario outputs against baseline.
    Quantify improvements in wait times, accessibility, coverage.
    """
    # TODO: Implement in Sprint 3a
    pass
