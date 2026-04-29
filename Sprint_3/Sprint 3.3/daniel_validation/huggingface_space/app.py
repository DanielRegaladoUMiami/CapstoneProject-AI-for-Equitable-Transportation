"""
Miami-Dade Transit Equity Simulator — Gradio app for HF Spaces.

University of Miami MSBA · Deloitte · Miami-Dade County.
Production UI over Luna's Sprint 3.2 simulator + Sprint 2b XGBoost model
+ city2graph network analysis (NetworkX, real GTFS).
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import geopandas as gpd
import gradio as gr
import importlib.util
import joblib
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests

HERE = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Brand — University of Miami (orange + green on white)
# ---------------------------------------------------------------------------
UM_ORANGE = "#F47321"
UM_ORANGE_DARK = "#D95F10"
UM_GREEN = "#005030"
UM_GREEN_DEEP = "#003824"
SOFT_ORANGE_BG = "#FFF7F1"
SOFT_GREEN_BG = "#EEFBF3"
OFF_WHITE = "#F8F9FA"
BORDER = "#DEE2E6"
INK = "#1A1A1A"
MUTED = "#495057"

TIER_COLORS = {
    "Critical": "#B03A2E",
    "High": "#CA6F1E",
    "Moderate": "#D4AC0D",
    "Low": "#1E8449",
}
TIER_ORDER = ["Low", "Moderate", "High", "Critical"]

# ---------------------------------------------------------------------------
# Load data + simulator
# ---------------------------------------------------------------------------
print("Loading Sprint 3 baseline and simulator...")

df = pd.read_csv(HERE / "Sprint3_Baseline_State.csv", dtype={"tract_geoid": str})

_spec = importlib.util.spec_from_file_location("simulator", HERE / "simulator.py")
simulator_mod = importlib.util.module_from_spec(_spec)
sys.modules["simulator"] = simulator_mod
_spec.loader.exec_module(simulator_mod)
from simulator import Simulator, FEATURE_NAMES, FREQ_HEADWAY_PAIRS, HEADWAY_CAP  # type: ignore

sim = Simulator(
    baseline_path=str(HERE / "Sprint3_Baseline_State.csv"),
    model_path=str(HERE / "Sprint2b_XGBoost_v3.pkl"),
    lever_catalog_path=str(HERE / "Sprint3_Lever_Catalog.json"),
)

# Route-level diagnostic
c2g_routes = pd.read_csv(HERE / "City2Graph_Tract_Routes.csv", dtype={"GEOID": str})
c2g_problems = pd.read_csv(HERE / "City2Graph_Problem_Routes.csv")

# Real network analysis from city2graph (NetworkX on GTFS)
c2g_network = pd.read_csv(HERE / "City2Graph_Network_Metrics.csv", dtype={"GEOID": str})
c2g_graph_summary = (HERE / "City2Graph_Graph_Summary.txt").read_text() if (HERE / "City2Graph_Graph_Summary.txt").exists() else ""

# Tract geometries
geojson_path = HERE / "miami_dade_tracts.geojson"
if geojson_path.exists():
    gdf_all = gpd.read_file(geojson_path)
else:
    r = requests.get(
        "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Tracts_Blocks/MapServer/0/query",
        params={"where": "STATE='12' AND COUNTY='086'",
                "outFields": "GEOID", "outSR": "4326", "f": "geojson"},
        timeout=60,
    )
    gdf_all = gpd.read_file(r.text)
    gdf_all.to_file(geojson_path, driver="GeoJSON")

gdf = gdf_all.merge(df, left_on="GEOID", right_on="tract_geoid", how="inner")
gdf_geojson = json.loads(gdf.to_json())

print(f"  {len(df)} tracts · {len(c2g_routes)} tract-route pairs · {len(c2g_problems)} ranked routes")
print(f"  network metrics: {c2g_network['n_stops_served'].notna().sum()}/{len(c2g_network)} tracts covered")

# ---------------------------------------------------------------------------
# Scenario helpers
# ---------------------------------------------------------------------------
CRITICAL_TRACTS = df.loc[df["equity_tier"] == "Critical", "tract_geoid"].astype(int).tolist()
HIGH_CRIT_TRACTS = df.loc[df["equity_tier"].isin(["High", "Critical"]), "tract_geoid"].astype(int).tolist()
FRAGILE_TRACTS = df.loc[df["flag_fragile"] == True, "tract_geoid"].astype(int).tolist()


def run_scenario(deltas=None, targets=None, tract_filter="all", label=""):
    deltas = deltas or {}
    targets = targets or {}
    mask = sim._resolve_tract_mask(tract_filter)
    features = sim._features_base.copy()
    for feat, delta in deltas.items():
        features.loc[mask, feat] = features.loc[mask, feat] + delta
    for feat, target in targets.items():
        features.loc[mask, feat] = target
    touched = set(deltas) | set(targets)
    for fq, hw in FREQ_HEADWAY_PAIRS.items():
        if fq in touched:
            freq_vals = features.loc[mask, fq].values
            features.loc[mask, hw] = np.where(freq_vals > 0, 60.0 / freq_vals, HEADWAY_CAP)
    for lv in sim._lever_catalog["levers"]:
        lo, hi = lv["data_range"]
        features[lv["feature"]] = features[lv["feature"]].clip(lo, hi)
    features["headway_peak_am_min"] = features["headway_peak_am_min"].clip(0.0, HEADWAY_CAP)
    features["headway_early_min"] = features["headway_early_min"].clip(0.0, HEADWAY_CAP)
    deficit = sim._model.predict(features)
    equity, tier = sim._compute_equity(deficit)
    tier_base = sim._assign_tiers(sim._equity_base)
    return sim._build_result(deficit, equity, tier_base, tier, label)


PRESETS = {
    "S1": {"label": "Peak Rush Hour Boost",
           "desc": "+2 buses/hr in AM peak · Critical tracts",
           "deltas": {"freq_peak_am_tph": 2.0}, "targets": {},
           "scope": CRITICAL_TRACTS, "scope_label": f"Critical ({len(CRITICAL_TRACTS)})"},
    "S2": {"label": "Weekend Parity",
           "desc": "Weekend service to 80 pct of weekday · All tracts",
           "deltas": {}, "targets": {"weekend_weekday_ratio": 0.80},
           "scope": "all", "scope_label": "All 504"},
    "S3": {"label": "Early Service Expansion",
           "desc": "+1 bus/hr 5am-7am · High + Critical",
           "deltas": {"freq_early_tph": 1.0}, "targets": {},
           "scope": HIGH_CRIT_TRACTS, "scope_label": f"High + Critical ({len(HIGH_CRIT_TRACTS)})"},
    "S4": {"label": "Rail Modal Shift",
           "desc": "+10 pp of trips on Metrorail · All tracts",
           "deltas": {"rail_trip_share": 0.10}, "targets": {},
           "scope": "all", "scope_label": "All 504"},
    "S5": {"label": "Combined Strategy",
           "desc": "Peak +2 · Weekend 0.80 · Rail +0.05 · High + Critical",
           "deltas": {"freq_peak_am_tph": 2.0, "rail_trip_share": 0.05},
           "targets": {"weekend_weekday_ratio": 0.80},
           "scope": HIGH_CRIT_TRACTS, "scope_label": f"High + Critical ({len(HIGH_CRIT_TRACTS)})"},
}

# ---------------------------------------------------------------------------
# Hero KPIs
# ---------------------------------------------------------------------------
def compute_kpis():
    r = sim.run(access_deltas={"rail_trip_share": 0.10}, label="kpi_rail")
    pct = (r.tract_df["deficit_delta"] < 0).sum() / sim.n_tracts * 100
    # Mean travel-to-downtown from network analysis
    avg_travel = c2g_network["min_travel_min_to_downtown"].median()
    return {
        "critical": int((df["equity_tier"] == "Critical").sum()),
        "high": int((df["equity_tier"] == "High").sum()),
        "fragile": int(df["flag_fragile"].sum()),
        "rail_pct": round(pct, 1),
        "median_travel_min": round(avg_travel, 0) if not np.isnan(avg_travel) else "n/a",
    }

KPIS = compute_kpis()

# ---------------------------------------------------------------------------
# Maps — high-contrast, proper range, visible borders
# ---------------------------------------------------------------------------
def _choropleth(gdf_src, color_col, color_label, title="", color_range=None):
    vmax = color_range[1] if color_range else max(0.001, gdf_src[color_col].quantile(0.97))
    fig = px.choropleth_mapbox(
        gdf_src,
        geojson=gdf_geojson,
        locations="GEOID",
        featureidkey="properties.GEOID",
        color=color_col,
        color_continuous_scale="YlOrRd",
        range_color=(0, vmax),
        mapbox_style="carto-positron",
        zoom=9, center={"lat": 25.77, "lon": -80.30},
        opacity=0.85,
        labels={color_col: color_label},
    )
    fig.update_traces(marker_line_width=0.4, marker_line_color="white")
    fig.update_layout(
        margin={"r": 0, "t": 30 if title else 0, "l": 0, "b": 0},
        height=540,
        paper_bgcolor="white",
        title=dict(text=title, font=dict(color=UM_GREEN, size=15, family="system-ui")) if title else None,
        font=dict(family="system-ui, -apple-system, sans-serif", color=INK),
        coloraxis_colorbar=dict(
            title=dict(text=color_label, font=dict(color=INK, size=12)),
            tickfont=dict(color=INK, size=11),
            thickness=14, len=0.6,
        ),
    )
    return fig


def overview_map():
    return _choropleth(gdf, "equity_priority_score", "Equity priority")


def before_after_maps(tract_df):
    tdf = tract_df[["tract_geoid", "equity_before", "equity_after"]].copy()
    tdf["tract_geoid"] = tdf["tract_geoid"].astype(str).str.zfill(11)
    m = gdf.merge(
        tdf.rename(columns={"tract_geoid": "GEOID_inner"}),
        left_on="GEOID", right_on="GEOID_inner", how="left",
    )
    vmax = max(m["equity_before"].quantile(0.97), m["equity_after"].quantile(0.97), 0.01)
    return (_choropleth(m, "equity_before", "Equity (baseline)", "Before", (0, vmax)),
            _choropleth(m, "equity_after", "Equity (after scenario)", "After", (0, vmax)))


def tier_bar_chart(before_counts, after_counts):
    fig = go.Figure()
    for t in TIER_ORDER:
        fig.add_trace(go.Bar(name=t, x=["Before", "After"],
                             y=[before_counts.get(t, 0), after_counts.get(t, 0)],
                             marker_color=TIER_COLORS[t]))
    fig.update_layout(
        barmode="stack", height=320, paper_bgcolor="white", plot_bgcolor="white",
        margin={"r": 10, "t": 30, "l": 40, "b": 30},
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis=dict(title="Tracts", gridcolor=BORDER),
        font=dict(family="system-ui", color=INK),
    )
    return fig


def tier_shift_html(shifts_df):
    rows = ['<tr><th>From to</th>' + ''.join(f'<th>{t}</th>' for t in TIER_ORDER) + '</tr>']
    for from_t in TIER_ORDER:
        cells = [f'<td style="background:{OFF_WHITE}"><strong>{from_t}</strong></td>']
        for to_t in TIER_ORDER:
            try:
                v = int(shifts_df.loc[from_t, to_t])
            except Exception:
                v = 0
            if v == 0:
                cells.append(f'<td style="color:{BORDER}">-</td>')
            elif from_t == to_t:
                cells.append(f'<td style="background:{OFF_WHITE}"><strong>{v}</strong></td>')
            elif TIER_ORDER.index(to_t) < TIER_ORDER.index(from_t):
                cells.append(f'<td style="background:{SOFT_GREEN_BG}; color:#1E8449"><strong>{v}</strong></td>')
            else:
                cells.append(f'<td style="background:#FDEDEC; color:#B03A2E">{v}</td>')
        rows.append('<tr>' + ''.join(cells) + '</tr>')
    return '<table class="data-table tier-shift">' + ''.join(rows) + '</table>'


# ---------------------------------------------------------------------------
# Tract narrative
# ---------------------------------------------------------------------------
def _tier_badge(tier):
    c = TIER_COLORS.get(tier, "#495057")
    return f'<span class="tier-badge" style="background:{c}">{tier.upper()}</span>'


def _trend(val, positive_is_bad=True):
    if val is None or (isinstance(val, float) and np.isnan(val)) or val == 0:
        return f'<span style="color:{MUTED}">stable</span>'
    if positive_is_bad:
        return (f'<span style="color:#B03A2E">+{val:.2f} worsening</span>' if val > 0
                else f'<span style="color:#1E8449">{val:.2f} improving</span>')
    return (f'<span style="color:#1E8449">+{val:.2f} improving</span>' if val > 0
            else f'<span style="color:#B03A2E">{val:.2f} worsening</span>')


def _hdy_badge(hdy_min):
    if hdy_min >= 60:
        return f'<span class="hdy-bad">{hdy_min} min</span>'
    if hdy_min >= 30:
        return f'<span class="hdy-warn">{hdy_min} min</span>'
    return f'<span class="hdy-good">{hdy_min} min</span>'


def generate_narrative(tract_input):
    if not tract_input or not str(tract_input).strip():
        return '<em>Enter a census tract GEOID above (11 digits, starting with 12086).</em>'
    try:
        tid = str(int(float(tract_input))).zfill(11)
    except Exception:
        tid = str(tract_input).strip().zfill(11)
    match = df[df["tract_geoid"] == tid]
    if match.empty:
        return f'<em>Tract <code>{tract_input}</code> not found in the Miami-Dade baseline.</em>'
    row = match.iloc[0]
    tier = str(row["equity_tier"])
    fragile = bool(row["flag_fragile"])
    worsening = bool(row.get("flag_worsening", False))

    flag_badges = []
    if fragile:
        flag_badges.append('<span class="flag-badge flag-fragile">FRAGILE — PROJECTED TO WORSEN BY 2027</span>')
    if worsening and not fragile:
        flag_badges.append('<span class="flag-badge flag-worsening">TREND WORSENING</span>')

    header = f'''
<div class="narrative-card" style="border-left-color:{TIER_COLORS.get(tier, MUTED)}">
  <div style="display:flex;align-items:baseline;gap:0.8rem;flex-wrap:wrap">
    <h2 style="margin:0;color:{UM_GREEN}">Tract {tid}</h2>
    {_tier_badge(tier)}
    {''.join(flag_badges)}
  </div>
  <div class="score-row">
    <div class="score-item">
      <div class="score-label">Equity priority</div>
      <div class="score-value">{row["equity_priority_score"]:.3f}</div>
    </div>
    <div class="score-item">
      <div class="score-label">Service deficit</div>
      <div class="score-value">{row["deficit_predicted"]:.3f}</div>
    </div>
    <div class="score-item">
      <div class="score-label">Projected need 2027</div>
      <div class="score-value">{row.get("projected_need_2027", float("nan")):.1f}</div>
    </div>
  </div>
</div>'''

    transit = f'''
<h3 class="section-header">Transit service today</h3>
<table class="data-table">
  <tr><td>Peak AM headway</td><td><strong>{row["headway_peak_am_min"]:.0f} min</strong></td></tr>
  <tr><td>Peak AM frequency</td><td>{row["freq_peak_am_tph"]:.1f} trips/hr</td></tr>
  <tr><td>Early AM frequency</td><td>{row["freq_early_tph"]:.1f} trips/hr</td></tr>
  <tr><td>Weekend / weekday ratio</td><td>{row["weekend_weekday_ratio"]:.2f}</td></tr>
  <tr><td>Rail trip share</td><td>{row["rail_trip_share"]:.3f}</td></tr>
  <tr><td>Neighbor mean equity</td><td>{row["neighbor_mean_equity_score"]:.3f}</td></tr>
</table>'''

    trends = f'''
<h3 class="section-header">Demographic trends (ACS 2019 - 2024)</h3>
<table class="data-table">
  <tr><td>Transit commute share</td><td>{_trend(row.get("trend_commute_public_transit_pct"), False)}</td></tr>
  <tr><td>Drove-alone share</td><td>{_trend(row.get("trend_commute_drove_alone_pct"), True)}</td></tr>
  <tr><td>Work-from-home share</td><td>{_trend(row.get("trend_commute_wfh_pct"), False)}</td></tr>
  <tr><td>Mean commute time</td><td>{_trend(row.get("trend_mean_commute_time_min"), True)}</td></tr>
</table>'''

    # --- Network analysis (real city2graph) ---
    nrow = c2g_network[c2g_network["GEOID"] == tid]
    if len(nrow) > 0 and pd.notna(nrow.iloc[0].get("n_stops_served")):
        nr = nrow.iloc[0]
        rank_total = len(c2g_network)
        closeness_rank = int(nr["mean_closeness_rank"]) if pd.notna(nr.get("mean_closeness_rank")) else None
        travel_rank = int(nr["min_travel_min_to_downtown_rank"]) if pd.notna(nr.get("min_travel_min_to_downtown_rank")) else None
        travel_min = nr["min_travel_min_to_downtown"]
        travel_str = f"{travel_min:.0f} min" if pd.notna(travel_min) else "not reachable"
        pct_iso = nr.get("pct_isolated", 0)
        iso_note = f", {pct_iso:.0f}% of local stops isolated from downtown" if pd.notna(pct_iso) and pct_iso > 0 else ""

        network = f'''
<h3 class="section-header">Network analysis (city2graph on Miami-Dade GTFS)</h3>
<table class="data-table">
  <tr><td>Shortest travel time to downtown</td><td><strong>{travel_str}</strong>{iso_note}</td></tr>
  <tr><td>Stops within 500m (network-covered)</td><td>{int(nr["n_stops_served"])}</td></tr>
  <tr><td>Connectivity rank (closeness centrality)</td><td>#{closeness_rank} of {rank_total}</td></tr>
  <tr><td>Travel-time rank</td><td>#{travel_rank} of {rank_total} (lower = faster to downtown)</td></tr>
</table>'''
    else:
        network = '''
<h3 class="section-header">Network analysis (city2graph)</h3>
<div class="impact-callout">
  <div class="headline">Tract is disconnected from the Miami-Dade transit network</div>
  <div>No stops within 500m have weekday AM service in the GTFS feed.
  Network-wide, this is a walking-access gap.</div>
</div>'''

    # --- Route-level diagnostic ---
    routes_here = c2g_routes[c2g_routes["GEOID"] == tid].sort_values("best_headway_min")
    if len(routes_here) == 0:
        route_section = '''
<div class="impact-callout">
  <div class="headline">No weekday AM-peak bus service within 500m</div>
  <div>Candidates: new shuttle, bus re-routing, on-demand micro-transit.</div>
</div>'''
    else:
        rrows = []
        for _, rr in routes_here.iterrows():
            hdy = int(round(rr["best_headway_min"]))
            rrows.append(
                f'<tr><td><strong>{rr["route_short_name"]}</strong></td>'
                f'<td>{str(rr.get("route_long_name",""))[:55]}</td>'
                f'<td>{_hdy_badge(hdy)}</td>'
                f'<td>{int(rr["n_stops"])}</td>'
                f'<td>{int(rr["total_trips"])}</td></tr>'
            )
        worst = routes_here.iloc[-1]
        best = routes_here.iloc[0]
        if worst["best_headway_min"] >= 60:
            callout = f'''
<div class="impact-callout">
  <div class="headline">Bottleneck identified</div>
  <div>Route <strong>{worst["route_short_name"]}</strong>
  ({str(worst.get("route_long_name",""))[:55]}) runs every
  <strong>{int(round(worst["best_headway_min"]))} minutes</strong> at AM peak.
  Priority lever: increase peak AM frequency on this route.</div>
</div>'''
        else:
            callout = f'''
<div class="impact-callout" style="background:linear-gradient(135deg,{SOFT_GREEN_BG} 0%, white 80%); border-left-color:#1E8449">
  <div class="headline" style="color:#1E8449">Adequate service</div>
  <div>Best route <strong>{best["route_short_name"]}</strong> runs every
  {int(round(best["best_headway_min"]))} min. The gap is driven by demographic need,
  not service frequency.</div>
</div>'''
        route_section = f'''
<h3 class="section-header">Route-level diagnostic (GTFS · weekday AM peak · stops within 500m)</h3>
<table class="data-table routes-table">
  <thead><tr><th>Route</th><th>Long name</th><th>Headway</th><th>Stops</th><th>Trips</th></tr></thead>
  <tbody>{''.join(rrows)}</tbody>
</table>
{callout}'''

    return header + transit + trends + network + route_section


# ---------------------------------------------------------------------------
# Scenario output formatter
# ---------------------------------------------------------------------------
def format_scenario_output(result, name, description, scope_label):
    s = result.summary
    tdf = result.tract_df
    before_counts = tdf["tier_before"].value_counts().to_dict()
    after_counts = tdf["tier_after"].value_counts().to_dict()

    crit_delta = before_counts.get("Critical", 0) - after_counts.get("Critical", 0)
    if crit_delta > 0:
        headline = f'<strong>{crit_delta}</strong> tract{"s" if crit_delta != 1 else ""} moved <strong>out of Critical</strong>'
    elif s["n_tier_upgrades"] > 0:
        headline = f'<strong>{s["n_tier_upgrades"]}</strong> tier upgrades across the county'
    else:
        headline = f'<strong>{s["n_improved"]}</strong> tracts improved'

    summary = f'''
<div class="impact-callout">
  <div class="headline">{name}</div>
  <div style="margin-top:0.3rem;color:{MUTED}">{description} · Scope: {scope_label}</div>
  <div style="margin-top:0.8rem;font-size:1.15rem;color:{INK}">{headline}</div>
</div>
<div class="kpi-row">
  <div class="kpi-card">
    <div class="label">Tracts improved</div>
    <div class="value" style="color:#1E8449">{s["n_improved"]}</div>
    <div class="detail">of {s["n_tracts"]} total</div>
  </div>
  <div class="kpi-card">
    <div class="label">Tier upgrades</div>
    <div class="value" style="color:{UM_GREEN}">{s["n_tier_upgrades"]}</div>
    <div class="detail">moved to better tier</div>
  </div>
  <div class="kpi-card">
    <div class="label">Avg deficit change</div>
    <div class="value" style="color:{UM_ORANGE}">{s["avg_deficit_delta"]:+.4f}</div>
    <div class="detail">negative = better</div>
  </div>
  <div class="kpi-card">
    <div class="label">Worsened</div>
    <div class="value" style="color:#B03A2E">{s["n_worsened"]}</div>
    <div class="detail">flag for review</div>
  </div>
</div>'''

    before, after = before_after_maps(tdf)
    bars = tier_bar_chart(before_counts, after_counts)
    shift = tier_shift_html(result.tier_shifts)
    return summary, before, after, bars, shift


def run_preset(key):
    p = PRESETS[key]
    r = run_scenario(deltas=p["deltas"], targets=p["targets"],
                     tract_filter=p["scope"], label=p["label"])
    return format_scenario_output(r, p["label"], p["desc"], p["scope_label"])


def run_manual(freq_peak, freq_early, weekend, rail, scope_label, custom_geoids):
    if custom_geoids and custom_geoids.strip():
        try:
            scope = [int(g.strip()) for g in custom_geoids.split(",") if g.strip()]
            scope_str = f"Custom ({len(scope)} tracts)"
        except Exception:
            empty = go.Figure()
            return ('<div class="impact-callout"><div class="headline" style="color:#B03A2E">Invalid GEOID list</div><div>Use comma-separated 11-digit GEOIDs.</div></div>',
                    empty, empty, empty, "")
    else:
        scope_map = {"All 504 tracts": "all", "Critical only": CRITICAL_TRACTS,
                     "High + Critical": HIGH_CRIT_TRACTS, "Fragile only": FRAGILE_TRACTS}
        scope = scope_map.get(scope_label, "all")
        scope_str = scope_label

    deltas = {k: float(v) for k, v in {
        "freq_peak_am_tph": freq_peak, "freq_early_tph": freq_early,
        "weekend_weekday_ratio": weekend, "rail_trip_share": rail,
    }.items() if v != 0}

    if not deltas:
        empty = go.Figure()
        return ('<div class="impact-callout"><div class="headline">No changes applied</div><div>Move at least one slider, or pick a preset above.</div></div>',
                empty, empty, empty, "")

    r = run_scenario(deltas=deltas, tract_filter=scope, label="custom")
    desc = " · ".join(f"{k.replace('_',' ')}{v:+g}" for k, v in deltas.items())
    return format_scenario_output(r, "Custom scenario", desc, scope_str)


# ---------------------------------------------------------------------------
# Priority Routes tab
# ---------------------------------------------------------------------------
def priority_routes_table():
    top = c2g_problems.head(15).copy()
    top.insert(0, "Rank", range(1, len(top) + 1))
    top = top[["Rank", "route_short_name", "route_long_name",
               "n_critical_high_tracts", "worst_headway_min",
               "median_headway_min", "problem_score"]]
    top.columns = ["Rank", "Route", "Long name", "Crit + High tracts",
                   "Worst headway (min)", "Median headway (min)", "Problem score"]
    return top.round(1)


def priority_routes_summary_html():
    top5 = c2g_problems.head(5)
    n_tracts = int(top5["n_critical_high_tracts"].sum())
    worst = c2g_problems.iloc[0]
    return f'''
<div class="impact-callout">
  <div class="headline">Where to invest first</div>
  <div>The top-5 problem routes (below) together touch
  <strong>{n_tracts} Critical + High tracts</strong>. Investing in these
  captures the largest share of vulnerable populations per service hour added.</div>
</div>
<p>Route <strong>{worst["route_short_name"]}</strong>
(<em>{worst["route_long_name"]}</em>) is the #1 priority: reaches
{int(worst["n_critical_high_tracts"])} Critical + High tracts with a worst
AM-peak headway of {int(worst["worst_headway_min"])} minutes.</p>'''


# ---------------------------------------------------------------------------
# Network Analysis tab
# ---------------------------------------------------------------------------
def network_summary_html():
    covered = int(c2g_network["n_stops_served"].notna().sum())
    total = len(c2g_network)
    median_travel = c2g_network["min_travel_min_to_downtown"].median()
    worst_quartile = c2g_network["min_travel_min_to_downtown"].quantile(0.75)
    return f'''
<div class="impact-callout">
  <div class="headline">Network connectivity (NetworkX graph, Miami-Dade GTFS)</div>
  <div>Built with <strong>city2graph</strong>: 6,954 stops as nodes, 7,785
  service edges weighted by travel time, all from the real GTFS feed
  (weekday 06:00-09:00). {covered}/{total} tracts have at least one
  network-covered stop within 500m.</div>
</div>
<div class="kpi-row">
  <div class="kpi-card action">
    <div class="label">Median travel to downtown</div>
    <div class="value">{median_travel:.0f} min</div>
    <div class="detail">across all 504 tracts</div>
  </div>
  <div class="kpi-card high">
    <div class="label">Worst 25 pct of tracts</div>
    <div class="value">{worst_quartile:.0f}+ min</div>
    <div class="detail">to reach downtown</div>
  </div>
  <div class="kpi-card fragile">
    <div class="label">Unreachable tracts</div>
    <div class="value">{int((c2g_network["n_stops_served"].isna()).sum())}</div>
    <div class="detail">no GTFS service within 500m</div>
  </div>
  <div class="kpi-card critical">
    <div class="label">Stops isolated</div>
    <div class="value">182</div>
    <div class="detail">cannot reach downtown on the network</div>
  </div>
</div>'''


def network_table():
    crit_geoids = set(CRITICAL_TRACTS)
    t = c2g_network.copy()
    t = t[t["n_stops_served"].notna()]
    t = t.sort_values("min_travel_min_to_downtown", ascending=False)
    t = t.head(20)
    t["equity_tier"] = t["GEOID"].map(df.set_index("tract_geoid")["equity_tier"])
    t = t[["GEOID", "equity_tier", "n_stops_served",
           "min_travel_min_to_downtown", "mean_closeness_rank",
           "pct_isolated"]].copy()
    t.columns = ["GEOID", "Tier", "Stops within 500m",
                 "Travel to downtown (min)", "Connectivity rank",
                 "Pct isolated stops"]
    return t.round(1)


# ---------------------------------------------------------------------------
# Build network-overlay map for Network Analysis tab
# ---------------------------------------------------------------------------
def network_map():
    m = gdf.merge(
        c2g_network[["GEOID", "min_travel_min_to_downtown"]],
        on="GEOID", how="left",
    )
    # Replace missing with a high value for display (they'll stand out)
    m["min_travel_min_to_downtown"] = m["min_travel_min_to_downtown"].fillna(90)
    vmax = m["min_travel_min_to_downtown"].quantile(0.95)
    fig = px.choropleth_mapbox(
        m, geojson=gdf_geojson, locations="GEOID",
        featureidkey="properties.GEOID",
        color="min_travel_min_to_downtown",
        color_continuous_scale="Reds",
        range_color=(10, vmax),
        mapbox_style="carto-positron",
        zoom=9, center={"lat": 25.77, "lon": -80.30},
        opacity=0.85,
        labels={"min_travel_min_to_downtown": "Travel min"},
    )
    fig.update_traces(marker_line_width=0.4, marker_line_color="white")
    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        height=520, paper_bgcolor="white",
        font=dict(family="system-ui", color=INK),
        coloraxis_colorbar=dict(
            title=dict(text="Minutes to downtown", font=dict(color=INK, size=12)),
            tickfont=dict(color=INK, size=11),
            thickness=14, len=0.6,
        ),
    )
    return fig


# ---------------------------------------------------------------------------
# CSS + Hero
# ---------------------------------------------------------------------------
CUSTOM_CSS = f"""
.gradio-container {{
  font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
  max-width: 1400px !important;
  background: white !important;
}}
body {{ background: white !important; color: {INK} !important }}
.prose, .markdown, p, li {{ color: {INK} !important }}

