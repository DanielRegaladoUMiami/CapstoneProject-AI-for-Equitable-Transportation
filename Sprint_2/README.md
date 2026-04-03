# Sprint 2: Model Design & Analysis

**Duration:** February 21 - March 27, 2026 (5 weeks)
**Sprint Review:** March 27, 2026
**Status:** COMPLETE

## Objective

Design and validate interpretable baseline predictive models that identify current transit accessibility gaps and anticipate emerging equity issues, enabling the prioritization of geographic areas for targeted transit interventions.

## Sub-Sprints

### 2a - Equity Indicator Framework (Feb 21 - Mar 6)

- Built a composite equity indicator framework with 7 sub-indicators
- Combined GTFS transit metrics, Census (ACS) demographics, and ArcGIS isochrone data
- Covered 507 census tracts across Miami-Dade County
- Created equity tier assignments (Critical, High, Moderate, Low) using quantile-based cutoffs

> **Deliverable (Mar 6):** Validated equity indicator framework and tract-level scores.

**Key notebook:** [`Sprint_2a/Sprint2a_Composite_Equity_Indicators_v3.ipynb`](Sprint_2a/Sprint2a_Composite_Equity_Indicators_v3.ipynb)

### 2b - Leakage-Free XGBoost Modeling (Mar 7 - Mar 20)

- Engineered 13 features from transit scheduling data (headway, frequency, weekend ratio, rail share, spatial, commute trends)
- Identified and fixed data leakage: `transit_jobs_30_mean` appeared in 4/5 target sub-indicators AND as a predictor feature
- Rebuilt three sub-indicators using structural variables with zero feature/target overlap (verified programmatically)
- Trained XGBoost model with GridSearchCV and 5-fold StratifiedKFold cross-validation
- Built OLS need model (R2=0.82) for demographic need projection
- Produced risk scores and tract-level deficit predictions

**Key notebooks:**
- [`Sprint_2b/Sprint2b_V3_LeakageFree_Modeling.ipynb`](Sprint_2b/Sprint2b_V3_LeakageFree_Modeling.ipynb) — Final V3 model with SHAP analysis
- [`Sprint_2b/Sprint2b_Feature_Engineering.ipynb`](Sprint_2b/Sprint2b_Feature_Engineering.ipynb) — Feature engineering pipeline
- [`Sprint_2b/Sprint2b_RiskScoring/Sprint2b_Modeling_RiskScoring.ipynb`](Sprint_2b/Sprint2b_RiskScoring/Sprint2b_Modeling_RiskScoring.ipynb) — Risk scoring and OLS need model

### 2c - Validation & Documentation (Mar 21 - Mar 27)

- Sensitivity analysis via SHAP to understand feature influence on equity outcomes
- Validated model results against observed transit patterns
- Ranked and prioritized geographic zones for transit intervention
- Documented model methodology, performance metrics, and interpretation

> **Sprint 2 Review (Mar 27):** Presented model results, geographic priorities, and insights linking predictions to policy-relevant decisions.

## Model Results (V3 - Leakage-Free)

| Metric | Value |
|---|---|
| Model | XGBoost (GridSearchCV, 5-fold StratifiedKFold) |
| CV R2 | 0.823 +/- 0.033 |
| Test R2 | 0.789 |
| RMSE | 0.056 |
| Features | 13 (headway, frequency, weekend ratio, rail share, spatial, commute trends) |
| Target | Service Deficit Index — composite of 5 sub-indicators |

**Top predictors (SHAP importance):**
1. `freq_peak_am_tph` — 39.6% (peak AM frequency, trips/hr)
2. `weekend_weekday_ratio` — 21.7% (weekend service parity)
3. `freq_early_tph` — 6.9% (early morning frequency)
4. `headway_peak_am_min` — 3.8% (peak headway)

**Data leakage fix:** R2 dropped from 0.85 (leaked) to 0.82 (real) after rebuilding sub-indicators. This is the honest, production-ready model.

## Deliverables

