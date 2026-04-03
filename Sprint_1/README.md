# Sprint 1: Exploratory Data Analysis (EDA)

**Duration:** January 16 - February 20, 2026 (5 weeks)
**Sprint Review:** February 20, 2026
**Status:** COMPLETE

## Objective

Establish a clean, integrated dataset and develop a strong understanding of transit access patterns, data quality, and limitations across Miami-Dade County. Validate that the chosen datasets support the project goals.

## Sub-Sprints

### 1a - Data Acquisition & Evaluation (Jan 16 - Jan 30)

- Downloaded and inventoried all datasets: US Census (ACS), GTFS schedules, National Accessibility Evaluation Data
- Initial data profiling: shape, data types, missingness, distributions
- Evaluated dataset quality and fitness for project objectives
- Confirmed geographic levels align at census tract level for Miami-Dade County
- Documented initial findings and data limitations

> **Decision Gate (Jan 30):** Datasets confirmed sufficient to proceed.

### 1b - Data Cleaning & Integration (Jan 31 - Feb 13)

- Cleaned and standardized each dataset (handled missing values, normalized formats)
- Defined geographic join strategy at census tract level
- Merged datasets into integrated analytical tables
- Created comprehensive data dictionary
- Performed data validation and consistency checks across joined data

> **Deliverable (Feb 13):** Cleaned, merged analytical dataset with data dictionary.

### 1c - Exploratory Analysis & Insights (Feb 14 - Feb 20)

- Exploratory visualizations: maps, distributions, correlations
- Analyzed transit coverage vs. population density across neighborhoods
- Identified access disparities (baseline wait times, service frequency, stop coverage)
- Defined key metrics and KPIs (accessibility index, service gap score, demand proxies)
- Formulated hypotheses for modeling phase

> **Sprint 1 Review (Feb 20):** Presented EDA findings, hypotheses, and data readiness assessment to stakeholders.

## Deliverables

| # | Deliverable | Status |
|---|---|---|
| 1 | Cleaned, merged analytical dataset | Done |
| 2 | Data dictionary and KPI definitions | Done |
| 3 | EDA summary report with key findings and hypotheses | Done |
| 4 | Data fitness assessment (go/no-go recommendation) | Done |

## Folder Structure

```
Sprint_1/
├── data/
│   ├── MiamiDade_Merged_Sprint1.csv          # Merged dataset (all geographies)
│   ├── MiamiDade_Merged_Sprint1.gpkg         # GeoPackage version
│   ├── MiamiDade_Tract_Merged_Sprint1.csv    # Tract-level merged dataset
│   └── MiamiDade_Tract_Merged_Sprint1.gpkg   # Tract-level GeoPackage
├── notebooks/
│   ├── EDA_ACS_Census_Demographics.ipynb      # Census/ACS demographic EDA
│   ├── EDA_ARCGIS_Miami_Dade_Transit_Data.ipynb  # ArcGIS transit accessibility EDA
│   └── Transit_data_Miami_Dade-2.ipynb        # GTFS transit data EDA
├── Data_Dictionary_Sprint1.xlsx               # Data dictionary
├── Sprint1_Dataset_Overview.ipynb             # Dataset overview and profiling
└── README.md
```

## Data Sources

| Dataset | Description |
|---|---|
| US Census (ACS 2023) | Socioeconomic and demographic profiles for Miami-Dade tracts |
| GTFS Schedule | Schedule and real-time transit feeds for Miami-Dade |
| National Accessibility Evaluation | Transit accessibility metrics via ArcGIS isochrones |
