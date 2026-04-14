"""
Miami-Dade Transit Equity Simulator — Gradio app for Hugging Face Spaces.

Built from Sprint_3_Gradio_V3_fixed.ipynb. Wires the simulator.py engine
(XGBoost v3, proportional-change equity formula) to an interactive dashboard
with per-tract narratives, before/after maps, tier-shift matrix, and a
route-level City2Graph diagnostic.

Auto-generated from the notebook; re-run the exporter to update.
"""
import os, sys, subprocess, importlib.util, traceback, warnings
warnings.filterwarnings("ignore")

# ── cell 1 ──
# ── 0. Install & Imports ──────────────────────────────────────────────────────
import subprocess, sys
for pkg in ["gradio", "geopandas", "plotly", "joblib", "xgboost", "requests"]:
    try:
        __import__(pkg.replace("-", "_"))
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"])

import gradio as gr
import pandas as pd
import numpy as np
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
import joblib
import requests, json, os, importlib.util
import warnings
warnings.filterwarnings("ignore")
print("Imports OK")


# ── cell 2 ──
# ── 1. Load Data & Simulator ──────────────────────────────────────────────────
import traceback

BASELINE_PATH = "Sprint3_Baseline_State.csv"
FEATURES_PATH = "Sprint2b_Modeling_Features_NotebookOutput.csv"
MODEL_PATH    = "Sprint2b_XGBoost_v3.pkl"
SCALER_PATH   = "Sprint2b_Scaler_v3.pkl"
SIM_PATH      = "simulator.py"

FEATURE_NAMES = [
    "headway_early_min", "headway_peak_am_min",
    "freq_early_tph", "freq_peak_am_tph",
    "weekend_weekday_ratio", "rail_trip_share",
    "neighbor_mean_equity_score", "neighbor_mean_headway_peak", "n_neighbors",
    "trend_commute_public_transit_pct", "trend_commute_drove_alone_pct",
    "trend_commute_wfh_pct", "trend_mean_commute_time_min",
]

# ── Load main dataframe ───────────────────────────────────────────────────────
if os.path.exists(BASELINE_PATH):
    df = pd.read_csv(BASELINE_PATH)
    USING_BASELINE = True
    print("Loaded Sprint3 baseline: " + str(len(df)) + " tracts, " + str(len(df.columns)) + " columns")
elif os.path.exists(FEATURES_PATH):
    df = pd.read_csv(FEATURES_PATH)
    USING_BASELINE = False
    print("WARNING: Sprint3_Baseline_State.csv not found -- using Sprint2b features CSV (V2 fallback)")
else:
    raise FileNotFoundError("Neither baseline CSV nor features CSV found.")

# ── Load XGBoost model ───────────────────────────────────────────────────────
model, scaler = None, None
if os.path.exists(MODEL_PATH):
    model  = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH) if os.path.exists(SCALER_PATH) else None
    print("XGBoost model loaded")
else:
    print("WARNING: " + MODEL_PATH + " not found -- using composite_access_deficit as proxy score")

# ── File diagnostic (always runs so you can see what is missing) ──────────────
print("\n--- File check ---")
for fname in ["simulator.py", BASELINE_PATH, MODEL_PATH, SCALER_PATH,
              "Sprint3_Need_OLS_Coefficients.json", "Sprint3_Lever_Catalog.json"]:
    print(fname + ": " + ("FOUND" if os.path.exists(fname) else "MISSING"))
print("-------------------\n")

# ── Import simulator (Sprint 3.2) ─────────────────────────────────────────────
sim = None
if os.path.exists("simulator.py") and os.path.exists(BASELINE_PATH):
    try:
        spec = importlib.util.spec_from_file_location("simulator", "simulator.py")
        sim_module = importlib.util.module_from_spec(spec)
        sys.modules["simulator"] = sim_module  # required for @dataclass to resolve module
        spec.loader.exec_module(sim_module)
        Simulator = sim_module.Simulator

        # Print actual signature so we can see what arguments it takes
        import inspect
        sig = inspect.signature(Simulator.__init__)
        print("Simulator.__init__ signature: " + str(sig))
        params = list(sig.parameters.keys())  # e.g. ['self', 'baseline_path', 'model_path', ...]

        # Build kwargs using only parameter names the Simulator actually accepts
        kwargs = {}
        if "baseline_path" in params:
            kwargs["baseline_path"] = BASELINE_PATH
        if "model_path" in params:
            kwargs["model_path"] = MODEL_PATH if os.path.exists(MODEL_PATH) else None
        if "scaler_path" in params:
            kwargs["scaler_path"] = SCALER_PATH if os.path.exists(SCALER_PATH) else None
        if "need_coef_path" in params:
            kwargs["need_coef_path"] = (
                "Sprint3_Need_OLS_Coefficients.json"
                if os.path.exists("Sprint3_Need_OLS_Coefficients.json") else None
            )
        if "lever_catalog_path" in params:
            kwargs["lever_catalog_path"] = (
                "Sprint3_Lever_Catalog.json"
                if os.path.exists("Sprint3_Lever_Catalog.json") else None
            )
        print("Calling Simulator with kwargs: " + str(list(kwargs.keys())))
        sim = Simulator(**kwargs)
        print("Simulator loaded -- What-If will run against all 504 tracts.")
    except Exception:
        print("WARNING: simulator.py found but failed to load. Full traceback:")
        traceback.print_exc()
        print("Falling back to V2 single-tract what-if logic.")