| # | Deliverable | Status |
|---|---|---|
| 1 | Baseline predictive model outputs with documented performance metrics | Done |
| 2 | Ranked geographic zones for transit intervention with supporting rationale | Done |
| 3 | Interpretable insights linking model results to equity-focused decision-making | Done |

## Folder Structure

```
Sprint_2/
├── ACS_Tract_Level_Data/                              # Census ACS source data
│   ├── ACS_MiamiDade_Tracts_2019.csv                  #   ACS data by year (2019-2024)
│   ├── ACS_MiamiDade_Tracts_2020.csv
│   ├── ACS_MiamiDade_Tracts_2021.csv
│   ├── ACS_MiamiDade_Tracts_2022.csv
│   ├── ACS_MiamiDade_Tracts_2023.csv
│   ├── ACS_MiamiDade_Tracts_2024.csv
│   ├── Census_MiamiDade_Tracts_Combined.csv            #   Combined multi-year census
│   ├── Clean_Census_MiamiDade_Tracts_Combined.csv      #   Cleaned version
│   ├── DP03_MiamiDade_Tracts.csv                       #   Economic characteristics
│   ├── DP04_MiamiDade_Tracts.csv                       #   Housing characteristics
│   ├── DP05_MiamiDade_Tracts.csv                       #   Demographic characteristics
│   └── EDA_ACS_Tract_Level_MiamiDade.ipynb             #   ACS EDA notebook
│
├── Sprint_2a/                                          # Equity Indicator Framework
│   ├── Sprint2a_Composite_Equity_Indicators_v3.ipynb   #   Equity indicator notebook
│   ├── Sprint2a_Equity_Indicators_v3_tract.csv         #   Tract-level equity scores
│   └── Sprint2a_Equity_Results_Overview_v3.xlsx        #   Results summary
│
├── Sprint_2b/                                          # XGBoost Modeling & Risk Scoring
│   ├── Sprint2b_V3_LeakageFree_Modeling.ipynb          #   Final V3 model (main notebook)
│   ├── Sprint2b_Feature_Engineering.ipynb              #   Feature engineering pipeline
│   ├── Sprint2b_Regression_Modeling.ipynb              #   Initial regression modeling
│   ├── Sprint2b_ACS_TimeSeries.ipynb                   #   ACS time series analysis
│   ├── Sprint2b_Modeling_Features_NotebookOutput.csv   #   13 model features (507 tracts)
│   ├── Sprint2b_Model_Summary.csv                      #   Model performance summary
│   ├── Sprint2b_Tract_Risk_Scores.csv                  #   Tract-level risk scores
│   └── Sprint2b_RiskScoring/                           #   Risk scoring outputs & model artifacts
│       ├── Sprint2b_Modeling_RiskScoring.ipynb          #     Risk scoring + OLS need model
│       ├── Sprint2b_XGBoost_AccessDeficit.pkl           #     Trained XGBoost model
│       ├── Sprint2b_Model_Config.pkl                    #     Model config / scaler
│       ├── Sprint2b_AccessDeficit_Coefficients.csv      #     Access-side coefficients
│       └── Sprint2b_AccessDeficit_Predictions.csv       #     Tract-level deficit predictions
│
└── README.md
```

## Outputs Used by Sprint 3

The following files from Sprint 2 are inputs to the Sprint 3 simulation engine:

| File | Purpose in Sprint 3 |
|---|---|
| `Sprint_2b/Sprint2b_Modeling_Features_NotebookOutput.csv` | 13 model features for baseline state |
| `Sprint_2b/Sprint2b_RiskScoring/Sprint2b_XGBoost_AccessDeficit.pkl` | XGBoost model for deficit prediction |
| `Sprint_2b/Sprint2b_RiskScoring/Sprint2b_Model_Config.pkl` | Model config / StandardScaler |
| `Sprint_2b/Sprint2b_Tract_Risk_Scores.csv` | Tract-level risk scores |
| `Sprint_2b/Sprint2b_RiskScoring/Sprint2b_AccessDeficit_Coefficients.csv` | Access-side coefficients |
| `Sprint_2a/Sprint2a_Equity_Indicators_v3_tract.csv` | Equity tier cutoffs + population |
