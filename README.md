# AI for Equitable Public Transportation

> Predicting transit access gaps and equity issues across Miami-Dade County using AI-driven demand forecasting, scenario simulation, graph network analysis, and interactive visualization.

[![Status](https://img.shields.io/badge/Status-Sprint%203-blue)]()
[![Python](https://img.shields.io/badge/Python-3.10+-blue)]()
[![License](https://img.shields.io/badge/License-MIT-green)]()

**Capstone Project** — University of Miami x Deloitte
**Duration:** January 16 - May 1, 2026

[Project Board (GitHub)](https://github.com/DanielRegaladoUMiami/CapstoneProject-AI-for-Equitable-Transportation/issues) | [Notion Dashboard](https://www.notion.so/AI-for-Equitable-Transportation-Project-Dashboard-2ff03869ae4281d4b095df18a18ef77b) | [Wiki](https://github.com/DanielRegaladoUMiami/CapstoneProject-AI-for-Equitable-Transportation/wiki)

---

## Problem Statement

Urban public transportation systems face persistent equity challenges: uneven service coverage, long wait times in underserved areas, and limited visibility into how demographic changes impact access. These challenges are especially relevant in Miami-Dade County, where population density, income distribution, and transit dependency vary significantly across neighborhoods.

This project aims to design an AI-driven decision support system that identifies transit accessibility gaps, predicts emerging inequities, and evaluates the impact of potential service changes through what-if simulation and graph-based network analysis.

**Industry Focus:** Demand Forecasting, Universal Service Design, Accessibility

## Project Goals

1. **Identify** current and future public transportation access gaps
2. **Predict** changes in transit demand and equity outcomes using interpretable models
3. **Simulate** service change scenarios through a what-if simulation engine (frequency adjustments, demographic shifts)
4. **Analyze** transit network topology using City2Graph for connectivity and reachability insights
5. **Visualize** insights through an interactive Gradio dashboard with before/after scenario comparison
6. **Support** data-driven, equity-focused transit planning decisions

## Deliverables

| Sprint | Focus | Deliverables |
|---|---|---|
| **Sprint 1** | Exploratory Data Analysis | Cleaned integrated dataset, data dictionary, EDA report with hypotheses |
| **Sprint 2** | Model Design & Analysis | Leakage-free XGBoost model (CV R²=0.823), equity composite indicators, risk scoring |
| **Sprint 3** | Simulation Engine + City2Graph | `simulator.py`, 5 reference scenarios, validation notebook, City2Graph network analysis |
| **Sprint 4** | Dry-Run | Final presentation deck, polished visuals, rehearsal |
| **Sprint 5** | Final Presentation | Live demo, policy recommendations, complete documentation |

## Data Sources

| Dataset | Source | Description |
|---|---|---|
| Demographic Data | [US Census Bureau (ACS 2019-2024)](https://data.census.gov/table/ACSDP1Y2023.DP03?q=DP03&g=040XX00US12) | Socioeconomic and demographic profiles for Miami-Dade tracts |
| Transit System Data | [GTFS](https://gtfs.org/) | Schedule and real-time transit feeds |
| Accessibility Data | [National Accessibility Evaluation](https://www.arcgis.com/home/item.html?id=40526f1e2c734241bab4d3bb41385c51) | Transit accessibility metrics via ArcGIS |

## Tech Stack

| Category | Tools |
|---|---|
| Data Processing | Python (Pandas, NumPy, GeoPandas) |
| Modeling | XGBoost, Scikit-learn, Statsmodels, SHAP |
| Graph Analysis | City2Graph, NetworkX, DuckDB |
| Visualization | Plotly, Folium/Mapbox, Matplotlib, Seaborn |
| Dashboard | Gradio (V2 prototype, V3 with simulator integration) |
| Simulation | Custom Python engine (`simulator.py`) |
| Project Tracking | [GitHub Issues](https://github.com/DanielRegaladoUMiami/CapstoneProject-AI-for-Equitable-Transportation/issues) / [Notion](https://www.notion.so/AI-for-Equitable-Transportation-Project-Dashboard-2ff03869ae4281d4b095df18a18ef77b) |
| Version Control | Git / GitHub |

## Getting Started

```bash
# Clone the repo
git clone https://github.com/DanielRegaladoUMiami/CapstoneProject-AI-for-Equitable-Transportation.git
cd CapstoneProject-AI-for-Equitable-Transportation

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Project Structure

```
├── Sprint_1/                          # Sprint 1 — Exploratory Data Analysis
│   ├── data/                          #   Merged datasets (CSV, GeoPackage)
│   ├── notebooks/                     #   EDA notebooks (Census, GTFS, ArcGIS)
│   ├── Data_Dictionary_Sprint1.xlsx
│   └── Sprint1_Dataset_Overview.ipynb
│
├── Sprint_2/                          # Sprint 2 — Model Design & Analysis
│   ├── ACS_Tract_Level_Data/          #   Census ACS data (2019-2024) + EDA notebook
│   ├── Sprint_2a/                     #   Composite equity indicators (7 sub-indicators, 507 tracts)
│   └── Sprint_2b/                     #   XGBoost modeling, risk scoring, feature engineering
│       ├── Sprint2b_V3_LeakageFree_Modeling.ipynb
│       ├── Sprint2b_RiskScoring/      #   Model artifacts (.pkl), coefficients, predictions
│       └── ...
│
├── Sprint_3/                          # Sprint 3 — Simulation Engine + City2Graph
│   ├── Sprint_3a/
│   │   └── Gradio/                    #   Gradio V2 dashboard prototype
│   └── Sprint3_Plan.pdf
│
├── Sprint_4/                          # Sprint 4 — Dry-Run Presentation
├── Sprint_5/                          # Sprint 5 — Final Presentation
│
├── docs/                              # Project documentation & planning
│   ├── Capstone_Problem_Statement.pdf
│   └── ...
│
├── requirements.txt
├── .gitignore
└── README.md
```

## Sprint Timeline

```
Sprint 1 ▸ EDA                        Jan 16 – Feb 20  ████████████████████ COMPLETE
  1a · Data Acquisition & Evaluation   Jan 16 – Jan 30
  1b · Data Cleaning & Integration     Jan 31 – Feb 13
  1c · Exploratory Analysis & Insights Feb 14 – Feb 20  ★ Sprint Review

Sprint 2 ▸ Model Design & Analysis    Feb 21 – Mar 27  ████████████████████ COMPLETE
  2a · Equity Indicator Framework      Feb 21 – Mar 6
  2b · Leakage-Free XGBoost Modeling   Mar 7  – Mar 20
  2c · Validation & Documentation      Mar 21 – Mar 27  ★ Sprint Review

Sprint 3 ▸ Simulation Engine           Apr 3  – Apr 17  ████████░░░░░░░░░░░░ IN PROGRESS
  3.1 · Baseline State & Lever Catalog Apr 3  – Apr 9   Week 1
  3.2 · Simulator Core Engine          Apr 10 – Apr 13  Week 2
  3.3 · Scenario Validation            Apr 14 – Apr 16  Week 2
  3.4 · Gradio V3 Upgrade             Stretch           Post-demo
  City2Graph · Network Analysis        Parallel track    Non-blocking

Sprint 4 ▸ Dry-Run                     Apr 18 – Apr 24  ░░░░░░░░░░░░░░░░░░░░
Sprint 5 ▸ Final Presentation          May 1             ░░░░░░░░░░░░░░░░░░░░
```

## Methodology

### Sprint 1 — EDA (COMPLETE)

Data profiling, quality assessment, geographic join strategy, and exploratory visualizations to understand transit coverage vs. population density and identify access disparities across Miami-Dade County.

### Sprint 2 — Predictive Modeling (COMPLETE)

**Sprint 2a** — Built a composite equity indicator framework with 7 sub-indicators from GTFS, Census (ACS), and ArcGIS isochrone data across 507 census tracts.

**Sprint 2b** — Trained a leakage-free regression model to predict a Service Deficit Index from transit scheduling features:

| | |
|---|---|
| **Model** | XGBoost (GridSearchCV-tuned, 5-fold StratifiedKFold CV) |
| **CV R2** | 0.823 +/- 0.033 |
| **Test R2** | 0.789 |
| **RMSE** | 0.056 |
| **Features** | 13 (headway, frequency, weekend ratio, rail share, spatial, commute trends) |
| **Target** | Service Deficit Index — composite of 5 sub-indicators |

Data leakage was identified and fixed: `transit_jobs_30_mean` appeared in 4/5 target sub-indicators AND as a predictor feature. Three sub-indicators were rebuilt with zero feature/target overlap (verified programmatically). R2 dropped from 0.85 (fake) to 0.82 (real).

Top predictors (SHAP): `freq_peak_am_tph` (40%), `weekend_weekday_ratio` (22%), `freq_early_tph` (7%).

Notebook: [`Sprint_2/Sprint_2b/Sprint2b_V3_LeakageFree_Modeling.ipynb`](Sprint_2/Sprint_2b/Sprint2b_V3_LeakageFree_Modeling.ipynb)

### Sprint 3 — Simulation Engine + City2Graph (IN PROGRESS)

The simulation engine extends the two-model architecture from Sprint 2b: the leakage-free XGBoost v3 model (CV R2=0.823) for transit access deficit, and the OLS need model (R2=0.82) for demographic need. Both sides combine multiplicatively to produce equity scores and tier assignments.

**Simulator pipeline:** User adjusts 8 levers (6 access-side GTFS features + 2 need-side demographic features) -> XGBoost predicts updated deficit -> OLS computes updated need -> equity_score = need x deficit -> tier assignment using fixed cutoffs.

**City2Graph** runs as a parallel enhancement track using the [city2graph](https://city2graph.net/) library to build graph representations of Miami-Dade's GTFS transit network for connectivity analysis and visualization.

**5 Reference Scenarios** (Sprint 3 Deloitte deliverable): Peak Frequency Boost, Weekend Parity, Early Service Expansion, Poverty Stress Test, Combined Intervention.

Sprint 3 Plan: [`Sprint_3/Sprint3_Plan.pdf`](Sprint_3/Sprint3_Plan.pdf)

## Milestones

| Milestone | Due Date | Status |
|---|---|---|
| Sprint 1: EDA | Feb 20, 2026 | COMPLETE |
| Sprint 2: Modeling | Mar 27, 2026 | COMPLETE |
| Sprint 3: Solution Build | Apr 17, 2026 | IN PROGRESS |
| Sprint 4: Dry-Run | Apr 24, 2026 | Upcoming |
| Sprint 5: Final | May 1, 2026 | Upcoming |

## Team

| Name | Role |
|---|---|
| Daniel Regalado | Team Lead |
| Luna Gerlic | Team Member |
| Jeanne Hassoun | Team Member |
| Lina Graf | Team Member |
| Amelia Simpson | Team Member |

## Guiding Principles

- **Don't overcommit** — deliver what we promise, promise what we can deliver
- **AI is not just LLMs** — leverage regression, time series, clustering, spatial analysis, and graph neural networks
- **MVP first** — a working, interpretable pipeline beats an ambitious but unfinished system
- **Let data guide decisions** — evaluate early, pivot if needed
- **Stay curious** — ask questions and clarify assumptions continuously

---

*University of Miami — MS in Business Analytics — Deloitte Capstone 2026*
