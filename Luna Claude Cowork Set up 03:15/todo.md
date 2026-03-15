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
Pull 2019-2023 ACS 5-Year vintages from Census API (same variables as current ACS):
- poverty_rate, no_vehicle, snap_benefits, rent_burden, unemployment, commute_transit, etc.
- Compute per-tract temporal trend slopes (linear regression of each variable over 5 years)
- Output: trend_poverty_slope, trend_rent_burden_slope, trend_no_vehicle_slope, etc.

## 2b.3 — Feature Consolidation
Combine into one modeling dataset:
- Current demographics (from 2a master CSV)
- Temporal trend slopes (from 2b.2)
- GTFS service metrics (from 2b.1)
- Spatial features (neighboring tract mean scores, distance to nearest high-service tract)
- Interaction terms (poverty × transit_desert, headway × no_vehicle_rate, rent_burden_slope × low_service)

## 2b.4 — Regression Model (Interpretable)
- Dependent variable: equity_priority_score (or composite components separately)
- Linear regression + regularized (Lasso/Ridge) for feature selection
- Output: coefficient table (which factors drive inequity, by how much)
- Purpose: explainability layer for Deloitte stakeholders — goes in presentations

## 2b.5 — ML Model (Predictive Engine)
- XGBoost or LightGBM on same feature set
- Must accept GTFS service features (headway, frequency, span, stop_count) as inputs
- This is critical: simulation in Sprint 3 works by modifying these service inputs and re-predicting
- Hyperparameter tuning via cross-validation
- Compare performance to regression (R², RMSE, MAE)

## 2b.6 — Risk Scoring and Time Series Findings
- Flag tracts where temporal trends are worsening (poverty rising, vehicle access declining)
- Identify "fragile" tracts: currently Moderate but trending toward Critical
- Use ML model to predict what score would be if trends continue 2-3 years
- Document findings with tract-level detail

## 2b.7 — Validation and Reporting
- k-fold cross-validation for both models
- Residual analysis (are errors systematic? geographic patterns?)
- Feature importance plots (SHAP for ML, coefficients for regression)
- Model comparison table (regression vs ML on same metrics)
- Notebook + summary report

---

# Sprint 3: Simulation Engine — PENDING

## 3.1 — Define Simulation Parameters
Map user-adjustable levers to ML model input features:
- Headway changes → modify avg_headway_peak, avg_headway_evening, etc.
- Service span extension → modify service_span_hours
- Stop additions/removals → modify stop_count per tract
- Route additions → modify route_count, route_diversity
- Weekend service parity → modify weekend_weekday_ratio
Each lever modifies specific GTFS-derived features from 2b.1.

## 3.2 — Build the Simulator
Input: proposed service change (which tracts, which parameters, by how much)
Process: modify relevant features in modeling dataset → run ML model → re-predict equity scores
Output: before/after comparison (score deltas, tier shifts, number of tracts improved, affected population)

## 3.3 — Scenario Validation
Run 3-5 reference scenarios:
- "Double evening frequency in all Critical tracts"
- "Extend service span to midnight in top-20 priority tracts"
- "Add 5 stops to each transit desert tract"
- "Achieve weekend service parity county-wide"
Verify outputs behave sensibly. Document.

---

# Sprint 4: Interactive Dashboard — PENDING

## 4.1 — Dashboard Design
Layout: choropleth map (equity scores by tract), tier summary panel, tract detail drill-down, simulation control panel (sliders/dropdowns), before/after comparison view, trend alerts for at-risk tracts.

## 4.2 — Build Core Dashboard
Plotly Dash or Streamlit. Map view with tract coloring by tier/score, filter by neighborhood/tier/indicator, click-to-inspect tract profiles.

## 4.3 — Integrate Simulation
Connect Sprint 3 simulator to dashboard UI. User adjusts service parameters via controls → ML model re-predicts → map and scores update in real time. Before/after side-by-side.

## 4.4 — Alerts and Recommendations
Surface at-risk tracts (from 2b.6), display feature importance as actionable recommendations, export capability.
