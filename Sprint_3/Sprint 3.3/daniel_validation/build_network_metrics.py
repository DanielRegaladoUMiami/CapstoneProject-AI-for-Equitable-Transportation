"""
city2graph — real NetworkX analysis over the Miami-Dade GTFS feed.

Builds a stop-level weighted graph (edges = service connections with
travel_time + frequency), computes per-stop centrality + shortest-path
reachability to Downtown Miami, and aggregates per census tract.

Outputs
-------
City2Graph_Network_Metrics.csv   per-tract network stats (504 tracts)
City2Graph_Stop_Metrics.csv      per-stop raw centrality (for QA)
City2Graph_Graph_Summary.txt     top-level graph stats

Pipeline
--------
1. city2graph.load_gtfs(gtfs.zip) → DuckDB with GTFS tables
2. city2graph.travel_summary_graph(..., as_nx=True) →
   nx.Graph (nodes=stops with lat/lon, edges weighted by travel_time_sec)
3. networkx.degree_centrality, betweenness (approx via k=500 samples),
   closeness — ranked per stop
4. Shortest-path to Government Center (Metrorail hub, stop closest to
   25.778/-80.190 lat/lon) by travel_time_sec — a "reachability to
   downtown jobs" proxy
5. Spatial-join stops to tracts (500m buffer) and aggregate stop metrics
   to tract-level (mean, min, max)
"""
from __future__ import annotations

import warnings
warnings.filterwarnings("ignore")

import json
from pathlib import Path

import city2graph
import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
from shapely.geometry import Point

HERE = Path(__file__).resolve().parent
GTFS_ZIP = HERE / "gtfs" / "gtfs.zip"
BASELINE = HERE.parent.parent / "Sprint 3.1" / "Sprint3_Baseline_State.csv"
GEOJSON = HERE / "miami_dade_tracts.geojson"

# Government Center (Metrorail hub, downtown Miami) — anchor for
# shortest-path reachability.
DOWNTOWN_LAT = 25.778
DOWNTOWN_LON = -80.190

# Peak AM window + reasonable service calendar for city2graph
PEAK_START = "06:00:00"
PEAK_END = "09:00:00"

WALK_BUFFER_M = 500


def log(msg):
    print(f"[network] {msg}", flush=True)


# ---------------------------------------------------------------------------
# Build graph via city2graph
# ---------------------------------------------------------------------------

def build_graph():
    log("Loading GTFS into DuckDB via city2graph.load_gtfs...")
    con = city2graph.load_gtfs(str(GTFS_ZIP))

    log(f"Building travel-summary graph for weekday AM peak {PEAK_START}-{PEAK_END}...")
    G = city2graph.travel_summary_graph(
        con,
        start_time=PEAK_START,
        end_time=PEAK_END,
        as_nx=True,
        directed=False,
        use_frequencies=False,
    )
    log(f"  {G.number_of_nodes():,} nodes · {G.number_of_edges():,} edges")
    return G


# ---------------------------------------------------------------------------
# Node-level metrics
# ---------------------------------------------------------------------------

def compute_stop_metrics(G):
    log("Extracting node coordinates...")
    nodes_data = {}
    for n, data in G.nodes(data=True):
        # city2graph stores 'pos' as (lon, lat) or geometry
        geom = data.get("geometry") or data.get("pos")
        if hasattr(geom, "x"):
            nodes_data[n] = (geom.x, geom.y)
        elif isinstance(geom, (tuple, list)) and len(geom) >= 2:
            nodes_data[n] = (geom[0], geom[1])
    log(f"  stops with coordinates: {len(nodes_data):,}")

    log("Degree centrality...")
    degree_cent = nx.degree_centrality(G)

    log("Closeness centrality (on giant connected component)...")
    if not nx.is_connected(G):
        gcc_nodes = max(nx.connected_components(G), key=len)
        G_gcc = G.subgraph(gcc_nodes).copy()
        log(f"  GCC has {G_gcc.number_of_nodes():,} / {G.number_of_nodes():,} nodes")
    else:
        G_gcc = G
    closeness = nx.closeness_centrality(G_gcc, distance="travel_time_sec")

    log("Betweenness centrality (sampled, k=300)...")
    betweenness = nx.betweenness_centrality(
        G_gcc, k=min(300, G_gcc.number_of_nodes()),
        weight="travel_time_sec", seed=42,
    )

    log(f"Shortest-path time to downtown ({DOWNTOWN_LAT}, {DOWNTOWN_LON})...")
    # Find node closest to downtown
    best_node, best_d2 = None, float("inf")
    for n, (lon, lat) in nodes_data.items():
        d2 = (lat - DOWNTOWN_LAT) ** 2 + (lon - DOWNTOWN_LON) ** 2
        if d2 < best_d2:
            best_d2, best_node = d2, n
    log(f"  downtown anchor stop = {best_node}")
    try:
        sp = nx.single_source_dijkstra_path_length(
            G_gcc, best_node, weight="travel_time_sec"
        )
    except Exception as e:
        log(f"  shortest-path failed: {e}")
        sp = {}

    rows = []
    for n, (lon, lat) in nodes_data.items():
        rows.append({
            "stop_id": str(n),
            "lon": lon,
            "lat": lat,
            "degree_centrality": degree_cent.get(n, 0.0),
            "closeness": closeness.get(n, 0.0),
            "betweenness": betweenness.get(n, 0.0),
            "travel_sec_to_downtown": sp.get(n, float("nan")),
        })
    out = pd.DataFrame(rows)
    out["travel_min_to_downtown"] = out["travel_sec_to_downtown"] / 60.0
    out["is_isolated"] = out["travel_sec_to_downtown"].isna().astype(int)
    return out


