---
title: Miami-Dade Transit Equity Simulator
emoji: 🚌
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 5.9.1
app_file: app.py
pinned: false
license: mit
---

# Miami-Dade Transit Equity Simulator

Interactive simulation of how transit-service changes affect equity outcomes
across 504 Miami-Dade census tracts.

Built for the University of Miami MSBA Capstone: **AI for Equitable Public
Transportation** (Deloitte partnership).

## What you can do

- **Adjust 4 transit-service levers** (peak AM frequency, early-AM frequency,
  weekend/weekday ratio, rail modal share) and see per-tract equity impact.
- **Scope interventions** to All / Critical-only / High+Critical / Fragile / custom GEOIDs.
- **Click any tract** for a detailed narrative including demographics, service
  levels, and a **route-level diagnostic** (which bus routes serve the tract,
  their AM-peak headway, and the bottleneck route).
- **Before/after choropleth maps** + 4×4 tier-shift matrix for each scenario.

## Under the hood

- **Simulator:** Luna's Sprint 3.2 engine (proportional-change formula:
  `ratio = new_deficit / baseline_deficit`, applied to Sprint 2a composite).
- **Model:** XGBoost v3 predicting service_deficit from 13 features.
- **Baseline:** 504 tracts × 29 cols (inner join of features + deficit + need).
- **City2Graph:** GTFS-derived per-tract route-level diagnostic (Miami-Dade
  GTFS 2026-03-24, weekday AM peak 06:00–09:00, 500m walking buffer).

## Reference scenarios (S1–S5)

| # | Name | Lever(s) | Scope |
|---|---|---|---|
| S1 | Peak freq boost | `freq_peak_am_tph +2` | Critical (~51) |
| S2 | Weekend parity | `weekend_weekday_ratio → 0.80` | All 504 |
| S3 | Early service | `freq_early_tph +1` | High+Critical (~153) |
| S4 | Rail modal shift | `rail_trip_share +0.10` | All 504 |
| S5 | Combined | peak+2, weekend→0.80, rail+0.05 | High+Critical |

## Top problem routes (Critical+High tracts)

From the City2Graph diagnostic:

| Route | Long name | # Crit/High tracts | Worst headway |
|---|---|---|---|
| 17 | 163 ST TERM-VIZ VIA 17 AV | 28 | 60 min |
| 54 | HIALEAH-MIAMI LAKES-BISCA VIA 54 ST | 27 | 60 min |
| HIAFLA | City of Hialeah Transit (Flamingo) | 19 | 60 min |
| 95 | I-95 GOLDEN GLADES EXPRESS | 9 | 120 min |
| MIALIB | City of Miami - Liberty City Route | 14 | 60 min |

## Credits

- Luna (lunaasage): Sprint 3.1 baseline + Sprint 3.2 simulator
- Lina Graf: Gradio V2/V3 dashboard
- Daniel Regalado Cardoso: Sprint 1/2 modeling, Sprint 3.3 validation, City2Graph
