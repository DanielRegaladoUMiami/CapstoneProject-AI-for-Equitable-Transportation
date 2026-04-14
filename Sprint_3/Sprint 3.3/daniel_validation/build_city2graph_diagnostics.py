"""
City2Graph Diagnostic Pipeline — per-tract route-level explainer for the
Sprint 3 simulator. Answers: 'tract X is Critical — which routes are the
bottleneck, and what's their AM-peak headway?'

Inputs
------
- GTFS feed (gtfs/ folder with stops.txt, routes.txt, trips.txt, stop_times.txt, calendar.txt)
- Sprint3_Baseline_State.csv (for Critical-tract flag per tract)
- Miami-Dade census tract geometries (fetched from Census TIGERweb)

Outputs
-------
- City2Graph_Tract_Routes.csv      — per tract: routes serving it + AM-peak metrics
- City2Graph_Problem_Routes.csv    — ranked routes by impact on Critical+High tracts
- City2Graph_Tract_Narratives.json — per-tract human-readable diagnostic strings

Pipeline
--------
1. Load GTFS. Identify weekday-peak-AM service_ids (Mon-Fri, 06:00-09:00).
2. Count trips per (route_id, stop_id) in that window → derive per-stop headway.
3. Build 500m walking buffer around stops, spatial-join to tract geometries.
4. Per tract: aggregate stops within walking → per-route stats.
5. Rank routes by (#Critical/High tracts served × worst headway).
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import requests
from shapely.geometry import Point

warnings.filterwarnings("ignore")

HERE = Path(__file__).resolve().parent
GTFS = HERE / "gtfs"
BASELINE_CSV = HERE.parent.parent / "Sprint 3.1" / "Sprint3_Baseline_State.csv"

# Miami-Dade county FIPS: 12086. TIGERweb layer 0 = Census Tracts.
TIGER_URL = (
    "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Tracts_Blocks/"
    "MapServer/0/query"
)
WALK_BUFFER_METERS = 500
PEAK_AM_START_SEC = 6 * 3600
PEAK_AM_END_SEC = 9 * 3600


def log(msg: str) -> None:
    print(f"[city2graph] {msg}", flush=True)


# --------------------------------------------------------------------------
# Load GTFS
# --------------------------------------------------------------------------

def load_gtfs():
    """Load GTFS text files. If they've been gitignored, unzip gtfs.zip first."""
    import zipfile
    zip_path = GTFS / "gtfs.zip"
    required = ["stops.txt", "routes.txt", "trips.txt", "stop_times.txt", "calendar.txt"]
    missing = [f for f in required if not (GTFS / f).exists()]
    if missing and zip_path.exists():
        log(f"Extracting {missing} from gtfs.zip...")
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(GTFS)

    log("Loading GTFS tables...")
    stops = pd.read_csv(GTFS / "stops.txt")
    routes = pd.read_csv(GTFS / "routes.txt")
    trips = pd.read_csv(GTFS / "trips.txt")
    calendar = pd.read_csv(GTFS / "calendar.txt")
    # stop_times is the heavy one — only keep what we need
    stop_times = pd.read_csv(
        GTFS / "stop_times.txt",
        usecols=["trip_id", "arrival_time", "stop_id"],
        dtype={"trip_id": str, "stop_id": str},
    )
    log(f"  stops={len(stops):,}  routes={len(routes)}  trips={len(trips):,}  stop_times={len(stop_times):,}")
    return stops, routes, trips, calendar, stop_times


def weekday_peak_trips(trips, calendar, stop_times):
    """Return stop_times limited to weekday service AM peak (06:00-09:00)."""
    wkday_services = calendar.loc[
        (calendar[["monday", "tuesday", "wednesday", "thursday", "friday"]].sum(axis=1) >= 3),
        "service_id",
    ].astype(str).tolist()
    wkday_trips = trips.loc[trips["service_id"].astype(str).isin(wkday_services), ["trip_id", "route_id"]].copy()
    wkday_trips["trip_id"] = wkday_trips["trip_id"].astype(str)
    log(f"  weekday service_ids: {wkday_services} → {len(wkday_trips):,} trips")

    # Parse GTFS time HH:MM:SS → seconds. Can exceed 24:00:00 (service day).
    st = stop_times.merge(wkday_trips, on="trip_id", how="inner")
    parts = st["arrival_time"].str.split(":", expand=True).astype(int)
    st["sec"] = parts[0] * 3600 + parts[1] * 60 + parts[2]
    st = st[(st["sec"] >= PEAK_AM_START_SEC) & (st["sec"] < PEAK_AM_END_SEC)]
    log(f"  weekday AM-peak stop-events: {len(st):,}")
    return st


# --------------------------------------------------------------------------
# Fetch tract geometries
# --------------------------------------------------------------------------