else:
    print("WARNING: simulator.py or baseline CSV not found -- V2 fallback active")


# ── cell 3 ──
# ── 1b. Load City2Graph diagnostics (route-level per-tract data) ──────────────
# Produced by build_city2graph_diagnostics.py. Safe to skip if files aren't present.
city2graph_routes = None
city2graph_narratives = {}
city2graph_problem_routes = None

for fname in ['City2Graph_Tract_Routes.csv']:
    if os.path.exists(fname):
        city2graph_routes = pd.read_csv(fname, dtype={'GEOID': str})
        print('Loaded City2Graph_Tract_Routes.csv: ' + str(len(city2graph_routes)) + ' tract-route pairs')
        break

if os.path.exists('City2Graph_Tract_Narratives.json'):
    import json as _json
    with open('City2Graph_Tract_Narratives.json') as _f:
        city2graph_narratives = _json.load(_f)
    print('Loaded City2Graph_Tract_Narratives.json: ' + str(len(city2graph_narratives)) + ' tracts')

if os.path.exists('City2Graph_Problem_Routes.csv'):
    city2graph_problem_routes = pd.read_csv('City2Graph_Problem_Routes.csv')
    print('Loaded City2Graph_Problem_Routes.csv: ' + str(len(city2graph_problem_routes)) + ' routes')

if city2graph_routes is None:
    print('WARNING: City2Graph outputs not found. Route-level narrative will be skipped.')


# ── cell 4 ──
# ── 2. Build Deficit & Equity Columns ────────────────────────────────────────
if USING_BASELINE and "deficit_predicted" in df.columns:
    print("Using pre-computed deficit_predicted from Sprint3 baseline")
elif model is not None:
    X = df[FEATURE_NAMES].fillna(0)
    if scaler is not None:
        X = scaler.transform(X)
    df["deficit_predicted"] = model.predict(X)
    print("deficit_predicted computed via XGBoost")
else:
    col = df["composite_access_deficit"]
    df["deficit_predicted"] = (col - col.min()) / (col.max() - col.min())
    print("deficit_predicted proxied from composite_access_deficit")

if "equity_priority_score" not in df.columns:
    df["equity_priority_score"] = df["deficit_predicted"]

if USING_BASELINE and "equity_tier" in df.columns:
    df["equity_tier"] = df["equity_tier"]
    print("Using equity_tier from Sprint3 baseline (Sprint 2a fixed cutoffs)")
else:
    df["equity_tier"] = pd.qcut(
        df["deficit_predicted"], 4,
        labels=["Low", "Moderate", "High", "Critical"]
    )
    print("equity_tier derived via quantile cut")

if "flag_fragile" not in df.columns:
    df["flag_fragile"] = False

tier_counts = df["equity_tier"].value_counts()
print("Tier distribution:\n" + str(tier_counts))


# ── cell 5 ──
# ── 3. Fetch Miami-Dade Census Tract GeoJSON ──────────────────────────────────
GEOJSON_URL = (
    "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/"
    "tigerWMS_ACS2023/MapServer/8/query"
    "?where=STATE%3D'12'+AND+COUNTY%3D'086'"
    "&outFields=GEOID,NAME&f=geojson&outSR=4326"
)
GEOJSON_CACHE = "miami_dade_tracts.geojson"

def load_geodata():
    if os.path.exists(GEOJSON_CACHE):
        print("GeoJSON loaded from cache")
        return gpd.read_file(GEOJSON_CACHE)
    print("Downloading Miami-Dade tract geometries from Census Bureau...")
    r = requests.get(GEOJSON_URL, timeout=30)
    with open(GEOJSON_CACHE, "w") as f:
        json.dump(r.json(), f)
    gdf = gpd.read_file(GEOJSON_CACHE)
    print("Downloaded " + str(len(gdf)) + " tracts")
    return gdf

