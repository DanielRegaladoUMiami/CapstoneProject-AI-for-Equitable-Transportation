# 📊 Data Sources

## Overview

This project integrates three primary data sources to analyze transit equity across Miami-Dade County. Raw datasets are stored in their respective subfolders and should **never be modified directly** — all transformations go to `interim/` or `processed/`.

```
data/
├── raw/
│   ├── census/          # US Census Bureau (ACS)
│   ├── gtfs/            # General Transit Feed Specification
│   └── accessibility/   # National Accessibility Evaluation
├── interim/             # Intermediate transformations
└── processed/           # Final cleaned & merged datasets
```

---

## 1. Demographic Data — US Census Bureau (ACS 2023)

| | |
|---|---|
| **Source** | [US Census Bureau — American Community Survey](https://data.census.gov/table/ACSDP1Y2023.DP03?q=DP03&g=040XX00US12) |
| **Table** | DP03 — Selected Economic Characteristics |
| **Geography** | State of Florida (FIPS: 12), Miami-Dade County focus |
| **Format** | CSV |
| **Store in** | `data/raw/census/` |

**Key Variables:** median household income, employment status, commuting patterns, vehicle availability, poverty rates, industry distribution.

**Additional Census Links:**
| Table | Description | Link |
|---|---|---|
| DP02 | Social Characteristics (education, language, ancestry) | [Link](https://data.census.gov/table/ACSDP1Y2023.DP02?q=DP02&g=040XX00US12) |
| DP03 | Economic Characteristics (income, employment, commute) | [Link](https://data.census.gov/table/ACSDP1Y2023.DP03?q=DP03&g=040XX00US12) |
| DP05 | Demographic Characteristics (age, race, population) | [Link](https://data.census.gov/table/ACSDP1Y2023.DP05?q=DP05&g=040XX00US12) |
| Census API | Programmatic access to all tables | [Link](https://api.census.gov/data.html) |

---

## 2. Transit System Data — GTFS

| | |
|---|---|
| **Source** | [General Transit Feed Specification](https://gtfs.org/) |
| **Provider** | Miami-Dade Transit (MDT) |
| **Types** | Schedule (static) & Real-Time |
| **Format** | ZIP archive containing TXT files |
| **Store in** | `data/raw/gtfs/` |

**Key Files in GTFS Feed:**
| File | Description |
|---|---|
| `stops.txt` | Stop locations (lat/lon, name, zone) |
| `routes.txt` | Route definitions (name, type, agency) |
| `trips.txt` | Trip definitions per route |
| `stop_times.txt` | Arrival/departure times per stop per trip |
| `shapes.txt` | Geographic path of routes |
| `calendar.txt` | Service schedules (days of week) |
| `frequencies.txt` | Headway-based service (if available) |

**GTFS Links:**
| Resource | Link |
|---|---|
| GTFS Specification | [gtfs.org](https://gtfs.org/) |
| GTFS Reference Docs | [Google Transit — Static](https://developers.google.com/transit/gtfs/reference) |
| GTFS Realtime Docs | [Google Transit — Realtime](https://developers.google.com/transit/gtfs-realtime) |
| OpenMobilityData (Feed Index) | [transitfeeds.com](https://transitfeeds.com/) |
| Mobility Database | [mobilitydatabase.org](https://mobilitydatabase.org/) |

---

## 3. Accessibility Data — National Accessibility Evaluation

| | |
|---|---|
| **Source** | [National Accessibility Evaluation — ArcGIS](https://www.arcgis.com/home/item.html?id=40526f1e2c734241bab4d3bb41385c51) |
| **Provider** | University of Minnesota — Accessibility Observatory |
| **Format** | GeoJSON / Shapefile |
| **Store in** | `data/raw/accessibility/` |

**Description:** Transit accessibility metrics measuring how many destinations (jobs, healthcare, grocery, etc.) are reachable within a given travel time by public transit from each census block group.

**Additional Accessibility Links:**
| Resource | Link |
|---|---|
| ArcGIS Data Page | [arcgis.com](https://www.arcgis.com/home/item.html?id=40526f1e2c734241bab4d3bb41385c51) |
| Accessibility Observatory (UMN) | [access.umn.edu](https://access.umn.edu/) |
| EPA Smart Location Database | [epa.gov](https://www.epa.gov/smartgrowth/smart-location-mapping) |

---

## Data Pipeline

```
raw/census/          ─┐
raw/gtfs/            ─┼──▶  interim/  ──▶  processed/merged_dataset.csv
raw/accessibility/   ─┘
                         (clean &         (final analytical
                          standardize)     table for modeling)
```

**Geographic Join Strategy:** TBD in Sprint 1b (census tract, ZIP code, or custom zones)

## Notes

- Raw data files are excluded from Git via `.gitignore` due to size — download them from the links above
- All team members should download datasets to the same folder structure for reproducibility
- See `docs/data_dictionary.md` for variable definitions after Sprint 1b
