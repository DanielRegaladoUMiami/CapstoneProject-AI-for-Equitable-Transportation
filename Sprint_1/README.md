# Sprint 1: Exploratory Data Analysis (EDA)

**Duration:** January 16 – February 20 (5 weeks)  
**Sprint Review:** February 20  
**Technical Complexity:** Medium | **Business Impact:** Medium

## Objective

Establish a clean, integrated dataset and develop a strong understanding of transit access patterns, data quality, and limitations. Validate that the chosen datasets support the project goals.

## Sub-Sprints

### 1a · Data Acquisition & Evaluation (Jan 16 – Jan 30)

- Download and inventory all datasets: US Census (ACS), GTFS schedules, National Accessibility Evaluation Data
- Initial data profiling: shape, data types, missingness, distributions
- Evaluate dataset quality and fitness for project objectives
  - Do the geographic levels match (ZIP, tract, block group)?
  - Is there enough coverage for Miami-Dade County specifically?
  - Are there critical gaps that require alternative data sources?
- Document initial findings and data limitations

> **★ DECISION GATE (Jan 30):** Are these datasets sufficient? Team decides to proceed or identify alternative/supplementary data sources.

### 1b · Data Cleaning & Integration (Jan 31 – Feb 13)

- Clean and standardize each dataset (handle missing values, normalize formats)
- Define geographic join strategy (census tract, ZIP code, or custom zones)
- Merge datasets into an integrated analytical table
- Create a comprehensive data dictionary
- Perform data validation and consistency checks across joined data

> **★ DELIVERABLE (Feb 13):** Cleaned, merged analytical dataset with data dictionary.

### 1c · Exploratory Analysis & Insights (Feb 14 – Feb 20)

- Exploratory visualizations: maps, distributions, correlations
- Analyze transit coverage vs. population density across neighborhoods
- Identify access disparities (baseline wait times, service frequency, stop coverage)
- Define key metrics and KPIs (accessibility index, service gap score, demand proxies)
- Formulate hypotheses for modeling phase
- Prepare EDA summary report with key findings

> **★ SPRINT 1 REVIEW (Feb 20):** Present EDA findings, hypotheses, and data readiness assessment to stakeholders.

## Deliverables

| # | Deliverable | Status |
|---|---|---|
| 1 | Cleaned, merged analytical dataset | ⬜ |
| 2 | Data dictionary and KPI definitions | ⬜ |
| 3 | EDA summary report with key findings and hypotheses | ⬜ |
| 4 | Data fitness assessment (go/no-go recommendation) | ⬜ |

## Data Sources

| Dataset | Location |
|---|---|
| US Census (ACS 2023) | `data/raw/census/` |
| GTFS Schedule & Real-Time | `data/raw/gtfs/` |
| National Accessibility Evaluation | `data/raw/accessibility/` |
