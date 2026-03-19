# Session Start Checklist
1. Read this file (auto-loaded)
2. Read `tasks/lessons.md` for mistake patterns to avoid
3. Check the [CURRENT] sprint below to know where we are
4. Read `tasks/todo.md` for detailed sub-sprint specs if working on implementation

---

# Project Overview

**Deloitte Capstone — AI for Equitable Public Transportation, Miami-Dade County**

Design an AI system to predict transit access gaps and emerging equity issues. Deliverables: EDA, Prediction Model, Simulation Model, Interactive Dashboard.

## Key Files

| File | Description |
|------|-------------|
| `Sprint 2/Sprint2_Equity_Indicators_v3_tract.csv` | Master dataset: 512 tracts × 43 cols, 7 equity indicators + composite scores |
| `Sprint 2/Sprint2_Composite_Equity_Indicators_v3.ipynb` | v3 notebook (tract-level indicators) |
| `Sprint 2/Sprint2_Equity_Results_Overview_v3.xlsx` | 4-sheet results workbook |
| `Sprint 2/ACS Tract Level Data/Census_MiamiDade_Tracts_Combined_Clean.csv` | ACS 2023 5-Year, 707 tracts, 56 vars |
| `Sprint 1 EDAs/transit_data.xlsx` | GTFS: 128 routes, 6,530 stops, 943K stop-times, 24,529 trips |
| `MiamiDadeMpoAllAccessGpkg-expanded/` | GeoPackage: 36,507 blocks, auto/transit/bike accessibility |
| `Sprint 2/tab20_tract20_tract10_st12.txt` | Census 2010→2020 tract crosswalk (Florida) |
| `Sprint2b_Feature_Engineering.ipynb` | 2b.1–2b.3: GTFS features, ACS trend slopes, feature consolidation → outputs `Sprint2b_Modeling_Features_NotebookOutput.csv` |
| `Sprint 2 /ACS Tract Level Data/ACS_MiamiDade_Tracts_2024.csv` | Patched 2024 ACS 5-Year, tract-level (corrected DP codes for hispanic, black, asian, foreign_born) |
| `Sprint 2 /Sprint2b_ACS_TimeSeries.ipynb` | 2b.2 + 2b.6: 6-year ACS panel (2019-2024), per-tract trend slopes, 2027 risk projection, fragile tract flagging |
| `Sprint 2 /Sprint2b_Modeling_Features_NotebookOutput.csv` | Modeling-ready dataset: 504 tracts × 61 cols, all features (GTFS + ACS trends + spatial + interactions) + equity target |
| `Sprint 2 /Sprint2b_Modeling_RiskScoring.ipynb` | 2b.4–2b.7: Access Deficit models (regression + XGBoost), risk scoring, GTFS sensitivity |
| `tasks/todo.md` | Detailed sub-sprint specs, results, observations |
| `tasks/lessons.md` | Mistake patterns and rules to prevent recurrence |

---

# Project Plan and Status

## Sprint 1 — EDA [DONE]
## Sprint 2a — Composite Equity Indicators [DONE]

Key decisions: tract-level (not block), multiplicative composite (Need × Access Deficit), 2010→2020 crosswalk for 100% ACS match, unmatched tracts dropped, institutional 98xx tracts flagged.

## Sprint 2b — Predictive Modeling [CURRENT]

Key decision: Original single-model approach (predict equity_priority_score from all features) was circular — target is a formula built from the predictor features. Revised to two-model split: Need side (TimeSeries notebook `Sprint2b_ACS_TimeSeries.ipynb`, demographic projections) × Access Deficit side (Modeling notebook `Sprint2b_Modeling_RiskScoring.ipynb`, transit features → composite_access_deficit). See tasks/todo.md for full rationale.

- [x] 2b.1 — GTFS feature engineering (headways, service span, frequency by time band, weekend gap, route diversity)
- [x] 2b.2 — Multi-year ACS pull (2019-2024 vintages from Census API, 6-year panel, compute temporal trend slopes)
- [x] 2b.3 — Feature consolidation (demographics + trends + GTFS metrics + spatial + interactions)
- [ ] 2b.4 — Access Deficit regression model (target = composite_access_deficit, transit/spatial features only, coefficient table)
- [ ] 2b.5 — Access Deficit ML model (XGBoost, same target/features, Sprint 3 simulation engine)
- [ ] 2b.6 — Risk scoring (projected_need from TimeSeries × predicted_access_deficit, flag fragile tracts)
- [ ] 2b.7 — Validation and reporting (cross-val, residuals, GTFS sensitivity analysis, model comparison)

## Sprint 3 — Simulation Engine [PENDING]

