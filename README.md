# 🚍 AI for Equitable Public Transportation

> Predicting transit access gaps and equity issues across Miami-Dade County using AI-driven demand forecasting, graph network modeling, scenario simulation, and interactive visualization.

[![Status](https://img.shields.io/badge/Status-Sprint%201-yellow)]()
[![Python](https://img.shields.io/badge/Python-3.10+-blue)]()
[![License](https://img.shields.io/badge/License-MIT-green)]()

**Capstone Project** — University of Miami × Deloitte AI Academy  
**Duration:** January 16 – May 1, 2026

📋 [Project Board (GitHub)](https://github.com/DanielRegaladoUMiami/CapstoneProject-AI-for-Equitable-Transportation/projects) · [Dashboard (Notion)](https://www.notion.so/AI-for-Equitable-Transportation-Project-Dashboard-2ff03869ae4281d4b095df18a18ef77b) · [Wiki](https://github.com/DanielRegaladoUMiami/CapstoneProject-AI-for-Equitable-Transportation/wiki)

---

## 📋 Problem Statement

Urban public transportation systems face persistent equity challenges: uneven service coverage, long wait times in underserved areas, and limited visibility into how demographic changes impact access. These challenges are especially relevant in Miami-Dade County, where population density, income distribution, and transit dependency vary significantly across neighborhoods.

This project aims to design an AI-driven decision support system that identifies transit accessibility gaps, predicts emerging inequities, and evaluates the impact of potential service changes through graph-based network modeling and what-if simulations.

**Industry Focus:** Demand Forecasting · Universal Service Design · Accessibility

## 🎯 Project Goals

1. **Identify** current and future public transportation access gaps
2. **Predict** changes in transit demand and equity outcomes using interpretable models
3. **Model** the transit system as a graph network to capture connectivity and reachability patterns
4. **Simulate** service change scenarios using graph-based methods (frequency adjustments, route modifications, new stops)
5. **Visualize** insights through an interactive dashboard with network-aware views
6. **Support** data-driven, equity-focused transit planning decisions

## 📦 Deliverables

| Sprint | Focus | Deliverables |
|---|---|---|
| **Sprint 1** | Exploratory Data Analysis | Cleaned integrated dataset, data dictionary, EDA report with hypotheses |
| **Sprint 2** | Model Design & Analysis | Baseline regression & time series models, ranked geographic zones for intervention |
| **Sprint 3** | Graph Network + Simulation + Dashboard | Graph-based transit network model, GNN-powered simulation results, interactive Streamlit dashboard |
| **Sprint 4** | Dry-Run | Final presentation deck, polished visuals |
| **Sprint 5** | Final Presentation | Live demo, policy recommendations, complete documentation |

## 📊 Data Sources

| Dataset | Source | Description |
|---|---|---|
| Demographic Data | [US Census Bureau (ACS 2023)](https://data.census.gov/table/ACSDP1Y2023.DP03?q=DP03&g=040XX00US12) | Socioeconomic and demographic profiles for Florida |
| Transit System Data | [GTFS](https://gtfs.org/) | Schedule and real-time transit feeds |
| Accessibility Data | [National Accessibility Evaluation](https://www.arcgis.com/home/item.html?id=40526f1e2c734241bab4d3bb41385c51) | Transit accessibility metrics via ArcGIS |

## 🛠️ Tech Stack

| Category | Tools |
|---|---|
| Data Processing | Python (Pandas, NumPy, GeoPandas) |
| Modeling | Scikit-learn, Statsmodels, Interpretable ML |
| Graph Modeling | NetworkX, PyTorch Geometric (GNNs) |
| Visualization | Plotly, Folium/Mapbox, Matplotlib, Seaborn |
| Dashboard | Streamlit or Power BI |
| Simulation | Graph-based scenario engine (Python) |
| Project Tracking | [GitHub Projects](https://github.com/DanielRegaladoUMiami/CapstoneProject-AI-for-Equitable-Transportation/projects) · [Notion](https://www.notion.so/AI-for-Equitable-Transportation-Project-Dashboard-2ff03869ae4281d4b095df18a18ef77b) |
| Version Control | Git / GitHub |

## 🚀 Getting Started

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

## 📁 Project Structure

```
├── data/
│   ├── raw/                  # Original datasets (Census, GTFS, Accessibility)
│   │   ├── census/
│   │   ├── gtfs/
│   │   └── accessibility/
│   ├── interim/              # Intermediate transformations
│   └── processed/            # Final cleaned & merged datasets
├── sprint_1_eda/             # Data profiling, cleaning, integration, exploratory analysis
├── sprint_2_modeling/        # Feature engineering, regression, time series, validation
├── sprint_3_simulation/      # Graph network modeling, GNN simulation, Streamlit dashboard
├── sprint_4_dryrun/          # Refined deck, polished visuals, rehearsal feedback
├── sprint_5_final/           # Final presentation, live demo, executive recommendations
├── docs/                     # Data dictionary, methodology documentation
├── requirements.txt
├── .gitignore
└── README.md
```

## 📅 Sprint Timeline

```
Sprint 1 ▸ EDA                          Jan 16 – Feb 20  ██████████░░░░░░░░░░
  1a · Data Acquisition & Evaluation     Jan 16 – Jan 30  ★ Decision Gate
  1b · Data Cleaning & Integration       Jan 31 – Feb 13  ★ Deliverable
  1c · Exploratory Analysis & Insights   Feb 14 – Feb 20  ★ Sprint Review

Sprint 2 ▸ Model Design & Analysis      Feb 21 – Mar 27  ░░░░░░░░░░██████████
  2a · Feature Engineering               Feb 21 – Mar 6   ★ Deliverable
  2b · Baseline Modeling                 Mar 7  – Mar 20
  2c · Validation & Documentation        Mar 21 – Mar 27  ★ Sprint Review

Sprint 3 ▸ Graph Network + Dashboard    Mar 28 – Apr 17  ░░░░░░░░░░░░░░██████
  3a · Graph Modeling & Simulation       Mar 28 – Apr 7   ★ Deliverable
  3b · Dashboard Development             Apr 8  – Apr 17  ★ Sprint Review

Sprint 4 ▸ Dry-Run                      Apr 18 – Apr 24  ░░░░░░░░░░░░░░░░░░██
Sprint 5 ▸ Final Presentation           May 1             ░░░░░░░░░░░░░░░░░░░█
```

## 🔬 Methodology Overview

### Sprint 1 — EDA
Data profiling, quality assessment, geographic join strategy, and exploratory visualizations to understand transit coverage vs. population density and identify access disparities.

### Sprint 2 — Predictive Modeling
Regression and time series models to estimate transit demand, predict accessibility outcomes, and rank geographic zones for intervention. Focus on interpretability — feature importance and coefficient analysis to identify top drivers of inequity.

### Sprint 3 — Graph Network Modeling & Simulation
Model the transit system as a graph (stops = nodes, routes = edges). Compute network accessibility metrics (reachability, centrality, travel-time paths). Apply Graph Neural Networks (GNNs) to capture non-linear patterns in accessibility propagation. Simulate service changes on the graph and quantify impact vs. baseline.

### Dashboard
Four core views: access gap map with demographic overlay, scenario comparison (baseline vs. proposed changes), equity indicator charts, and network connectivity visualization.

## 📋 Project Tracking — How We Work

We use **GitHub Issues + Project Board** to track all tasks, milestones, and deliverables.

### Workflow

1. **Pick a task** — Go to the [Project Board](https://github.com/DanielRegaladoUMiami/CapstoneProject-AI-for-Equitable-Transportation/projects), find an issue in `Todo`
2. **Assign yourself** — Click the issue → assign yourself
3. **Move to In Progress** — Drag the card to `In Progress`
4. **Create a branch** — `git checkout -b feature/issue-number-short-description`
5. **Do the work** — Commit often with meaningful messages
6. **Open a PR** — Reference the issue: `Closes #12`
7. **Move to Done** — After merge, the card moves to `Done` automatically

### Labels

| Label Type | Examples | Purpose |
|---|---|---|
| **Sprint** | `sprint 1: eda`, `sprint 2: modeling` | Filter tasks by sprint |
| **Sub-Sprint** | `1a: data acquisition`, `2b: baseline modeling` | Filter by sub-sprint phase |
| **Priority** | `priority: high`, `priority: medium`, `priority: low` | Task urgency |
| **Type** | `type: task`, `type: milestone`, `type: deliverable`, `type: decision gate` | Task category |

### Milestones

| Milestone | Due Date |
|---|---|
| Sprint 1: EDA | Feb 20, 2026 |
| Sprint 2: Modeling | Mar 27, 2026 |
| Sprint 3: Solution Build | Apr 17, 2026 |
| Sprint 4: Dry-Run | Apr 24, 2026 |
| Sprint 5: Final | May 1, 2026 |

## 👥 Team

| Name | Role |
|---|---|
| Daniel Regalado | Team Lead |
| Luna Gerlic | Team Member |
| Jeanne Hassoun | Team Member |
| Lina Graf | Team Member |
| Amelia Simpson | Team Member |

## 📝 Guiding Principles

- **Don't overcommit** — deliver what we promise, promise what we can deliver
- **AI ≠ just LLMs** — leverage regression, time series, clustering, spatial analysis, and graph neural networks
- **MVP first** — a working, interpretable pipeline beats an ambitious but unfinished system
- **Let data guide decisions** — evaluate early, pivot if needed
- **Stay curious** — ask questions and clarify assumptions continuously

---

*University of Miami — MS in Business Analytics — Deloitte AI Academy Capstone 2026*