gdf_raw = load_geodata()
df["geoid_str"] = df["tract_geoid"].astype(str).str.zfill(11)
gdf_raw["GEOID"] = gdf_raw["GEOID"].astype(str).str.zfill(11)
gdf = gdf_raw.merge(df, left_on="GEOID", right_on="geoid_str", how="inner")
gdf = gdf.to_crs(epsg=4326)
print("Merged: " + str(len(gdf)) + " tracts with geometry + equity scores")


# ── cell 6 ──
# ── 4. Map Builders ───────────────────────────────────────────────────────────
TIER_ORDER  = ["Low", "Moderate", "High", "Critical"]
COLOR_SCALE = [
    [0.0,  "#27ae60"],
    [0.33, "#f1c40f"],
    [0.66, "#e67e22"],
    [1.0,  "#c0392b"],
]

# Ensure equity_tier is a plain string column (not Categorical) so .isin() and JSON work
gdf["equity_tier"] = gdf["equity_tier"].astype(str)


def _make_empty_fig(msg="No data"):
    fig = go.Figure()
    fig.update_layout(
        title=msg, height=500,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig


def _choropleth(subset, color_col, title):
    """Build one choropleth figure from a GeoDataFrame subset."""
    if subset.empty:
        return _make_empty_fig("No tracts match current filters")

    # Ensure the color column exists
    if color_col not in subset.columns:
        return _make_empty_fig("Column '" + color_col + "' not found in data")

    # Build hover_data dict — only include columns that actually exist in subset
    hover_candidates = {
        "equity_tier":         True,
        "poverty_rate_pct":  ":.1f",
        "hh_no_vehicle_pct": ":.1f",
        "stop_count":        ":.0f",
        "equity_delta":      ":.4f",
        "tier_changed":      True,
    }
    hover = {col: fmt for col, fmt in hover_candidates.items()
             if col in subset.columns and col != color_col}

    labels = {
        color_col:           "Score",
        "equity_tier":         "Tier",
        "poverty_rate_pct":  "Poverty %",
        "hh_no_vehicle_pct": "No Vehicle %",
        "stop_count":        "Stops",
        "equity_delta":      "Equity Delta",
        "tier_changed":      "Tier Changed",
    }

    try:
        geojson_dict = json.loads(subset.to_json())
        fig = px.choropleth_mapbox(
            subset,
            geojson=geojson_dict,
            locations=subset.index,
            color=color_col,
            color_continuous_scale=COLOR_SCALE,
            range_color=[0, 1],
            mapbox_style="open-street-map",
            zoom=9, center={"lat": 25.77, "lon": -80.19},
            opacity=0.65,
            hover_data=hover,
            labels=labels,
        )
        fig.update_layout(
            title=dict(text=title, font=dict(size=13)),
            margin=dict(l=0, r=0, t=40, b=0),
            height=500,
            coloraxis_colorbar=dict(
                title="Score",
                tickvals=[0, 0.25, 0.5, 0.75, 1.0],
                ticktext=["0", "0.25", "0.50", "0.75", "1"],
                len=0.6,
            ),
        )
        return fig
    except Exception as e:
        return _make_empty_fig("Map error: " + str(e))


def build_map(selected_tiers, score_threshold):
    """Tab 1: current state map filtered by tier and min score."""
    # Guard against None inputs (can happen on Gradio initial load)
    if selected_tiers is None:
        selected_tiers = TIER_ORDER
    if score_threshold is None:
        score_threshold = 0.0
    try:
        mask = gdf["equity_tier"].isin(selected_tiers) & (gdf["deficit_predicted"] >= score_threshold)
        subset = gdf[mask].copy()
        return _choropleth(
            subset, "deficit_predicted",
            "Current Deficit Map  -  " + str(len(subset)) + " tracts shown"
        )
    except Exception as e:
        return _make_empty_fig("build_map error: " + str(e))


def build_before_after_maps(result_df):
    """
    Build before/after maps from a SimulationResult tract_df.
    Expects columns: tract_geoid, deficit_before, deficit_after,
                     tier_before, tier_after, equity_delta
    Returns (fig_before, fig_after).
    """
    try:
        result_df = result_df.copy()
        result_df["geoid_str"] = result_df["tract_geoid"].astype(str).str.zfill(11)
        result_df["tier_changed"] = (result_df["tier_before"] != result_df["tier_after"]).astype(int)

        after_cols = ["geoid_str", "deficit_after", "tier_after", "equity_delta", "tier_changed"]
        for opt_col in ["poverty_rate_pct", "hh_no_vehicle_pct", "stop_count"]:
            if opt_col in result_df.columns:
                after_cols.append(opt_col)
        after_cols = [c for c in after_cols if c in result_df.columns]

        after_renamed = result_df[after_cols].rename(columns={
            "tier_after": "equity_tier", "geoid_str": "GEOID"
        })
        after_renamed["equity_tier"] = after_renamed["equity_tier"].astype(str)

        gdf_after = gdf_raw.merge(after_renamed, on="GEOID", how="inner").to_crs(epsg=4326)

        fig_before = _choropleth(gdf.copy(), "deficit_predicted", "Before: Current State")
        fig_after  = _choropleth(gdf_after,  "deficit_after",     "After: Scenario")
        return fig_before, fig_after
    except Exception as e:
        err_fig = _make_empty_fig("Map error: " + str(e))
        return err_fig, err_fig


# ── cell 7 ──
# ── 5. Expanded Narrative Generator ──────────────────────────────────────────

def _trend_arrow(val, positive_is_bad=True):
    """Return trend direction indicator."""
    if val is None or (isinstance(val, float) and np.isnan(val)) or val == 0:
        return "stable"
    if positive_is_bad:
        return ("UP " + format(val, "+.2f") + " (worsening)") if val > 0 else ("DOWN " + format(val, "+.2f") + " (improving)")
    else:
        return ("UP " + format(val, "+.2f") + " (improving)") if val > 0 else ("DOWN " + format(val, "+.2f") + " (worsening)")


def _g(row, col, fmt=".1f"):
    """Safe get + format from a row."""
    v = row.get(col, None)
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "N/A"
    return format(v, fmt)


def generate_narrative(tract_id_input):
    if not tract_id_input:
        return "Enter a tract ID above to see its detailed narrative."
    try:
        tid = str(int(float(tract_id_input))).zfill(11)
    except Exception:
        tid = str(tract_id_input).strip().zfill(11)

    match = gdf[gdf["GEOID"] == tid]
    if match.empty:
        match = gdf[gdf["GEOID"].str.contains(tract_id_input.strip(), na=False)]
    if match.empty:
        return "Tract '" + tract_id_input + "' not found. Try a full 11-digit GEOID like 12086010100."

    row   = match.iloc[0]
    tier  = str(row.get("equity_tier", "Unknown"))
    fragile = bool(row.get("flag_fragile", False))
    tier_emoji = {"Low": "green", "Moderate": "yellow", "High": "orange", "Critical": "red"}.get(tier, "?")

    lines = [
        "### Tract " + tract_id_input,
        "**Equity Tier: " + tier + "**" + ("  FRAGILE - projected to worsen" if fragile else ""),
        "- Equity Priority Score: **" + _g(row, "equity_priority_score", ".3f") + "**",
        "- Service Deficit Score: **" + _g(row, "deficit_predicted", ".3f") + "**",
    ]

    if "projected_need_2027" in row.index:
        lines.append("- Projected Need (2027): **" + _g(row, "projected_need_2027", ".3f") + "**")

    lines += [
        "",
        "---",
        "#### Demographics - Current",
        "| Indicator | Value |",
        "|-----------|-------|",
        "| Poverty rate | " + _g(row, "poverty_rate_pct") + "% |",
        "| Households without a vehicle | " + _g(row, "hh_no_vehicle_pct") + "% |",
        "| SNAP/food stamp recipients | " + _g(row, "snap_benefits_pct") + "% |",
        "| Rent-burdened (50%+ income on rent) | " + _g(row, "rent_burden_50pct_plus") + "% |",
        "| Unemployment rate | " + _g(row, "unemployment_rate_pct") + "% |",
        "",
        "#### Demographic Trends (ACS direction)",
        "| Indicator | Trend |",
        "|-----------|-------|",
        "| Poverty rate | " + _trend_arrow(row.get("trend_poverty_rate_pct"), True) + " |",
        "| No-vehicle households | " + _trend_arrow(row.get("trend_hh_no_vehicle_pct"), True) + " |",
        "| Rent burden | " + _trend_arrow(row.get("trend_rent_burden_50pct_plus"), True) + " |",
        "| Unemployment | " + _trend_arrow(row.get("trend_unemployment_rate_pct"), True) + " |",
        "| Median household income | " + _trend_arrow(row.get("trend_median_household_income"), False) + " |",
        "| Transit commute share | " + _trend_arrow(row.get("trend_commute_public_transit_pct"), False) + " |",
        "",
        "#### Transit Service",
        "| Indicator | Value |",
        "|-----------|-------|",
        "| Bus stops | " + _g(row, "stop_count", ".0f") + " |",
        "| Routes | " + _g(row, "route_count", ".0f") + " |",
        "| Peak AM headway | " + _g(row, "headway_peak_am_min", ".0f") + " min |",
        "| Peak AM frequency | " + _g(row, "freq_peak_am_tph", ".1f") + " trips/hr |",
        "| Early AM frequency | " + _g(row, "freq_early_tph", ".1f") + " trips/hr |",
        "| Weekend/weekday ratio | " + _g(row, "weekend_weekday_ratio", ".2f") + " |",
        "| Service span | " + _g(row, "mean_service_span_hours", ".1f") + " hrs/day |",
        "| Rail trip share | " + _g(row, "rail_trip_share", ".3f") + " |",
        "| Transit jobs accessible (30 min) | " + _g(row, "transit_jobs_30_mean", ".0f") + " |",
    ]

    # Compounding risk flags (above 75th percentile on interaction features)
    interaction_flags = []
    checks = [
        ("poverty_x_low_span",        "High poverty combined with short service span"),
        ("novehicle_x_low_service",   "High car-free rate combined with low service density"),
        ("novehicle_x_weekend_gap",   "High car-free rate combined with weak weekend coverage"),
        ("rising_poverty_x_current",  "Rising poverty trend combined with already-high poverty"),
    ]
    for col, label in checks:
        if col in df.columns and col in row.index:
            val = row.get(col, None)
            if val is not None and not (isinstance(val, float) and np.isnan(val)):
                if val > df[col].quantile(0.75):
                    interaction_flags.append("WARNING: " + label)
    if interaction_flags:
        lines += ["", "#### Compounding Risk Factors"] + interaction_flags

    lines += ["", "---"]
    tier_messages = {
        "Critical": (
            "**Critical tier:** This tract shows compounding service gaps - low frequency, "
            "poor weekend coverage, and high transit dependency reinforce each other. "
            "Peak frequency improvements would have the largest modeled impact (SHAP #1, 39.6%)."
        ),
        "High": (
            "This tract has **above-average deficits**. Targeted frequency or weekend ratio "
            "improvements could meaningfully reduce transit burden."
        ),
        "Moderate": (
            "This tract has **moderate gaps**, likely concentrated in off-peak windows. "
            "Targeted schedule adjustments could close the gap efficiently."
        ),
        "Low": "This tract has **relatively good coverage** compared to the rest of Miami-Dade.",
    }
    lines.append(tier_messages.get(tier, ""))

    # ── Route-level diagnostic (City2Graph) ──
    if city2graph_routes is not None and len(city2graph_routes) > 0:
        routes_here = city2graph_routes[city2graph_routes["GEOID"] == tid]
        if len(routes_here) > 0:
            routes_here = routes_here.sort_values("best_headway_min")
            lines += [
                "",
                "---",
                "#### Route-level diagnostic (weekday AM peak, stops within 500m)",
                "| Route | Long name | Headway (min) | # stops | AM trips |",
                "|-------|-----------|---------------|---------|----------|",
            ]
            for _, rr in routes_here.iterrows():
                hdy = int(round(rr["best_headway_min"]))
                lines.append(
                    "| **" + str(rr["route_short_name"]) + "** | "
                    + str(rr.get("route_long_name", ""))[:50] + " | "
                    + str(hdy) + " | "
                    + str(int(rr["n_stops"])) + " | "
                    + str(int(rr["total_trips"])) + " |"
                )
            worst = routes_here.iloc[-1]
            best = routes_here.iloc[0]
            if worst["best_headway_min"] >= 60:
                lines += [
                    "",
                    "**Bottleneck:** route **" + str(worst["route_short_name"]) + "** (" + str(worst.get("route_long_name",""))[:60] + ") has " + str(int(round(worst["best_headway_min"]))) + "min headway. Lever candidate: increase freq_peak_am_tph on this route.",
                ]
            else:
                lines.append(
                    "All routes serving this tract have AM-peak headways < 60 min. "
                    "Best: **" + str(best["route_short_name"]) + "** at " + str(int(round(best["best_headway_min"]))) + "min."
                )
        else:
            lines += [
                "",
                "---",
                "#### Route-level diagnostic",
                "No routes with weekday AM-peak service found within 500m. "
                "This tract is a walking-access gap.",
            ]

    return "\n".join(lines)


# ── cell 8 ──
# ── 6. What-If Simulator Logic ────────────────────────────────────────────────
SCOPE_OPTIONS = [
    "All 504 tracts",
    "Critical only",
    "High + Critical",
    "Fragile tracts only",
]


def _scope_to_filter(scope_label):
    if scope_label == "All 504 tracts":
        return "all"
    elif scope_label == "Critical only":
        return df[df["equity_tier"] == "Critical"]["tract_geoid"].tolist()
    elif scope_label == "High + Critical":
        return df[df["equity_tier"].isin(["High", "Critical"])]["tract_geoid"].tolist()
    elif scope_label == "Fragile tracts only":
        return df[df["flag_fragile"] == True]["tract_geoid"].tolist()
    return "all"


def _format_tier_matrix(tier_shifts_df):
    """Render 4x4 tier shift matrix as markdown table."""
    tiers = ["Low", "Moderate", "High", "Critical"]
    header = "| From / To | " + " | ".join(tiers) + " |"
    sep    = "|" + "---|" * (len(tiers) + 1)
    rows   = [header, sep]
    for from_tier in tiers:
        row_cells = []
        for to_tier in tiers:
            try:
                val = int(tier_shifts_df.loc[from_tier, to_tier])
            except Exception:
                val = 0
            row_cells.append("**" + str(val) + "**" if from_tier == to_tier else (str(val) if val > 0 else "-"))
        rows.append("| " + from_tier + " | " + " | ".join(row_cells) + " |")
    return "\n".join(rows)


def run_whatif_simulator(freq_peak_delta, freq_early_delta, weekend_delta,
                         rail_delta, scope_label, custom_geoids_str):
    """
    Returns: (summary_md, fig_before, fig_after, tier_matrix_md)
    """
    # Parse custom GEOID list if provided
    if custom_geoids_str and custom_geoids_str.strip():
        try:
            tract_filter = [int(g.strip()) for g in custom_geoids_str.split(",") if g.strip()]
        except ValueError:
            return (
                "ERROR: Custom GEOID list must be comma-separated integers.",
                go.Figure(), go.Figure(), ""
            )
    else:
        tract_filter = _scope_to_filter(scope_label)

    empty_fig = go.Figure()
    empty_fig.update_layout(title="Maps require simulator.py", height=500)

    if sim is not None:
        # Full 504-tract simulation via simulator.py
        try:
            access_deltas = {}
            if freq_peak_delta  != 0: access_deltas["freq_peak_am_tph"]     = freq_peak_delta
            if freq_early_delta != 0: access_deltas["freq_early_tph"]       = freq_early_delta
            if weekend_delta    != 0: access_deltas["weekend_weekday_ratio"] = weekend_delta
            if rail_delta       != 0: access_deltas["rail_trip_share"]       = rail_delta

            result = sim.run(
                access_deltas=access_deltas,
                tract_filter=tract_filter,
                label="gradio_scenario"
            )
            s = result.summary
            n_scope = len(tract_filter) if isinstance(tract_filter, list) else 504
            scope_display = scope_label if not (custom_geoids_str and custom_geoids_str.strip()) else "Custom GEOIDs"

            summary_parts = [
                "### Scenario Results - " + scope_display,
                "- Tracts in scope: **" + str(n_scope) + "**",
                "- Tracts improved: **" + str(s.get("n_improved", "?")) + "**",
                "- Tier upgrades: **" + str(s.get("n_tier_upgrades", "?")) + "**",
                "- Tier downgrades: **" + str(s.get("n_tier_downgrades", 0)) + "**",
                "- Avg equity delta: **" + format(s.get("avg_equity_delta", float("nan")), ".4f") + "**",
                "- Population affected: **" + str(n_scope) + "**",
            ]
            summary_md = "\n".join(summary_parts)

            tier_md = "#### Tier Shift Matrix\n*(rows = before tier, columns = after tier)*\n\n"
            try:
                tier_md += _format_tier_matrix(result.tier_shifts)
            except Exception as e:
                tier_md += "(tier matrix unavailable: " + str(e) + ")"

            fig_before, fig_after = build_before_after_maps(result.tract_df)
            return summary_md, fig_before, fig_after, tier_md

        except Exception as e:
            return (
                "ERROR running simulator: " + str(e),
                empty_fig, empty_fig, ""
            )

    else:
        # V2 fallback: single synthetic median tract
        if model is None:
            return (
                "WARNING: Neither simulator.py nor XGBoost model loaded. Cannot run simulation.",
                empty_fig, empty_fig, ""
            )
        medians = df[FEATURE_NAMES].median()
        X_input = medians.copy()
        X_input["freq_peak_am_tph"]      = max(medians["freq_peak_am_tph"]      + freq_peak_delta,  0)
        X_input["freq_early_tph"]        = max(medians["freq_early_tph"]        + freq_early_delta, 0)
        X_input["weekend_weekday_ratio"]  = max(medians["weekend_weekday_ratio"] + weekend_delta,    0)
        X_input["rail_trip_share"]        = max(min(medians["rail_trip_share"]   + rail_delta, 1),   0)
        # Derive headways from frequencies
        fp = max(X_input["freq_peak_am_tph"],  0.01)
        fe = max(X_input["freq_early_tph"],    0.01)
        X_input["headway_peak_am_min"] = min(60 / fp, 120)
        X_input["headway_early_min"]   = min(60 / fe, 120)

        pred     = model.predict(X_input.values.reshape(1, -1))[0]
        baseline = model.predict(medians.values.reshape(1, -1))[0]
        delta    = pred - baseline
        flag     = "CRITICAL" if pred > 0.65 else "HIGH" if pred > 0.45 else "LOW"

        summary_md = "\n".join([
            "### Scenario Results (V2 fallback - synthetic median tract)",
            "Predicted deficit: **" + format(pred, ".3f") + "** [" + flag + "]",
            "vs. baseline (" + format(baseline, ".3f") + "): **" + format(delta, "+.3f") + "** "
            + ("worse" if delta > 0 else "better"),
            "",
            "*simulator.py not loaded - result uses median feature values, not 504-tract baseline.*",
        ])
        return summary_md, empty_fig, empty_fig, ""


# ── cell 9 ──
# ── 7. Summary Stats ──────────────────────────────────────────────────────────
def summary_stats():
    counts = df["equity_tier"].value_counts()
    lines = ["**Miami-Dade Transit Equity - Overview**\n"]
    lines.append(
        "Total census tracts: **" + str(len(df)) + "**  |  "
        "Model: XGBoost v3 (CV R2=0.823)\n"
    )
    for tier in ["Critical", "High", "Moderate", "Low"]:
        n   = counts.get(tier, 0)
        pct = 100 * n / len(df)
        e   = {"Critical": "CRITICAL", "High": "HIGH", "Moderate": "MODERATE", "Low": "LOW"}[tier]
        lines.append(e + " **" + tier + "**: " + str(n) + " tracts (" + format(pct, ".0f") + "%)")
    if "flag_fragile" in df.columns:
        n_fragile = int(df["flag_fragile"].sum())
        lines.append("\nFragile tracts (projected to worsen): **" + str(n_fragile) + "**")
    sim_status = "simulator.py loaded" if sim else "simulator.py not found (V2 fallback active)"
    lines.append("\n*" + sim_status + "*")
    return "\n".join(lines)


# ── cell 10 ──
# ── 8. Build Gradio App ───────────────────────────────────────────────────────
INITIAL_TIERS = ["Low", "Moderate", "High", "Critical"]

with gr.Blocks(
    title="Miami-Dade Transit Equity Dashboard",
    theme=gr.themes.Soft(),
    css=".gradio-container { max-width: 1300px !important }"
) as demo:

    gr.Markdown(
        "# Miami-Dade Transit Equity Dashboard - Sprint 3\n"
        "**University of Miami - AI for Equitable Public Transportation - Deloitte Capstone**\n"
        "Simulation engine: XGBoost v3 (CV R2=0.823) + Sprint 3.1 Baseline State."
    )
    gr.Markdown(summary_stats())

    # Tab 1: Current Deficit Map
    with gr.Tab("Map - Deficit"):
        gr.Markdown("Filter tracts by risk tier and minimum deficit score.")
        with gr.Row():
            tier_filter = gr.CheckboxGroup(
                choices=TIER_ORDER, value=INITIAL_TIERS, label="Show Risk Tiers"
            )
            score_slider = gr.Slider(
                0.0, 1.0, value=0.0, step=0.05, label="Minimum Deficit Score"
            )
        map_output = gr.Plot(label="")
        tier_filter.change(fn=build_map, inputs=[tier_filter, score_slider], outputs=map_output)
        score_slider.change(fn=build_map, inputs=[tier_filter, score_slider], outputs=map_output)
        demo.load(fn=build_map, inputs=[tier_filter, score_slider], outputs=map_output)

    # Tab 2: Tract Narrative
    with gr.Tab("Tract Narrative"):
        gr.Markdown(
            "Enter any census tract GEOID for a full demographic + transit breakdown.\n"
            "GEOIDs are 11 digits starting with 12086. Find them on the map hover tooltips."
        )
        with gr.Row():
            tract_input = gr.Textbox(
                label="Census Tract GEOID", placeholder="e.g. 12086010100", scale=2
            )
            tract_btn = gr.Button("Generate Narrative", variant="primary", scale=1)
        narrative_output = gr.Markdown(value="Enter a tract ID and click Generate Narrative.")
        tract_btn.click(fn=generate_narrative, inputs=tract_input, outputs=narrative_output)
        tract_input.submit(fn=generate_narrative, inputs=tract_input, outputs=narrative_output)

    # Tab 3: What-If Simulator
    with gr.Tab("What-If Simulator"):
        gr.Markdown(
            "Adjust transit service levers and see the effect across census tracts.\n"
            "**Sliders are deltas** (changes from baseline), not absolute values.\n\n"
            "| Lever | SHAP Importance | Baseline Mean |\n"
            "|-------|----------------|---------------|\n"
            "| Peak AM frequency (delta trips/hr) | 39.6% - #1 | 26.7 tph |\n"
            "| Weekend/weekday ratio (delta) | 21.7% - #2 | 0.43 |\n"
            "| Early AM frequency (delta trips/hr) | 6.9% - #3 | 2.98 tph |\n"
            "| Rail trip share (delta fraction) | Modal lever | 0.011 |\n"
        )
        with gr.Row():
            with gr.Column():
                gr.Markdown("**Service Levers (SHAP-ranked)**")
                s_freq_peak = gr.Slider(
                    -10.0, 10.0, value=0.0, step=0.5,
                    label="Delta Peak AM Frequency (trips/hr)  [SHAP #1]"
                )
                s_weekend = gr.Slider(
                    -0.5, 0.5, value=0.0, step=0.05,
                    label="Delta Weekend/Weekday Ratio  [SHAP #2]"
                )
                s_freq_early = gr.Slider(
                    -5.0, 5.0, value=0.0, step=0.5,
                    label="Delta Early AM Frequency (trips/hr)  [SHAP #3]"
                )
                s_rail = gr.Slider(
                    -0.1, 0.3, value=0.0, step=0.01,
                    label="Delta Rail Trip Share"
                )
            with gr.Column():
                gr.Markdown("**Scope**")
                s_scope = gr.Radio(
                    choices=SCOPE_OPTIONS, value="All 504 tracts",
                    label="Apply changes to:"
                )
                s_custom = gr.Textbox(
                    label="Custom GEOID list (overrides scope above)",
                    placeholder="e.g. 12086008904, 12086010100",
                    lines=2
                )
                gr.Markdown("Fragile tracts are those projected to worsen by 2027 (ACS trend model).")

        sim_btn     = gr.Button("Run Scenario", variant="primary", size="lg")
        sim_summary = gr.Markdown(value="Adjust levers and click Run Scenario.")

        with gr.Row():
            map_before = gr.Plot(label="Before")
            map_after  = gr.Plot(label="After")

        tier_matrix_output = gr.Markdown(value="")

        sim_btn.click(
            fn=run_whatif_simulator,
            inputs=[s_freq_peak, s_freq_early, s_weekend, s_rail, s_scope, s_custom],
            outputs=[sim_summary, map_before, map_after, tier_matrix_output]
        )

    # Tab 4: Data Table
    with gr.Tab("Data Table"):
        gr.Markdown("All 504 tracts. Sorted by equity priority score (highest first).")
        display_cols = [
            "tract_geoid", "equity_tier", "equity_priority_score", "deficit_predicted",
            "poverty_rate_pct", "hh_no_vehicle_pct", "snap_benefits_pct",
            "rent_burden_50pct_plus", "unemployment_rate_pct",
            "trend_poverty_rate_pct", "trend_hh_no_vehicle_pct",
            "stop_count", "route_count", "headway_peak_am_min",
            "freq_peak_am_tph", "weekend_weekday_ratio", "rail_trip_share",
            "flag_fragile",
        ]
        available_cols = [c for c in display_cols if c in df.columns]
        sort_col = "equity_priority_score" if "equity_priority_score" in df.columns else "deficit_predicted"
        table_df = df[available_cols].sort_values(sort_col, ascending=False).round(3)
        if "equity_tier" in table_df.columns:
            table_df["equity_tier"] = table_df["equity_tier"].astype(str)
        gr.Dataframe(value=table_df, interactive=False, wrap=False)

    gr.Markdown(
        "---\n"
        "*Data: GTFS (MDT), ACS 2019-2023, ArcGIS isochrones. Sprint 3.1 Baseline State. XGBoost v3.*"
    )


# ── cell 11 ──
# ── 9. Launch ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    demo.launch(share=True)   # share=True for Colab; remove for local