# ---------------------------------------------------------------------------
# Per-tract aggregation (spatial join stop→tract with walking buffer)
# ---------------------------------------------------------------------------

def tracts_metrics(stop_metrics, baseline):
    log("Loading tract geometries...")
    gdf = gpd.read_file(GEOJSON)
    gdf["GEOID"] = gdf["GEOID"].astype(str)

    log(f"Spatial-joining {len(stop_metrics):,} stops to {len(gdf)} tracts (buffer {WALK_BUFFER_M}m)...")
    stops_gdf = gpd.GeoDataFrame(
        stop_metrics,
        geometry=gpd.points_from_xy(stop_metrics["lon"], stop_metrics["lat"]),
        crs="EPSG:4326",
    ).to_crs("EPSG:2236")
    tracts_buf = gdf.to_crs("EPSG:2236").copy()
    tracts_buf["geometry"] = tracts_buf.geometry.buffer(WALK_BUFFER_M)
    joined = gpd.sjoin(
        stops_gdf, tracts_buf[["GEOID", "geometry"]],
        how="inner", predicate="within",
    )

    log("Aggregating per tract...")
    agg = joined.groupby("GEOID").agg(
        n_stops_served=("stop_id", "nunique"),
        mean_degree_centrality=("degree_centrality", "mean"),
        max_degree_centrality=("degree_centrality", "max"),
        mean_closeness=("closeness", "mean"),
        mean_betweenness=("betweenness", "mean"),
        max_betweenness=("betweenness", "max"),
        min_travel_min_to_downtown=("travel_min_to_downtown", "min"),
        mean_travel_min_to_downtown=("travel_min_to_downtown", "mean"),
        pct_isolated=("is_isolated", "mean"),
    ).reset_index()
    agg["pct_isolated"] = (agg["pct_isolated"] * 100).round(1)

    # Mark tracts with no stop access
    baseline["tract_geoid"] = baseline["tract_geoid"].astype(str)
    all_geoids = baseline[["tract_geoid"]].rename(columns={"tract_geoid": "GEOID"})
    agg = all_geoids.merge(agg, on="GEOID", how="left")

    # Rank fields (higher = better connected, except travel time)
    for col, ascending in [
        ("mean_closeness", False),
        ("mean_betweenness", False),
        ("mean_degree_centrality", False),
        ("min_travel_min_to_downtown", True),
    ]:
        agg[f"{col}_rank"] = agg[col].rank(method="min", ascending=ascending).astype("Int64")

    agg["n_tracts"] = len(all_geoids)
    return agg


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    G = build_graph()
    stop_metrics = compute_stop_metrics(G)
    baseline = pd.read_csv(BASELINE)
    tract_metrics = tracts_metrics(stop_metrics, baseline)

    stop_metrics.to_csv(HERE / "City2Graph_Stop_Metrics.csv", index=False)
    tract_metrics.to_csv(HERE / "City2Graph_Network_Metrics.csv", index=False)

    summary = [
        f"city2graph graph summary (weekday AM {PEAK_START}-{PEAK_END})",
        f"  nodes (stops):   {G.number_of_nodes():,}",
        f"  edges (service): {G.number_of_edges():,}",
        f"  connected?       {nx.is_connected(G)}",
        f"  stops with coords: {len(stop_metrics):,}",
        f"  tracts with network coverage: {tract_metrics['n_stops_served'].notna().sum()}/{len(tract_metrics)}",
        f"  avg travel-min to downtown: {stop_metrics['travel_min_to_downtown'].mean():.1f} min",
        f"  stops unreachable from downtown: {int(stop_metrics['is_isolated'].sum())}",
    ]
    (HERE / "City2Graph_Graph_Summary.txt").write_text("\n".join(summary))
    for line in summary:
        print(line)

    print()
    print("Outputs:")
    print(f"  Stop-level metrics:  City2Graph_Stop_Metrics.csv      ({len(stop_metrics):,} rows)")
    print(f"  Tract aggregated:    City2Graph_Network_Metrics.csv   ({len(tract_metrics):,} rows)")


if __name__ == "__main__":
    main()
