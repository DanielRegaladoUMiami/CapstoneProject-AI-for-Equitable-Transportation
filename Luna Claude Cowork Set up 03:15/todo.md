# Sprint 2a: Composite Equity Indicators — COMPLETE

- [x] Approach report (.docx) with Luna's walk-to-job vs walk-to-transit correction
- [x] Block-level v2 (superseded by tract-level v3)
- [x] Tract-level v3: 512 tracts, 7 indicators, equity priority score
- [x] Results overview workbook (.xlsx, 4 sheets)
- [x] Census 2010→2020 crosswalk → 100% real ACS match
- [x] Quality filter: dropped 12 unmatched tracts (6 non-MD + 6 institutional 98xx)

### Key Results (v3)
| Indicator | Median | Std |
|-----------|--------|-----|
| Transit Dependency | 0.097 | 0.074 |
| Temporal Mismatch | 0.442 | 0.203 |
| Structural Access Gap | 0.294 | 0.127 |
| Time Tax | 0.413 | 0.191 |
| Service Coverage | 0.635 | 0.095 |
| Economic Vulnerability | 0.244 | 0.077 |
| Multimodal Deficit | 0.955 | 0.142 |
| **Equity Priority** | **0.095** | **—** |

### Tier Distribution
Critical: 53 (10.2%), High: 104 (19.9%), Moderate: 156 (29.9%), Low: 209 (40.0%)

### Data Observations
1. Tract 12086980700 (98xx): 82.5% poverty, 57% no vehicle — Dade Correctional Institution. Flagged institutional.
2. Tract 12086008904: 100% poverty, 100% no vehicle, 3 housing units — likely group quarters.
3. Overtown scores Low: strong transit access (170K-235K transit jobs, 30+ stops). High need but low access deficit.

---

# Sprint 2b: Predictive Modeling — CURRENT

## 2b.1 — GTFS Feature Engineering
Compute granular transit service metrics from 943K stop-time records:
- **Headway per stop**: avg minutes between consecutive arrivals, by time-of-day band (peak 6-9AM, midday 9AM-3PM, evening 3-7PM, late 7PM-midnight)
- **Service span per stop**: first arrival to last departure (hours of operation)
- **Frequency by time band per tract**: trips/hour at peak, midday, evening, late
- **Weekend vs weekday service gap**: ratio of Saturday/Sunday trips to weekday trips per tract
- **Route diversity per tract**: unique routes + unique headsigns (destination diversity)
- Spatial join: stops (lat/lon) → tracts via point-in-polygon

These serve dual purpose: predictive features for ML AND adjustable parameters for Sprint 3 simulation.

## 2b.2 — Multi-Year ACS Data Pull
Pull 2019-2024 ACS 5-Year vintages from Census API (same variables as current ACS):
- poverty_rate, no_vehicle, snap_benefits, rent_burden, unemployment, commute_transit, etc.
- Compute per-tract temporal trend slopes (linear regression of each variable over 6 years)
- Output: trend_poverty_slope, trend_rent_burden_slope, trend_no_vehicle_slope, etc.
- Note: ACS 2024 5-Year estimates were pulled specifically for this sprint; 6-year panel (2019-2024)

## 2b.3 — Feature Consolidation
Combine into one modeling dataset:
- Current demographics (from 2a master CSV)
- Temporal trend slopes (from 2b.2)
- GTFS service metrics (from 2b.1)
- Spatial features (neighboring tract mean scores, distance to nearest high-service tract)
- Interaction terms (poverty × transit_desert, headway × no_vehicle_rate, rent_burden_slope × low_service)

## 2b.4 — Access Deficit Regression Model (REVISED)

**Approach change:** Original plan predicted equity_priority_score from all features. This was circular — the
target is a formula we built from the predictor features, so the model just recovered our own weight
assignments. Revised to predict composite_access_deficit (the transit infrastructure side only) from
transit/spatial features. This is non-circular: the model discovers which service parameters most drive
access gaps. Demographics enter only at the combination step via the TimeSeries notebook's need projections.

