"""
Builder for Sprint3_Scenario_Validation.ipynb — the primary Deloitte deliverable
for Sprint 3.3 per Luna's v3 plan. Emits a clean .ipynb with 5 scenario runs,
tier-shift matrices, pass-criteria checks, and the output CSV.

Run: python3 build_validation_notebook.py
"""
from __future__ import annotations
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "Sprint3_Scenario_Validation.ipynb"


def md(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": text.splitlines(keepends=True)}


def code(text: str) -> dict:
    return {
        "cell_type": "code",
        "metadata": {},
        "execution_count": None,
        "outputs": [],
        "source": text.splitlines(keepends=True),
    }


cells = []

cells.append(md("""\
# Sprint 3.3 — Scenario Validation Notebook

**Primary Deloitte deliverable** per Luna's Sprint 3 Plan v3 (Apr 9, 2026).

Runs the 5 reference scenarios (S1–S5) through Luna's Sprint 3.2 `Simulator`,
verifies direction, magnitude, and tier logic, and emits `Sprint3_Scenario_Results.csv`
with proper per-scenario scopes.

**Plan pass criteria:**
1. All validation gates in `test_simulator.py` pass
2. S1–S3 directions consistent with SHAP rankings (|S1| > |S3| per-tract deficit delta)
3. S4 produces the largest single-lever county-wide deficit improvement (98% tracts)
4. S5 combined delta > any single component
5. No scenario produces equity scores outside [0, 1] or invalid tiers

**Note:** This notebook uses a local fork of `simulator.py` in this folder with the
default-path bug fixed (original in `Sprint 3/Sprint 3.2/` is untouched).
"""))

cells.append(code("""\
# Imports & setup
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
from pathlib import Path

from simulator import Simulator, SimulationResult, TIER_LABELS, FEATURE_NAMES, FREQ_HEADWAY_PAIRS, HEADWAY_CAP

sim = Simulator()
baseline = sim.baseline_df
print(f'Loaded: {sim.n_tracts} tracts, {len(sim.lever_names)} levers')
print(f'Levers: {sim.lever_names}')
"""))

cells.append(md("""\
## Tract scopes per plan

- S1 (Peak frequency boost) → **Critical tracts** (~51)
- S2 (Weekend parity → 0.80) → **All 504 tracts**
- S3 (Early service expansion) → **High + Critical** (~153)
- S4 (Rail modal shift) → **All 504 tracts**
- S5 (Combined multi-lever) → **Critical + High** (~153)
"""))

cells.append(code("""\
CRITICAL_TRACTS = baseline.loc[baseline['equity_tier'] == 'Critical', 'tract_geoid'].tolist()
HIGH_CRITICAL_TRACTS = baseline.loc[baseline['equity_tier'].isin(['High', 'Critical']), 'tract_geoid'].tolist()

print(f'Critical tracts:       {len(CRITICAL_TRACTS)}')
print(f'High + Critical:       {len(HIGH_CRITICAL_TRACTS)}')
print(f'All tracts:            {sim.n_tracts}')
"""))

cells.append(md("""\
## Helper: target-value scenarios

Luna's `Simulator.run()` accepts uniform deltas applied to a tract mask. Scenario S2
(and S5's weekend component) is specified as *"set weekend_weekday_ratio to 0.80"*,
which is a **per-tract target**, not a uniform delta.

This helper computes the per-tract feature matrix directly, re-predicts deficit with
the same XGBoost model, and reuses `Simulator`'s proportional-change equity logic
and tier cutoffs — no re-implementation of the core math.
"""))

cells.append(code("""\
def run_scenario(sim, *, deltas=None, targets=None, tract_filter='all', label=''):
    '''
    Extended scenario runner that supports both uniform deltas and per-tract targets.

    deltas  : dict {feature: delta}        — same semantics as Simulator.run()
    targets : dict {feature: target_value} — set feature to this value in-scope
    '''
    deltas = deltas or {}
    targets = targets or {}

    # Reuse Simulator's mask logic
    mask = sim._resolve_tract_mask(tract_filter)
    features = sim._features_base.copy()

    # Apply deltas
    for feat, delta in deltas.items():
        if feat not in sim._lever_features:
            raise ValueError(f"'{feat}' is not an adjustable lever")
        features.loc[mask, feat] = features.loc[mask, feat] + delta

    # Apply targets
    for feat, target in targets.items():
        if feat not in sim._lever_features:
            raise ValueError(f"'{feat}' is not an adjustable lever")
        features.loc[mask, feat] = target

    # Auto-derive headways for any frequency that changed
    touched_freqs = set(deltas) | set(targets)
    for freq_feat, hw_feat in FREQ_HEADWAY_PAIRS.items():
        if freq_feat in touched_freqs:
            freq_vals = features.loc[mask, freq_feat].values
            features.loc[mask, hw_feat] = np.where(freq_vals > 0, 60.0 / freq_vals, HEADWAY_CAP)

    # Clamp lever features to data_range
    for lv in sim._lever_catalog['levers']:
        lo, hi = lv['data_range']
        features[lv['feature']] = features[lv['feature']].clip(lo, hi)
    features['headway_peak_am_min'] = features['headway_peak_am_min'].clip(0.0, HEADWAY_CAP)
    features['headway_early_min']   = features['headway_early_min'].clip(0.0, HEADWAY_CAP)

    # Predict + reuse Simulator's equity/tier logic
    deficit_scenario = sim._model.predict(features)
    equity_scenario, tier_scenario = sim._compute_equity(deficit_scenario)
    tier_base = sim._assign_tiers(sim._equity_base)
    return sim._build_result(deficit_scenario, equity_scenario, tier_base, tier_scenario, label)


def print_summary(r):
    s = r.summary
    print(f"  n_improved:         {s['n_improved']}")
    print(f"  n_worsened:         {s['n_worsened']}")
    print(f"  n_tier_upgrades:    {s['n_tier_upgrades']}")
    print(f"  n_tier_downgrades:  {s['n_tier_downgrades']}")
    print(f"  avg_deficit_delta:  {s['avg_deficit_delta']:+.6f}")
    print(f"  avg_equity_delta:   {s['avg_equity_delta']:+.6f}")
"""))

cells.append(md("""\
## S1 — Peak frequency boost on Critical tracts

Lever: `freq_peak_am_tph +2 trips/hr`  (SHAP #1, 39.6%)
Scope: Critical tracts (~51)
Expected: deficit drops in Critical; some tier upgrades Critical → High.
"""))

cells.append(code("""\
r_s1 = run_scenario(sim, deltas={'freq_peak_am_tph': 2.0}, tract_filter=CRITICAL_TRACTS, label='S1')
print('S1 — Peak frequency boost +2 tph on Critical')
print_summary(r_s1)
print()
print('Tier shift matrix (rows = before, cols = after):')
print(r_s1.tier_shifts)
"""))

cells.append(md("""\
## S2 — Weekend parity → 0.80 on all tracts

Target: `weekend_weekday_ratio = 0.80` for all 504 tracts  (SHAP #2, 21.7%)
Expected: broad improvement; tracts with low current ratio improve most.
"""))

cells.append(code("""\
r_s2 = run_scenario(sim, targets={'weekend_weekday_ratio': 0.80}, tract_filter='all', label='S2')
print('S2 — Weekend parity -> 0.80 on all 504')
print_summary(r_s2)
print()
print('Tier shift matrix:')
print(r_s2.tier_shifts)

# Sanity: tracts below 0.80 should improve most
below_thresh = baseline['weekend_weekday_ratio'] < 0.80
print(f"\\nTracts below 0.80 baseline: {below_thresh.sum()}  |  above or equal: {(~below_thresh).sum()}")
"""))

cells.append(md("""\
## S3 — Early service expansion on High + Critical

Lever: `freq_early_tph +1 trip/hr`  (SHAP #3, 6.9%)
Scope: High + Critical (~153)
Expected: shift-worker tracts benefit. |S1| > |S3| in per-tract deficit delta.
"""))

cells.append(code("""\
r_s3 = run_scenario(sim, deltas={'freq_early_tph': 1.0}, tract_filter=HIGH_CRITICAL_TRACTS, label='S3')
print('S3 — Early freq +1 on High + Critical')
print_summary(r_s3)
print()
print('Tier shift matrix:')
print(r_s3.tier_shifts)
"""))

cells.append(md("""\
## S4 — Rail modal shift on all tracts

Lever: `rail_trip_share +0.10`  (what-if: largest single-lever county-wide impact)
Scope: All 504 tracts
Expected: largest single-lever deficit drop; ~98% tracts improve.
"""))

cells.append(code("""\
r_s4 = run_scenario(sim, deltas={'rail_trip_share': 0.10}, tract_filter='all', label='S4')
print('S4 — Rail +0.10 on all 504')
print_summary(r_s4)
print()
print('Tier shift matrix:')
print(r_s4.tier_shifts)

pct_improved = (r_s4.tract_df['deficit_delta'] < 0).sum() / sim.n_tracts * 100
print(f"\\nPct tracts with deficit improvement: {pct_improved:.1f}%  (plan: ~98%)")
"""))

cells.append(md("""\
## S5 — Combined multi-lever on High + Critical

Levers: `freq_peak_am +2`, `weekend → 0.80`, `rail +0.05`
Scope: High + Critical (~153)
Expected: combined delta > any single-lever component.
"""))

cells.append(code("""\
r_s5 = run_scenario(
    sim,
    deltas={'freq_peak_am_tph': 2.0, 'rail_trip_share': 0.05},
    targets={'weekend_weekday_ratio': 0.80},
    tract_filter=HIGH_CRITICAL_TRACTS,
    label='S5',
)
print('S5 — Combined peak+2, weekend->0.80, rail+0.05 on High + Critical')
print_summary(r_s5)
print()
print('Tier shift matrix:')
print(r_s5.tier_shifts)
"""))

cells.append(md("""\
## Pass-criteria validation (plan §3.3 "Pass criteria")
"""))

cells.append(code("""\
checks = {}

# (2) |S1| > |S3| per-tract deficit delta (SHAP ranking consistency)
# Compare on the overlap: tracts affected by S3 (High + Critical) include all S1 (Critical) + rest of High.
# Per the plan, this is an aggregate |avg_deficit_delta| check.
s1_abs = abs(r_s1.summary['avg_deficit_delta'])
s3_abs = abs(r_s3.summary['avg_deficit_delta'])
checks['S1 > S3 magnitude'] = (s1_abs > s3_abs, f'|S1|={s1_abs:.6f}, |S3|={s3_abs:.6f}')

# (3) S4 largest single-lever county-wide deficit improvement
s4_abs = abs(r_s4.summary['avg_deficit_delta'])
s2_abs = abs(r_s2.summary['avg_deficit_delta'])
# Single-lever candidates evaluated county-wide: we compare S4 (all) vs S2 (all)
# S1 and S3 are on restricted scopes so direct comparison of avg deltas is apples-to-oranges;
# re-run S1 and S3 county-wide for the magnitude check.
r_s1_all = run_scenario(sim, deltas={'freq_peak_am_tph': 2.0}, tract_filter='all', label='S1_all')
r_s3_all = run_scenario(sim, deltas={'freq_early_tph': 1.0}, tract_filter='all', label='S3_all')
all_single_lever = {
    'S1_all (peak+2)':     abs(r_s1_all.summary['avg_deficit_delta']),
    'S2 (weekend->0.80)':  s2_abs,
    'S3_all (early+1)':    abs(r_s3_all.summary['avg_deficit_delta']),
    'S4 (rail+0.10)':      s4_abs,
}
largest = max(all_single_lever, key=all_single_lever.get)
checks['S4 largest single-lever (county-wide)'] = (largest == 'S4 (rail+0.10)', all_single_lever)

# (3b) S4 ~98% tracts improve
pct_s4 = (r_s4.tract_df['deficit_delta'] < 0).sum() / sim.n_tracts * 100
checks['S4 >= 95% tracts improve'] = (pct_s4 >= 95, f'{pct_s4:.1f}%')

# (4) S5 combined delta > any single component (on S5 scope = High + Critical)
components = {
    'peak+2':   run_scenario(sim, deltas={'freq_peak_am_tph': 2.0}, tract_filter=HIGH_CRITICAL_TRACTS, label='peak'),
    'weekend':  run_scenario(sim, targets={'weekend_weekday_ratio': 0.80}, tract_filter=HIGH_CRITICAL_TRACTS, label='wk'),
    'rail+.05': run_scenario(sim, deltas={'rail_trip_share': 0.05}, tract_filter=HIGH_CRITICAL_TRACTS, label='rail'),
}
s5_abs = abs(r_s5.summary['avg_deficit_delta'])
comp_max = max(abs(r.summary['avg_deficit_delta']) for r in components.values())
checks['S5 > any single component'] = (
    s5_abs > comp_max,
    {k: f'{abs(v.summary[\"avg_deficit_delta\"]):.6f}' for k, v in components.items()} | {'S5': f'{s5_abs:.6f}'}
)

# (5) Equity bounds + valid tiers across ALL scenarios
all_ok = True
bounds_info = {}
for name, r in [('S1', r_s1), ('S2', r_s2), ('S3', r_s3), ('S4', r_s4), ('S5', r_s5)]:
    eq_min = r.tract_df['equity_after'].min()
    eq_max = r.tract_df['equity_after'].max()
    invalid_tiers = (~r.tract_df['tier_after'].isin(TIER_LABELS)).sum()
    ok = (eq_min >= 0) and (eq_max <= 1) and (invalid_tiers == 0)
    all_ok &= ok
    bounds_info[name] = f'[{eq_min:.3f}, {eq_max:.3f}]  invalid_tiers={invalid_tiers}'
checks['equity in [0,1] and tiers valid'] = (all_ok, bounds_info)

# Report
print('=' * 70)
print('PASS CRITERIA RESULTS')
print('=' * 70)
for name, (ok, info) in checks.items():
    mark = 'PASS' if ok else 'FAIL'
    print(f'[{mark}] {name}')
    if isinstance(info, dict):
        for k, v in info.items():
            print(f'         {k}: {v}')
    else:
        print(f'         {info}')
    print()

overall = all(ok for ok, _ in checks.values())
print('=' * 70)
print(f'OVERALL: {\"ALL CRITERIA PASS\" if overall else \"SOME CRITERIA FAIL\"}')
print('=' * 70)
"""))

cells.append(md("""\
## Direction gates re-check (mirrors test_simulator.py)

Final sanity: increasing each lever (county-wide) must reduce average deficit.
"""))

cells.append(code("""\
direction_checks = {}
for lever, delta in [
    ('freq_peak_am_tph', 2.0),
    ('weekend_weekday_ratio', 0.1),
    ('rail_trip_share', 0.10),
    ('freq_early_tph', 1.0),
]:
    r = run_scenario(sim, deltas={lever: delta}, tract_filter='all', label=f'dir_{lever}')
    direction_checks[f'{lever} +{delta}'] = r.summary['avg_deficit_delta']
    mark = 'PASS' if r.summary['avg_deficit_delta'] < 0 else 'FAIL'
    print(f'[{mark}] {lever:+<25} +{delta}: avg_deficit_delta = {r.summary[\"avg_deficit_delta\"]:+.6f}')
"""))

cells.append(md("""\
## Build Sprint3_Scenario_Results.csv (corrected)

Replaces Lina's CSV: respects per-scenario scopes from the plan and uses the
canonical simulator output.
"""))

cells.append(code("""\
def scenario_cols(r, prefix):
    return pd.DataFrame({
        f'{prefix}_equity_new':  r.tract_df['equity_after'].values,
        f'{prefix}_tier_new':    r.tract_df['tier_after'].values,
        f'{prefix}_deficit_new': r.tract_df['deficit_after'].values,
    }, index=r.tract_df['tract_geoid'].values)

base_cols = pd.DataFrame({
    'tract_geoid':               r_s1.tract_df['tract_geoid'].values,
    'tier_baseline':             r_s1.tract_df['tier_before'].values,
    'equity_baseline':           r_s1.tract_df['equity_before'].values,
    'composite_need':            r_s1.tract_df['composite_need'].values,
    'composite_access_deficit':  r_s1.tract_df['composite_access_deficit'].values,
    'deficit_baseline':          r_s1.tract_df['deficit_before'].values,
    'flag_fragile':              r_s1.tract_df['is_fragile'].values,
    'flag_worsening':            r_s1.tract_df['is_worsening'].values,
}).set_index('tract_geoid')

out = base_cols.copy()
for r, name in [(r_s1, 'S1'), (r_s2, 'S2'), (r_s3, 'S3'), (r_s4, 'S4'), (r_s5, 'S5')]:
    out = out.join(scenario_cols(r, name))
out = out.reset_index()

out_path = Path('Sprint3_Scenario_Results.csv')
out.to_csv(out_path, index=False)
print(f'Wrote: {out_path}  ({out.shape[0]} tracts x {out.shape[1]} cols)')
out.head()
"""))

cells.append(md("""\
## Per-scenario summary table
"""))

cells.append(code("""\
summary_rows = []
for name, r, scope in [
    ('S1', r_s1, f'Critical ({len(CRITICAL_TRACTS)})'),
    ('S2', r_s2, f'All ({sim.n_tracts})'),
    ('S3', r_s3, f'High+Critical ({len(HIGH_CRITICAL_TRACTS)})'),
    ('S4', r_s4, f'All ({sim.n_tracts})'),
    ('S5', r_s5, f'High+Critical ({len(HIGH_CRITICAL_TRACTS)})'),
]:
    s = r.summary
    summary_rows.append({
        'scenario':         name,
        'scope':            scope,
        'n_improved':       s['n_improved'],
        'n_worsened':       s['n_worsened'],
        'tier_upgrades':    s['n_tier_upgrades'],
        'tier_downgrades':  s['n_tier_downgrades'],
        'avg_deficit_delta': round(s['avg_deficit_delta'], 6),
        'avg_equity_delta':  round(s['avg_equity_delta'], 6),
    })
pd.DataFrame(summary_rows)
"""))

nb = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.12"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

OUT.write_text(json.dumps(nb, indent=1))
print(f"Wrote {OUT}")
