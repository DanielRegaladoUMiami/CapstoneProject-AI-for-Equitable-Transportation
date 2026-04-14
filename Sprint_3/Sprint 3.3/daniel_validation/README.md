# Sprint 3.3 — Validation & Gradio Bug-Fixes (Daniel's working folder)

This folder contains the **primary Deloitte deliverable** for Sprint 3.3 plus
bug-fixes for Lina's Gradio V3. Built after reviewing Luna's Sprint 3 Plan v3
(Apr 9) and the team's Apr 9–14 commits.

## What's in here

| File | Purpose |
|---|---|
| `Sprint3_Scenario_Validation.ipynb` | Primary Deloitte deliverable per plan §3.3. Runs S1–S5 through Luna's simulator, tier-shift matrices, direction tests, pass-criteria checks. |
| `Sprint3_Scenario_Results.csv` | 504 × 23. Replaces Lina's CSV with per-scenario scopes respected per plan. |
| `Sprint_3_Gradio_V3_fixed.ipynb` | Lina's Gradio V3 with 4 bugs patched so it actually talks to Luna's simulator. |
| `simulator.py` | Fork of Luna's Sprint 3.2 simulator **only** to fix the default-path bug. Original in `Sprint 3.2/` left untouched. |
| `build_validation_notebook.py` | Generator for `Sprint3_Scenario_Validation.ipynb` (regen if scenarios change). |

## What I did NOT modify

- `Sprint 3/Sprint 3.2/simulator.py` — Luna's original. Fork lives here with a path fix.
- `Sprint 3/Sprint 3.3/Sprint_3_Gradio_V3.ipynb` — Lina's original. Fixed copy lives here.
- `Sprint 3/Sprint 3.3/Sprint3_Scenario_Results.csv` — Lina's CSV kept for comparison.
- Anyone else's code or data.

## Bugs fixed in Lina's Gradio V3

1. `sim.run(need_deltas={}, ...)` → Luna's `run()` doesn't accept this kwarg. Removed.
2. Summary keys: `n_upgrades`, `n_downgrades`, `avg_delta`, `pop_affected` → Luna's simulator returns `n_tier_upgrades`, `n_tier_downgrades`, `avg_equity_delta`. Mapped. `pop_affected` replaced with scope size.
3. `df["fragile_flag"]` → baseline column is `flag_fragile`. Global rename.
4. `df["risk_tier"]` → plan/simulator use `equity_tier` (Sprint 2a fixed cutoffs, not Sprint 2b risk scoring). Global rename. This is what makes the Critical/High/Moderate/Low scope filters match the plan's 51/153/504 cohorts.

## Fix in simulator.py (default paths only)

Luna's Sprint 3.2 `simulator.py` has:
```python
sprint2 = sprint3.parent / "Sprint 2 "   # with space; folder doesn't exist
self._model_path = ... or sprint2 / "Sprint2b_XGBoost_v3.pkl"
```

Repo layout is `Sprint_2/Sprint_2b/Sprint2b_XGBoost_v3.pkl`. Fork fixes the
default path so `Simulator()` works without passing every argument. Original
`simulator.py` in `Sprint 3.2/` is unchanged — explicit paths still work there.

## Pass criteria (plan §3.3) — 4 of 5 pass

| Criterion | Result |
|---|---|
| S1 > S3 magnitude (SHAP ranking) | PASS (0.0028 vs 0.0016) |
| S5 > any single component | PASS (0.026 vs max 0.012) |
| S4 ≥ 95% tracts improve | PASS (96.6%) |
| Equity in [0,1] + valid tiers, all 5 scenarios | PASS |
| S4 largest single-lever county-wide | **FAIL** — S2 dominates |

### On the S4 vs S2 failure

**Not a bug.** The plan asserts S4 (rail +0.10) is the largest single-lever per
the 2b.5 what-if, but **S2 is specified as a target (`weekend_ratio → 0.80`), not
a uniform +0.10 delta**. Mean baseline `weekend_ratio` is 0.43, so S2's effective
per-tract delta averages +0.37 — a much larger intervention than S4's +0.10.
Of course it dominates.

Options for team:
1. Accept as finding — document that target-based scenarios dominate fixed-delta
   scenarios by intervention size, not by lever efficiency per unit.
2. Normalize S2 to a comparable delta (e.g., +0.10 on current value).
3. Adjust plan language: "largest among fixed-delta levers".

Also worth flagging: **S2 worsens 57 tracts** — the 76 tracts with `weekend_ratio`
above 0.80 get equalized down, hurting them. Team should decide if S2 is
"improve-only" or "equalize".

## How to run

```bash
cd "Sprint_3/Sprint 3.3/daniel_validation"
# Validation notebook — produces Sprint3_Scenario_Results.csv
jupyter nbconvert --to notebook --execute Sprint3_Scenario_Validation.ipynb \
  --output Sprint3_Scenario_Validation.ipynb

# Gradio dashboard
jupyter notebook Sprint_3_Gradio_V3_fixed.ipynb
# (requires Sprint3_Baseline_State.csv, Sprint2b_XGBoost_v3.pkl, Sprint3_Lever_Catalog.json
#  colocated — same assumption as Lina's original)
```