def fetch_tracts(baseline_geoids):
    """Query TIGERweb for Miami-Dade (FIPS 12086) census tracts."""
    cache = HERE / "miami_dade_tracts.geojson"
    if cache.exists():
        log(f"  using cached geometries: {cache.name}")
        return gpd.read_file(cache)

    log("  fetching Miami-Dade tracts from Census TIGERweb...")
    params = {
        "where": "STATE='12' AND COUNTY='086'",
        "outFields": "GEOID,STATE,COUNTY,TRACT",
        "outSR": "4326",
        "f": "geojson",
    }
    r = requests.get(TIGER_URL, params=params, timeout=60)
    r.raise_for_status()
    gdf = gpd.read_file(r.text)
    gdf.to_file(cache, driver="GeoJSON")
    log(f"  saved {len(gdf)} tract geometries")
    return gdf


# --------------------------------------------------------------------------
# Build diagnostics
# --------------------------------------------------------------------------

def per_stop_route_metrics(peak_st):
    """
    For each (route_id, stop_id): count AM-peak arrivals, derive headway.
    headway_min = (3h window in minutes) / n_trips, capped at 120 min (no-service sentinel).
    """
    peak_st = peak_st.copy()
    peak_st["stop_id"] = peak_st["stop_id"].astype(str)
    g = peak_st.groupby(["route_id", "stop_id"], as_index=False).size().rename(columns={"size": "n_trips"})
    window_min = (PEAK_AM_END_SEC - PEAK_AM_START_SEC) / 60.0
    g["headway_min"] = np.where(g["n_trips"] > 0, window_min / g["n_trips"], 120.0)
    g["headway_min"] = g["headway_min"].clip(upper=120.0)
    return g


def stops_to_tracts(stops_df, tracts_gdf):
    """Spatial join: each stop → tract(s) whose 500m-walking-buffer contains it."""
    stops_df = stops_df.copy()
    stops_df["stop_id"] = stops_df["stop_id"].astype(str)
    stops_gdf = gpd.GeoDataFrame(
        stops_df,
        geometry=gpd.points_from_xy(stops_df["stop_lon"], stops_df["stop_lat"]),
        crs="EPSG:4326",
    )
    # Project to meters (Florida East State Plane 2236 is appropriate for Miami-Dade)
    stops_m = stops_gdf.to_crs("EPSG:2236")
    tracts_m = tracts_gdf.to_crs("EPSG:2236")
    # Buffer tracts outward by 500m so we catch nearby stops too
    tracts_buf = tracts_m.copy()
    tracts_buf["geometry"] = tracts_buf.geometry.buffer(WALK_BUFFER_METERS)
    joined = gpd.sjoin(stops_m[["stop_id", "geometry"]], tracts_buf[["GEOID", "geometry"]],
                       how="inner", predicate="within")
    return joined[["stop_id", "GEOID"]].drop_duplicates()


def build_tract_routes(stop_tract_map, stop_route_metrics, routes_df):
    """For each tract, aggregate the routes serving its in-walking-range stops."""
    # stop_tract_map: stop_id → GEOID (many-to-many)
    # stop_route_metrics: (route_id, stop_id, n_trips, headway_min)
    joined = stop_route_metrics.merge(stop_tract_map, on="stop_id", how="inner")

    # For each (tract, route): best headway among stops of that route in the tract.
    per_tract_route = (
        joined.groupby(["GEOID", "route_id"])
        .agg(n_stops=("stop_id", "nunique"),
             best_headway_min=("headway_min", "min"),
             total_trips=("n_trips", "sum"))
        .reset_index()
        .merge(routes_df[["route_id", "route_short_name", "route_long_name", "route_type"]],
               on="route_id", how="left")
    )
    return per_tract_route


def tract_summary(per_tract_route):
    """One row per tract with aggregate metrics + top routes list."""
    summary = (
        per_tract_route.groupby("GEOID")
        .agg(n_routes=("route_id", "nunique"),
             n_stops_served=("n_stops", "sum"),
             min_headway_min=("best_headway_min", "min"),
             max_headway_min=("best_headway_min", "max"),
             median_headway_min=("best_headway_min", "median"),
             total_am_trips=("total_trips", "sum"))
        .reset_index()
    )
    # Top 3 routes per tract (by total_trips served)
    tops = (
        per_tract_route.sort_values(["GEOID", "total_trips"], ascending=[True, False])
        .groupby("GEOID")
        .head(3)
        .assign(label=lambda d: d["route_short_name"].astype(str) + " (" + d["best_headway_min"].round(0).astype(int).astype(str) + "min)")
        .groupby("GEOID")["label"].apply(lambda s: " | ".join(s))
        .reset_index()
        .rename(columns={"label": "top_routes"})
    )
    return summary.merge(tops, on="GEOID", how="left")