- [ ] 3.1 — Define simulation parameters (map user levers to both models: GTFS params → Access Deficit, demographic scenarios → Need)
- [ ] 3.2 — Build simulator (two-model pipeline: modify either side → recombine projected_need × predicted_access_deficit → new equity score)
- [ ] 3.3 — Scenario validation (3-5 reference scenarios testing both sides, sanity-check)

## Sprint 4 — Interactive Dashboard [PENDING]

- [ ] 4.1 — Dashboard design (map + controls for both need/access sides + decomposition view + before/after)
- [ ] 4.2 — Build core dashboard (Plotly Dash or Streamlit)
- [ ] 4.3 — Integrate simulation (user adjusts GTFS params and/or demographic scenarios → both models update → equity score responds)
- [ ] 4.4 — Alerts and recommendations (fragile tracts from both models, trend projections, export)

## Deliverable Mapping

| Deloitte Requirement | Sprint | Status |
|---|---|---|
| Exploratory Data Analysis | 1 | DONE |
| Prediction Model Results | 2b | CURRENT |
| Simulation Model Results | 3 | PENDING |
| Interactive Dashboard | 4 | PENDING |

---

# Environment

- **Primary IDE**: VS Code (local). Used for most coding tasks.
- **Colab**: Used only for GPU-dependent workloads (model training) or one-off throwaway tasks (small data pulls like ACS fetches) to avoid polluting the local file system.
- **Python**: 3.9.6
- When writing code or instructions, assume VS Code / local execution unless the task specifically requires GPU or is a disposable one-off.

---

# Rules

## Workflow
- Plan before building. STOP and re-plan if something goes sideways.
- Use subagents for research, exploration, parallel analysis. One task per subagent.
- After ANY correction: update `tasks/lessons.md`. Review lessons at session start.
- Never mark a task complete without proving it works.
- For non-trivial changes: pause and ask "is there a more elegant way?"
- When given a bug: just fix it autonomously. Zero hand-holding.

## Data Integrity Gate (MANDATORY)
- Before starting ANY implementation: verify that all required data/materials are available and sufficient for the task.
- If data is missing, incomplete, or suspect: STOP. Do not proceed. Flag to Luna:
  1. What is missing and why it's needed
  2. How it affects the task if we proceed without it
  3. Specific guidance on where to obtain it (exact source, URL, API, file format)
- Never fill gaps with assumptions, synthetic data, or workarounds without explicit approval.
- This applies to data files, API access, reference materials, shapefiles, external datasets — anything the task depends on.

## Expert Judgment Gate (MANDATORY)
- If the current approach, task, or direction is wrong, inefficient, or irrelevant given the project goals: STOP and flag it immediately.
- Explain: what's wrong, why, and what a better approach would be.
- DO NOT implement the flagged task or the alternative until Luna explicitly confirms the direction.
- On confirmation: update CLAUDE.md (plan/status) and tasks/todo.md (specs) to reflect the agreed change, THEN proceed with implementation.
- This applies to: model choices, feature engineering decisions, data handling strategies, sprint scope, deliverable framing — any technical or strategic decision.

## Sprint Status Tracking (MANDATORY)
- When a sub-sprint is completed, ASK Luna two things before updating this file:
  1. **Confirm completion:** "Can I mark [sub-sprint] as done?"
  2. **Confirm key files:** "Which files should I log in the Key Files table for this task?" (list the candidates you think are relevant — Luna confirms or corrects)
- On confirmation: check off `[x]`, update sprint status labels (CURRENT → DONE), and update the Key Files table to add new outputs / remove superseded files
- When all sub-sprints in a sprint are confirmed: move [CURRENT] to next sprint
- NEVER mark done without Luna's explicit confirmation
- NEVER leave stale file references in the Key Files table — if a file was superseded or discarded, remove it
- At session start: read this file first to know where we are

## Notebook Standards (.ipynb)
1. Changelog as first cell (version history: what, when, why)
2. Numbered section headers (## 1. Data Loading, ## 2. Feature Engineering, etc.)
3. Markdown before every code cell explaining reasoning, not just description. State what you're doing, why, and what you expect — but also connect it to prior outputs (example:"From the correlation matrix we saw X, so now we do Y"). This requires building the notebook cell-by-cell with live outputs guiding each next step, not writing a generic template end-to-end.
4. Markdown after key outputs interpreting findings for the project AND explaining what they imply for the next step. Think like a senior data scientist reasoning through a problem — assess mid-process outputs, flag surprises, adjust course. The notebook should read as an analytical narrative, not a sequence of disconnected steps.
5. Mature, simple code. Comments only where not self-explanatory.
6. No dead code, no debugging artifacts.

## Core Principles
- **Simplicity First**: Minimal changes, minimal code.
- **No Laziness**: Root causes only. Senior developer standards.
- **No Guessing**: Never hardcode derivable values. Query the data. Investigate the unexpected.
- **Track Everything**: For each model/change: what was implemented, rationale, expected results, insights.