- Target: composite_access_deficit (already in Sprint2b_Modeling_Features_NotebookOutput.csv)
- Predictor features (transit/infrastructure only):
  - GTFS service: headway_early_min, headway_peak_am_min, freq_early_tph, freq_peak_am_tph,
    weekend_weekday_ratio, unique_routes, unique_stops, rail_trip_share, stop_count, route_count
  - Accessibility: transit_jobs_30_mean, auto_jobs_30_mean
  - Spatial: neighbor_mean_equity_score, neighbor_mean_headway_peak, n_neighbors
  - Transit-relevant trends: trend_commute_public_transit_pct, trend_commute_drove_alone_pct,
    trend_commute_wfh_pct, trend_mean_commute_time_min
- Excluded (define Need, not Access): poverty, no_vehicle, SNAP, rent burden, unemployment,
  demographic trends, demographic interaction terms
- Approach: OLS baseline → Lasso/Ridge/ElasticNet → coefficient table
- Reference files: Sprint2b_Modeling_Features_NotebookOutput.csv

## 2b.5 — Access Deficit ML Model (REVISED)
- Same target and features as 2b.4, XGBoost
- This is the Sprint 3 simulation engine: modify GTFS inputs → re-predict access deficit
- Feature importance (permutation/SHAP) tells planners which service levers matter most
- Key validation: GTFS sensitivity test — lower headway by 5 min, add routes, etc. and verify
  the model produces plausible, non-trivial access deficit changes
- Reference files: same as 2b.4

## 2b.6 — Risk Scoring (REVISED)
- In same modeling notebook, load TimeSeries output and combine both halves:
  - Projected Need ← TimeSeries notebook (Sprint2b_ACS_TimeSeries.ipynb output)
  - Predicted Access Deficit ← Access Deficit model from 2b.5
  - Projected Equity Score = projected_need × predicted_access_deficit
- Flag fragile tracts: Moderate/High tracts where either side is worsening
- Note: depends on TimeSeries notebook being finalized
- Reference files: TimeSeries notebook outputs, Access Deficit model from 2b.5,
  Sprint2_Equity_Indicators_v3_tract.csv (current tier assignments)

## 2b.7 — Validation and Reporting (REVISED)
- Cross-validation for Access Deficit models
- Residual analysis: are certain tract types systematically mispredicted?
- Feature importance plots for the access deficit model
- GTFS sensitivity analysis: simulate small service changes, verify plausible access deficit responses
- Model comparison table (regression vs XGBoost)
- Document the circularity issue and two-model split rationale (for Deloitte deliverable)
- Reference files: all model outputs from 2b.4–2b.6

---

# Sprint 3: Simulation Engine — PENDING

## 3.1 — Define Simulation Parameters (REVISED)
Two sets of user-adjustable levers matching the two-model architecture:

Access Deficit side (feeds Access Deficit ML model from 2b.5):
- Headway changes → modify headway_early_min, headway_peak_am_min
- Frequency changes → modify freq_early_tph, freq_peak_am_tph
- Stop additions/removals → modify stop_count, unique_stops per tract
- Route additions → modify route_count, unique_routes
- Weekend service parity → modify weekend_weekday_ratio
- Rail expansion → modify rail_trip_share

Need side (feeds through TimeSeries need projections):
- Demographic scenario changes → "what if poverty rises/falls X% in tract Y?"
- Economic shifts → "what if median income changes by $Z?"
- Population changes → "what if tract gains/loses N residents?"
These modify the projected need component from the TimeSeries notebook.

Note: transit_jobs_30_mean (job accessibility) is NOT directly adjustable — it's a downstream
outcome of service changes. If 2b.5 shows it's a dominant predictor, consider building a
sub-model mapping GTFS changes → transit_jobs changes (scope TBD based on 2b.7 sensitivity results).