def problem_routes(per_tract_route, baseline_df):
    """
    Rank routes by impact:  #Critical+High tracts served × worst headway in those tracts.
    Surfaces which routes are both (a) in bad shape and (b) serving the populations
    the simulator flagged as priority.
    """
    crit_high = baseline_df.loc[
        baseline_df["equity_tier"].isin(["Critical", "High"]), "tract_geoid"
    ].astype(str).tolist()
    # tract_geoid in baseline is full 11-digit FIPS; GEOID from TIGER is also 11-digit.
    in_scope = per_tract_route[per_tract_route["GEOID"].isin(crit_high)]
    r = (
        in_scope.groupby(["route_id", "route_short_name", "route_long_name"])
        .agg(n_critical_high_tracts=("GEOID", "nunique"),
             worst_headway_min=("best_headway_min", "max"),
             median_headway_min=("best_headway_min", "median"))
        .reset_index()
    )
    r["problem_score"] = r["n_critical_high_tracts"] * r["worst_headway_min"]
    return r.sort_values("problem_score", ascending=False)


def tract_narratives(tract_summary_df, per_tract_route, baseline_df):
    """Short human-readable string per tract for Gradio."""
    base = baseline_df.set_index(baseline_df["tract_geoid"].astype(str))
    by_tract_routes = per_tract_route.sort_values(
        ["GEOID", "best_headway_min"]
    ).groupby("GEOID")

    out = {}
    for _, row in tract_summary_df.iterrows():
        geoid = row["GEOID"]
        if geoid not in base.index:
            continue
        b = base.loc[geoid]
        tier = b["equity_tier"]
        fragile = bool(b["flag_fragile"])

        routes_here = by_tract_routes.get_group(geoid) if geoid in by_tract_routes.groups else None
        if routes_here is None or len(routes_here) == 0:
            out[geoid] = (
                f"Tract {geoid} [{tier}] has NO routes with AM-peak service within 500m "
                f"(worst-case isolation)."
            )
            continue

        worst = routes_here.iloc[-1]
        best = routes_here.iloc[0]
        n_routes = row["n_routes"]
        n_stops = int(row["n_stops_served"])

        parts = [
            f"Tract {geoid} [{tier}]" + (" (fragile)" if fragile else ""),
            f"{n_routes} routes / {n_stops} stops within 500m (weekday AM peak).",
            f"Best route: {best['route_short_name']} — {best['best_headway_min']:.0f}min headway.",
            f"Worst route: {worst['route_short_name']} — {worst['best_headway_min']:.0f}min headway.",
        ]
        if row["max_headway_min"] >= 60:
            parts.append(
                "Bottleneck: headway >= 60min on at least one route. "
                "Lever candidate: freq_peak_am_tph on this route."
            )
        out[geoid] = " ".join(parts)
    return out


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    stops, routes, trips, calendar, stop_times = load_gtfs()

    log("Filtering to weekday AM-peak trips (Mon-Fri 06:00-09:00)...")
    peak_st = weekday_peak_trips(trips, calendar, stop_times)

    log("Computing per-(route, stop) headway...")
    stop_route_metrics = per_stop_route_metrics(peak_st)
    log(f"  (route, stop) pairs: {len(stop_route_metrics):,}")

    log("Loading baseline + fetching tract geometries...")
    baseline = pd.read_csv(BASELINE_CSV)
    baseline["tract_geoid"] = baseline["tract_geoid"].astype(str)
    tracts = fetch_tracts(baseline["tract_geoid"].tolist())

    log(f"Spatial-joining {len(stops):,} stops to {len(tracts)} tracts (500m walking buffer)...")
    stop_tract_map = stops_to_tracts(stops, tracts)
    log(f"  stop→tract links: {len(stop_tract_map):,}")

    log("Aggregating per tract...")
    per_tract_route = build_tract_routes(stop_tract_map, stop_route_metrics, routes)
    summary = tract_summary(per_tract_route)
    log(f"  tracts with at least one served route: {len(summary)}")

    log("Ranking problem routes...")
    problems = problem_routes(per_tract_route, baseline)

    log("Generating per-tract narratives...")
    narratives = tract_narratives(summary, per_tract_route, baseline)

    # Write outputs
    per_tract_route.to_csv(HERE / "City2Graph_Tract_Routes.csv", index=False)
    summary.to_csv(HERE / "City2Graph_Tract_Summary.csv", index=False)
    problems.to_csv(HERE / "City2Graph_Problem_Routes.csv", index=False)
    (HERE / "City2Graph_Tract_Narratives.json").write_text(json.dumps(narratives, indent=2))

    log("Done.")
    log(f"  Tract-route pairs:  City2Graph_Tract_Routes.csv         ({len(per_tract_route):,} rows)")
    log(f"  Tract summary:      City2Graph_Tract_Summary.csv         ({len(summary):,} rows)")
    log(f"  Problem routes:     City2Graph_Problem_Routes.csv        ({len(problems):,} rows)")
    log(f"  Tract narratives:   City2Graph_Tract_Narratives.json     ({len(narratives):,} entries)")

    # Show top 5 problem routes + a few sample narratives
    print("\nTop 5 problem routes (Critical+High scope):")
    print(problems.head(5).to_string(index=False))
    print("\nSample narratives:")
    for gid in list(narratives.keys())[:3]:
        print(f"  {gid}: {narratives[gid]}")


if __name__ == "__main__":
    main()
