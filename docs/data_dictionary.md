# 📖 Data Dictionary

## Overview

This document describes all variables in the integrated analytical dataset.

**Last Updated:** Sprint 1b (TBD)

---

## Census ACS Data

| Variable | Type | Description | Source |
|---|---|---|---|
| `census_tract` | string | Census tract FIPS code | ACS 2023 |
| `total_population` | int | Total population count | ACS 2023 |
| `median_income` | float | Median household income ($) | ACS 2023 |
| `pct_no_vehicle` | float | % households with no vehicle | ACS 2023 |
| `pct_below_poverty` | float | % population below poverty line | ACS 2023 |
| *... to be expanded* | | | |

## GTFS Transit Data

| Variable | Type | Description | Source |
|---|---|---|---|
| `stop_id` | string | Unique transit stop identifier | GTFS |
| `route_id` | string | Unique route identifier | GTFS |
| `avg_headway_min` | float | Average headway in minutes | GTFS |
| `service_hours` | float | Daily service hours | GTFS |
| *... to be expanded* | | | |

## Accessibility Data

| Variable | Type | Description | Source |
|---|---|---|---|
| `access_score` | float | Transit accessibility index | Nat'l Accessibility Eval |
| *... to be expanded* | | | |

## Engineered Features (Sprint 2)

| Variable | Type | Description | Formula |
|---|---|---|---|
| `stop_density` | float | Stops per sq mile | stops / area |
| `equity_index` | float | Composite equity indicator | TBD |
| *... to be expanded* | | | |

---

## KPIs & Metrics

| Metric | Definition | Target |
|---|---|---|
| Accessibility Index | Composite score of transit access dimensions | Higher = better |
| Service Gap Score | Areas with high demand but low service | Lower = better |
| Equity Ratio | Service level relative to demographic need | Closer to 1.0 |