## 3.2 — Build the Simulator (REVISED)
Two-model prediction pipeline:
1. Access Deficit side: modify GTFS features in target tracts → Access Deficit model re-predicts composite_access_deficit
2. Need side: apply demographic scenario changes → recompute composite_need from TimeSeries projections
3. Combine: new_equity_score = updated_need × updated_access_deficit

Input: proposed changes on either or both sides (which tracts, which parameters, by how much)
Output: before/after comparison showing:
  - Access deficit change per tract (if GTFS params modified)
  - Need change per tract (if demographic scenario applied)
  - Equity score change per tract (the combined effect)
  - Tier shifts (how many tracts change tier)
  - Affected population

Use cases:
- Transit planning: "add a route here" → access deficit drops → equity improves
- Trend projection: "poverty rises 2% over 3 years" → need increases → equity worsens
- Combined: "add a route AND poverty rises" → see net effect on equity

## 3.3 — Scenario Validation (REVISED)
Run 3-5 reference scenarios testing BOTH sides:

Access-side scenarios:
- "Halve peak headway in all Critical tracts"
- "Add 5 bus stops to each transit desert tract"
- "Achieve weekend service parity county-wide"

Need-side scenarios:
- "Poverty rises 3% in all currently-Moderate tracts" (stress test)
- "Income drops $5K in fragile tracts identified in 2b.6"

Combined scenario:
- "Add a new route to top-5 underserved tracts while poverty rises 2%"

For each scenario, verify:
  - Access deficit and need changes are plausible (direction and magnitude)
  - Equity score changes reflect the multiplication correctly
  - Tier shifts are sensible
Document results with tract-level detail.
Reference files: Access Deficit model from 2b.5, TimeSeries need projections,
Sprint2_Equity_Indicators_v3_tract.csv (current tiers)

---

# Sprint 4: Interactive Dashboard — PENDING

## 4.1 — Dashboard Design (REVISED)
Layout reflecting the two-model architecture:
- Choropleth map: equity scores by tract, toggle between need/access deficit/composite views
- Tier summary panel with count and population per tier
- Tract detail drill-down: show need score, access deficit score, and which side drives the equity score
- Simulation control panel with TWO sections:
  - Transit levers: GTFS parameter sliders (headway, frequency, stops, routes, weekend parity)
  - Demographic scenarios: sliders or dropdowns for poverty change, income change, population shift
- Before/after comparison view: side-by-side maps showing access deficit, need, and equity changes
- Trend alerts panel: fragile tracts from risk scoring (2b.6), projected need changes from TimeSeries

## 4.2 — Build Core Dashboard (REVISED)
Plotly Dash or Streamlit. Core views:
- Map: tract coloring by tier/score, filter by neighborhood/tier/indicator
- Need vs Access Deficit decomposition: for any tract, show which side drives the equity score
  (high need + low access deficit vs low need + high access deficit → different interventions needed)
- Click-to-inspect tract profiles with demographic summary, GTFS service summary, trend direction

## 4.3 — Integrate Simulation (REVISED)
Connect Sprint 3 simulator to dashboard UI:
- User adjusts transit parameters (access side) and/or demographic scenarios (need side)
- Access Deficit model re-predicts per tract; Need recomputed from scenario
- Combined: updated_need × updated_access_deficit = new equity score
- Map and scores update in real time, before/after side-by-side
- Show decomposed deltas: "access deficit changed by X, need changed by Y, equity changed by Z"
- Highlights where transit improvements have the most equity impact (where need is also high)

## 4.4 — Alerts and Recommendations (REVISED)
- Surface fragile tracts from 2b.6 risk scoring (both need-worsening and access-worsening)
- Display Access Deficit model feature importance as actionable recommendations
  ("lowering headway has 3× more impact than adding stops in this tract")
- Trend projections: show which tracts are projected to worsen over 2-3 years (TimeSeries)
- Intervention prioritization: rank tracts by "equity improvement per dollar" using both models
- Export capability: filtered tract lists, simulation results, trend reports
Reference files: all Sprint 2b and 3 outputs