.hero {{
  background: linear-gradient(135deg, {SOFT_ORANGE_BG} 0%, white 60%);
  padding: 1.8rem 2rem;
  border-radius: 12px;
  border-left: 6px solid {UM_ORANGE};
  margin-bottom: 1.2rem;
}}
.hero .brand {{
  color: {UM_GREEN}; font-weight: 700; font-size: 0.85rem;
  letter-spacing: 1px; text-transform: uppercase;
}}
.hero h1 {{
  color: {UM_ORANGE}; font-weight: 800; margin: 0.4rem 0 0.5rem 0;
  font-size: 2.1rem; letter-spacing: -0.01em;
}}
.hero .tagline {{ color: {INK}; font-size: 1.05rem; max-width: 860px; line-height: 1.55 }}

.kpi-row {{ display: flex; gap: 1rem; margin: 0.8rem 0 1.2rem 0; flex-wrap: wrap }}
.kpi-card {{
  background: white; border: 1px solid {BORDER}; border-radius: 10px;
  padding: 1.1rem 1.2rem; flex: 1 1 200px; min-width: 180px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  transition: transform 0.15s, box-shadow 0.15s;
}}
.kpi-card:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.08) }}
.kpi-card .label {{
  color: {MUTED}; font-size: 0.78rem; text-transform: uppercase;
  letter-spacing: 0.5px; font-weight: 700;
}}
.kpi-card .value {{
  color: {UM_GREEN}; font-size: 2.15rem; font-weight: 800;
  line-height: 1.1; margin: 0.4rem 0 0.2rem 0;
}}
.kpi-card .detail {{ color: {MUTED}; font-size: 0.85rem }}
.kpi-card.critical {{ border-left: 4px solid #B03A2E }}
.kpi-card.critical .value {{ color: #B03A2E }}
.kpi-card.high {{ border-left: 4px solid #CA6F1E }}
.kpi-card.high .value {{ color: #CA6F1E }}
.kpi-card.fragile {{ border-left: 4px solid #6A1B9A }}
.kpi-card.fragile .value {{ color: #6A1B9A }}
.kpi-card.action {{ border-left: 4px solid {UM_ORANGE} }}
.kpi-card.action .value {{ color: {UM_ORANGE} }}

.section-header {{
  color: {UM_GREEN}; font-weight: 700; font-size: 1.05rem;
  border-bottom: 2px solid {UM_ORANGE};
  padding: 0.3rem 0; margin: 1.2rem 0 0.6rem 0;
}}

.tier-badge {{
  display: inline-block; padding: 0.25rem 0.8rem;
  border-radius: 20px; font-weight: 700; font-size: 0.8rem;
  color: white; letter-spacing: 0.8px;
}}
.flag-badge {{
  display: inline-block; padding: 0.2rem 0.6rem;
  border-radius: 4px; font-size: 0.72rem; font-weight: 700;
  letter-spacing: 0.5px;
}}
.flag-fragile {{ background: #FDEDEC; color: #B03A2E; border: 1px solid #F5B7B1 }}
.flag-worsening {{ background: #FEF5E7; color: #9A6200; border: 1px solid #F8D49E }}

.narrative-card {{
  background: white; border: 1px solid {BORDER};
  border-left: 6px solid {TIER_COLORS["Moderate"]};
  border-radius: 10px; padding: 1.2rem 1.4rem; margin-bottom: 1rem;
}}
.score-row {{ display: flex; gap: 2rem; margin-top: 1rem; flex-wrap: wrap }}
.score-item .score-label {{
  color: {MUTED}; font-size: 0.72rem;
  text-transform: uppercase; letter-spacing: 0.5px;
}}
.score-item .score-value {{ color: {UM_GREEN}; font-size: 1.5rem; font-weight: 700 }}

.data-table {{ width: 100%; border-collapse: collapse; margin: 0.5rem 0 1rem 0; font-size: 0.92rem; color: {INK} }}
.data-table td, .data-table th {{ padding: 0.5rem 0.8rem; border-bottom: 1px solid {BORDER}; text-align: left; color: {INK} }}
.data-table th {{
  background: {OFF_WHITE}; color: {UM_GREEN};
  font-weight: 700; text-transform: uppercase; font-size: 0.72rem; letter-spacing: 0.5px;
}}
.data-table.routes-table td:first-child {{ font-weight: 700; color: {UM_GREEN} }}
.data-table.tier-shift td {{ text-align: center }}
.hdy-bad {{ color: #B03A2E; font-weight: 700 }}
.hdy-warn {{ color: #CA6F1E; font-weight: 700 }}
.hdy-good {{ color: #1E8449; font-weight: 700 }}

.impact-callout {{
  background: linear-gradient(135deg, {SOFT_ORANGE_BG} 0%, white 80%);
  border-left: 5px solid {UM_ORANGE};
  padding: 1rem 1.3rem; border-radius: 8px; margin: 1rem 0;
}}
.impact-callout .headline {{
  color: {UM_ORANGE}; font-size: 1.1rem; font-weight: 700; margin-bottom: 0.2rem;
  letter-spacing: 0.2px;
}}

button.preset-btn {{
  min-height: 90px !important; background: white !important;
  color: {UM_GREEN} !important; border: 1.5px solid {BORDER} !important;
  border-radius: 10px !important; font-weight: 600 !important;
  text-align: left !important; white-space: normal !important;
  padding: 0.9rem 1.1rem !important; transition: all 0.15s !important;
  line-height: 1.4 !important; font-size: 0.93rem !important;
}}
button.preset-btn:hover {{
  border-color: {UM_ORANGE} !important;
  background: {SOFT_ORANGE_BG} !important;
  box-shadow: 0 2px 10px rgba(244,115,33,0.18) !important;
  transform: translateY(-1px);
}}

button.primary-cta {{
  background: {UM_ORANGE} !important; color: white !important;
  border: none !important; font-weight: 700 !important;
  box-shadow: 0 2px 8px rgba(244,115,33,0.25) !important;
  letter-spacing: 0.3px;
}}
button.primary-cta:hover {{ background: {UM_ORANGE_DARK} !important }}

footer {{ display: none !important }}

button[role="tab"] {{ font-weight: 700 !important; color: {MUTED} !important; font-size: 0.95rem !important }}
button[role="tab"][aria-selected="true"] {{
  color: {UM_ORANGE} !important;
  border-bottom: 3px solid {UM_ORANGE} !important;
}}
"""

HERO_HTML = f'''
<div class="hero">
  <div class="brand">University of Miami MSBA · Deloitte · Miami-Dade County</div>
  <h1>Miami-Dade Transit Equity Simulator</h1>
  <div class="tagline">
    One engine. 504 census tracts. 4 policy levers. Quantify which transit
    investments move the most people out of service-gap crisis — and identify
    the exact routes and network gaps driving the need.
  </div>
</div>
<div class="kpi-row">
  <div class="kpi-card critical">
    <div class="label">Critical service gap</div>
    <div class="value">{KPIS["critical"]}</div>
    <div class="detail">tracts in severe gap</div>
  </div>
  <div class="kpi-card high">
    <div class="label">High-risk</div>
    <div class="value">{KPIS["high"]}</div>
    <div class="detail">tracts with significant gap</div>
  </div>
  <div class="kpi-card fragile">
    <div class="label">Fragile by 2027</div>
    <div class="value">{KPIS["fragile"]}</div>
    <div class="detail">projected to worsen</div>
  </div>
  <div class="kpi-card action">
    <div class="label">Rail expansion impact</div>
    <div class="value">{KPIS["rail_pct"]}%</div>
    <div class="detail">of tracts improve</div>
  </div>
</div>'''


THEME = gr.themes.Soft(
    primary_hue=gr.themes.colors.orange,
    secondary_hue=gr.themes.colors.green,
    neutral_hue=gr.themes.colors.gray,
).set(
    body_background_fill="white",
    background_fill_primary="white",
    background_fill_secondary=OFF_WHITE,
    block_background_fill="white",
    block_border_width="1px",
    body_text_color=INK,
)

# ---------------------------------------------------------------------------
# Build Gradio app
# ---------------------------------------------------------------------------
with gr.Blocks(title="Miami-Dade Transit Equity Simulator", theme=THEME, css=CUSTOM_CSS) as demo:
    gr.HTML(HERO_HTML)

    with gr.Tabs():
        # ── The Problem ────────────────────────────────────────────────────
        with gr.Tab("The Problem"):
            gr.HTML(f'''
<div class="impact-callout">
  <div class="headline">What are we looking at</div>
  <div>Each tract is scored on an <strong>equity priority index</strong>
  combining demographic need (poverty, car-free households, unemployment
  trends) with service deficit (peak frequency, weekend coverage, rail
  access). The {KPIS["critical"]} Critical tracts below are where transit
  gaps meet the highest dependency — these are the places a policy dollar
  buys the most equity.</div>
</div>''')
            gr.Plot(value=overview_map(), show_label=False, container=False)
            with gr.Row():
                gr.Markdown(f'''
### Tier distribution
- **Critical:** {KPIS["critical"]} tracts — immediate priority
- **High:** {KPIS["high"]} tracts — significant gap
- **Moderate:** {(df["equity_tier"]=="Moderate").sum()} tracts
- **Low:** {(df["equity_tier"]=="Low").sum()} tracts
- **Fragile:** {KPIS["fragile"]} tracts projected to worsen by 2027
''')
                gr.Markdown('''
### What drives Critical status
Per our XGBoost v3 model (CV R²=0.823), the top drivers are:
1. **Peak AM frequency** (SHAP 39.6%) — fastest single lever
2. **Weekend / weekday ratio** (SHAP 21.7%)
3. **Early AM frequency** (SHAP 6.9%)
4. **Rail modal share** — largest *county-wide* impact per lever

Head to **Simulate Policy** to test interventions.
''')

        # ── Tract Explorer ─────────────────────────────────────────────────
        with gr.Tab("Tract Explorer"):
            gr.Markdown('''
Pick a tract to see the full story: demographics, service levels, network
connectivity, and the specific bus routes serving it. The app flags the
route that is the bottleneck, so you know which line to invest in.
''')
            with gr.Row():
                tract_input = gr.Textbox(label="Census tract GEOID",
                                         placeholder="e.g. 12086000220", scale=3)
                tract_btn = gr.Button("Generate narrative",
                                      elem_classes=["primary-cta"], scale=1)
            gr.Markdown("**Try these Critical tracts with a 90-minute-headway route:** `12086000220`, `12086000307`")
            narrative_output = gr.HTML(value='<em>Enter a tract ID above and click Generate narrative.</em>')
            tract_btn.click(fn=generate_narrative, inputs=tract_input, outputs=narrative_output)
            tract_input.submit(fn=generate_narrative, inputs=tract_input, outputs=narrative_output)

        # ── Simulate Policy ────────────────────────────────────────────────
        with gr.Tab("Simulate Policy"):
            gr.Markdown("### Five reference policies · click to run")

            preset_buttons = {}
            with gr.Row():
                for key in ["S1", "S2", "S3"]:
                    p = PRESETS[key]
                    preset_buttons[key] = gr.Button(
                        f"{p['label']}\n{p['desc']}",
                        elem_classes=["preset-btn"])
            with gr.Row():
                for key in ["S4", "S5"]:
                    p = PRESETS[key]
                    preset_buttons[key] = gr.Button(
                        f"{p['label']}\n{p['desc']}",
                        elem_classes=["preset-btn"])
                gr.Markdown("")

            with gr.Accordion("Advanced · custom sliders", open=False):
                gr.Markdown("Each slider is a **delta from baseline**. Mix and match.")
                with gr.Row():
                    with gr.Column():
                        s_freq_peak = gr.Slider(-10, 10, value=0, step=0.5,
                                                label="Delta peak AM frequency (trips/hr) · SHAP #1")
                        s_weekend = gr.Slider(-0.5, 0.5, value=0, step=0.05,
                                              label="Delta weekend / weekday ratio · SHAP #2")
                        s_freq_early = gr.Slider(-5, 5, value=0, step=0.5,
                                                 label="Delta early AM frequency (trips/hr) · SHAP #3")
                        s_rail = gr.Slider(-0.1, 0.3, value=0, step=0.01,
                                           label="Delta rail trip share")
                    with gr.Column():
                        s_scope = gr.Radio(
                            choices=["All 504 tracts", "Critical only", "High + Critical", "Fragile only"],
                            value="All 504 tracts", label="Apply to")
                        s_custom = gr.Textbox(label="Custom GEOID list (overrides scope)",
                                              placeholder="12086000220, 12086000307", lines=2)
                run_custom_btn = gr.Button("Run custom scenario",
                                           elem_classes=["primary-cta"])

            gr.Markdown("---")
            scenario_summary = gr.HTML(value='<em>Pick a preset above, or open Advanced for custom sliders.</em>')
            with gr.Row():
                map_before = gr.Plot(label="Before", container=False)
                map_after = gr.Plot(label="After", container=False)
            with gr.Row():
                tier_bars = gr.Plot(label="Tier distribution", container=False)
                tier_shift_out = gr.HTML(value="")

            out_list = [scenario_summary, map_before, map_after, tier_bars, tier_shift_out]

            for key, btn in preset_buttons.items():
                btn.click(fn=lambda k=key: run_preset(k), inputs=None, outputs=out_list)

            run_custom_btn.click(
                fn=run_manual,
                inputs=[s_freq_peak, s_freq_early, s_weekend, s_rail, s_scope, s_custom],
                outputs=out_list,
            )

        # ── Priority Routes ────────────────────────────────────────────────
        with gr.Tab("Priority Routes"):
            gr.HTML(priority_routes_summary_html())
            gr.Markdown("### Top 15 problem routes — ranked by impact on Critical + High tracts")
            gr.Markdown('''
*Problem score = number of Critical + High tracts served × worst AM-peak
headway. A higher score means the route serves many vulnerable tracts
**and** runs infrequently — strong candidate for investment.*
''')
            gr.Dataframe(value=priority_routes_table(), interactive=False, wrap=True)

        # ── Network Analysis (city2graph) ──────────────────────────────────
        with gr.Tab("Network Analysis"):
            gr.HTML(network_summary_html())
            gr.Markdown("### Travel-time to downtown from each tract (NetworkX shortest path)")
            gr.Plot(value=network_map(), show_label=False, container=False)
            gr.Markdown("### 20 tracts with longest travel time to downtown")
            gr.Dataframe(value=network_table(), interactive=False, wrap=True)

        # ── About ──────────────────────────────────────────────────────────
        with gr.Tab("About"):
            gr.Markdown('''
## Methodology

**Baseline.** 504 Miami-Dade census tracts × 29 columns joining:
- ACS 2019–2024 demographics (poverty, car-free households, commute trends)
- Sprint 2a equity composites (need × service deficit)
- Sprint 2b deficit predictions (XGBoost v3, CV R²=0.823)
- ACS time-series projections to 2027

**Simulator engine.** User adjusts 4 service levers → simulator re-predicts
deficit via XGBoost v3 → `ratio = new_deficit / baseline_deficit` → applied
to Sprint 2a composite → updated equity score + tier reassignment.

**Proportional-change math.** We don't use raw model predictions directly
(different scale than Sprint 2a). We use the *ratio of change*, which gives
99.6% tier recovery at zero delta (vs 57% with naive multiplication).

**Route-level diagnostic.** Miami-Dade GTFS (2026-03-24, 123 routes, 6,954
stops, 972K stop-events). Per (route, stop) AM-peak headway derived from
06:00–09:00 weekday service. Stops spatial-joined to tracts with a 500m
walking buffer. Rankings surface routes that are both (a) low-frequency
**and** (b) serving many Critical + High tracts.

**Network analysis.** Built with `city2graph` + NetworkX:
- 6,954 stops as nodes, 7,785 service edges
- Edges weighted by `travel_time_sec` and filtered to weekday AM
- Per-stop degree centrality, closeness, betweenness
- Shortest-path travel time to Downtown Government Center anchor
- Aggregated to tract level with 500m walking buffer

## Credits

- **Luna Sage** — Sprint 3.1 baseline + Sprint 3.2 simulator engine
- **Lina Graf** — Gradio V2/V3 dashboard prototypes
- **Daniel Regalado Cardoso** — Sprint 1/2 modeling, Sprint 3.3 validation, city2graph integration, production UI
- **Partners:** University of Miami MSBA · Deloitte · Miami-Dade Transit

## Data sources

- [Miami-Dade Transit GTFS](https://www.miamidade.gov/transit/) feed 2026-03-24
- [US Census TIGERweb](https://tigerweb.geo.census.gov/) for tract geometries
- [American Community Survey](https://www.census.gov/programs-surveys/acs) 2019–2024
- [city2graph](https://pypi.org/project/city2graph/) for NetworkX graph construction

*Simulator code, validation notebook, and this app are open-source in the
[project repo](https://github.com/DanielRegaladoUMiami/CapstoneProject-AI-for-Equitable-Transportation).*
''')


if __name__ == "__main__":
    demo.queue(default_concurrency_limit=4).launch()
