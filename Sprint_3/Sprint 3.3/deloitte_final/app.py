"""
Miami-Dade Transit Equity Simulator — Deloitte Final.

Directly answers the three business questions from the Deloitte problem
statement that the earlier version only covered structurally:

  1. "Measurable reduction in travel times" → Wait-time saved per trip,
     deterministic from headway math.

  2. "Increased transit usage among underserved populations" → Ridership
     change via APTA/TCRP service elasticity (0.65 frequency, 0.4 weekend,
     1.2 rail). Reported per-tract and county-wide.

  3. "Alerts & recommendations" → Per-tract top-3 actionable interventions
     with expected impact, plus a county-wide intervention ranker.

Also: precomputes the 5 reference policies at startup so the Simulate
Policy tab responds in <1s instead of 15-60s on cpu-basic HF.

Built on:
  • Luna's Sprint 3.2 simulator (XGBoost v3 proportional-change engine)
  • Daniel's Sprint 2b model (CV R²=0.823)
  • city2graph NetworkX analysis over real Miami-Dade GTFS
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
sys.path.insert(0, str(HERE))

# ---------------------------------------------------------------------------
# Brand — University of Miami
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
    "Critical": "#C0392B",  # vivid red
    "High":     "#E67E22",  # vivid orange
    "Moderate": "#F1C40F",  # amber
    "Low":      "#2ECC71",  # green
}

# Urban Miami-Dade bounding box (tight crop on densely populated corridor,
# excluding giant unincorporated western tracts that are Moderate-tier by
# score but cover huge rural area and visually swamp the frame).
URBAN_LON = [-80.40, -80.10]
URBAN_LAT = [25.43, 25.95]
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

from extended_metrics import (
    wait_time_saved_min,
    ridership_change_pct,
    extended_summary,
    FREQUENCY_ELASTICITY,
    WEEKEND_WEEKDAY_ELASTICITY,
    RAIL_SUBSTITUTION_FACTOR,
)
from recommendations import recommend_for_tract, recommend_countywide_top_levers

c2g_routes = pd.read_csv(HERE / "City2Graph_Tract_Routes.csv", dtype={"GEOID": str})
c2g_problems = pd.read_csv(HERE / "City2Graph_Problem_Routes.csv")
c2g_network = pd.read_csv(HERE / "City2Graph_Network_Metrics.csv", dtype={"GEOID": str})

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

# Simplify geometries to speed up plotly (reduces JSON payload ~40%)
gdf_all["geometry"] = gdf_all["geometry"].simplify(0.0005, preserve_topology=True)
gdf = gdf_all.merge(df, left_on="GEOID", right_on="tract_geoid", how="inner")
gdf_geojson = json.loads(gdf.to_json())

print(f"  {len(df)} tracts loaded")

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
    result = sim._build_result(deficit, equity, tier_base, tier, label)
    # Attach scenario features for extended metrics
    result._scenario_features = features
    return result


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
# KPIs
# ---------------------------------------------------------------------------
def compute_kpis():
    r = sim.run(access_deltas={"rail_trip_share": 0.10}, label="kpi_rail")
    pct = (r.tract_df["deficit_delta"] < 0).sum() / sim.n_tracts * 100
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
# Maps
# ---------------------------------------------------------------------------
def _choropleth(gdf_src, color_col, color_label, title="", color_range=None, scale="YlOrRd"):
    """SVG-based choropleth (no Mapbox, no WebGL, no tile fetch)."""
    vmax = color_range[1] if color_range else max(0.001, gdf_src[color_col].quantile(0.97))
    fig = px.choropleth(
        gdf_src, geojson=gdf_geojson, locations="GEOID",
        featureidkey="properties.GEOID",
        color=color_col, color_continuous_scale=scale,
        range_color=(color_range[0] if color_range else 0, vmax),
        labels={color_col: color_label},
    )
    fig.update_geos(
        fitbounds="locations",
        visible=False,
        showframe=False,
        projection_type="mercator",
        bgcolor="#FFFFFF",
    )
    fig.update_traces(marker_line_width=0.4, marker_line_color="#FFFFFF")
    fig.update_layout(
        margin={"r": 0, "t": 30 if title else 0, "l": 0, "b": 0},
        height=580, paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
        title=dict(text=title, font=dict(color="#1D1D1F", size=14,
                   family="-apple-system, SF Pro Display, sans-serif")) if title else None,
        font=dict(family="-apple-system, SF Pro Text, sans-serif", color="#1D1D1F", size=12),
        coloraxis_colorbar=dict(
            title=dict(text=color_label, font=dict(color="#1D1D1F", size=11)),
            tickfont=dict(color="#1D1D1F", size=11),
            thickness=10, len=0.5, outlinewidth=0, bgcolor="rgba(0,0,0,0)",
        ),
    )
    return fig


import plotly.io as _pio


def fig_to_iframe(fig, height=580):
    """Convert a Plotly figure to an iframe-embedded HTML string.
    Gradio's gr.HTML strips <script> tags, so we use iframe srcdoc
    which preserves the Plotly JS execution context."""
    html = _pio.to_html(fig, full_html=True, include_plotlyjs="cdn",
                         config={"displayModeBar": False})
    escaped = html.replace('"', '&quot;')
    return (f'<iframe srcdoc="{escaped}" '
            f'style="width:100%;height:{height}px;border:0;"></iframe>')


def overview_map():
    """Mapbox choropleth with carto-positron basemap, rendered via iframe."""
    fig = px.choropleth_mapbox(
        gdf, geojson=gdf_geojson, locations="GEOID",
        featureidkey="properties.GEOID",
        color="equity_tier",
        color_discrete_map=TIER_COLORS,
        category_orders={"equity_tier": ["Critical", "High", "Moderate", "Low"]},
        mapbox_style="carto-positron",
        zoom=9, center={"lat": 25.77, "lon": -80.25},
        opacity=0.75,
        hover_data={"equity_priority_score": ":.3f", "equity_tier": True},
    )
    fig.update_traces(marker_line_width=0.5, marker_line_color="#FFFFFF")
    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        height=580, paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
        font=dict(family="-apple-system, SF Pro Text, sans-serif", color="#1D1D1F", size=12),
        legend=dict(
            title=dict(text="Equity tier", font=dict(color="#1D1D1F", size=12)),
            font=dict(color="#1D1D1F", size=12),
            orientation="h", yanchor="top", y=-0.02, xanchor="left", x=0,
            bgcolor="rgba(255,255,255,0.85)", bordercolor="#D2D2D7", borderwidth=1,
        ),
    )
    return fig


def before_after_maps(tract_df):
    """
    Tier-discrete before/after maps. Each tract gets one of four clear
    colors so tier changes pop against the basemap.
    """
    tdf = tract_df[["tract_geoid", "tier_before", "tier_after"]].copy()
    tdf["tract_geoid"] = tdf["tract_geoid"].astype(str).str.zfill(11)
    m = gdf.merge(
        tdf.rename(columns={"tract_geoid": "GEOID_inner"}),
        left_on="GEOID", right_on="GEOID_inner", how="left",
    )
    m["tier_before"] = m["tier_before"].fillna(m["equity_tier"])
    m["tier_after"] = m["tier_after"].fillna(m["equity_tier"])

    def tier_choropleth(col, title):
        fig = px.choropleth_mapbox(
            m, geojson=gdf_geojson, locations="GEOID",
            featureidkey="properties.GEOID", color=col,
            color_discrete_map=TIER_COLORS,
            category_orders={col: ["Critical", "High", "Moderate", "Low"]},
            mapbox_style="carto-positron",
            zoom=9, center={"lat": 25.77, "lon": -80.25},
            opacity=0.75,
        )
        fig.update_traces(marker_line_width=0.4, marker_line_color="#FFFFFF")
        fig.update_layout(
            margin={"r": 0, "t": 30, "l": 0, "b": 0},
            height=420, paper_bgcolor="#FFFFFF",
            title=dict(text=title, font=dict(color="#1D1D1F", size=14,
                       family="-apple-system, SF Pro Display, sans-serif"), x=0.02),
            font=dict(family="-apple-system, SF Pro Text, sans-serif", color="#1D1D1F", size=11),
            legend=dict(
                title=dict(text="Tier", font=dict(color="#1D1D1F", size=11)),
                font=dict(color="#1D1D1F", size=10),
                orientation="h", yanchor="top", y=-0.02,
                xanchor="left", x=0,
                bgcolor="rgba(255,255,255,0.85)",
                bordercolor="#D2D2D7", borderwidth=1,
            ),
        )
        return fig_to_iframe(fig, 420)

    return tier_choropleth("tier_before", "Before"), tier_choropleth("tier_after", "After")


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
# Format scenario output (now with extended metrics)
# ---------------------------------------------------------------------------
def format_scenario_output(result, name, description, scope_label):
    s = result.summary
    tdf = result.tract_df
    before_counts = tdf["tier_before"].value_counts().to_dict()
    after_counts = tdf["tier_after"].value_counts().to_dict()

    # Extended metrics
    ext = extended_summary(
        result,
        sim._features_base,
        getattr(result, "_scenario_features", sim._features_base),
    )

    crit_delta = before_counts.get("Critical", 0) - after_counts.get("Critical", 0)
    if crit_delta > 0:
        headline = f'<strong>{crit_delta}</strong> tract{"s" if crit_delta != 1 else ""} moved <strong>out of Critical</strong>'
    elif s["n_tier_upgrades"] > 0:
        headline = f'<strong>{s["n_tier_upgrades"]}</strong> tier upgrades across the county'
    else:
        headline = f'<strong>{s["n_improved"]}</strong> tracts improved'

    # Business-impact lines (new)
    wait_line = ""
    ride_line = ""
    if ext["avg_wait_saved_min"] > 0.02:
        wait_line = f'<div style="margin-top:0.6rem">Average wait-time saved per trip: <strong>{ext["avg_wait_saved_min"]:.1f} min</strong> (peak in best tract: {ext["max_wait_saved_min"]:.1f} min)</div>'
    if ext["avg_ridership_pct"] > 0.1:
        ride_line = f'<div>Projected ridership change: <strong>+{ext["avg_ridership_pct"]:.1f}%</strong> county-wide, positive in {ext["n_tracts_ridership_up"]} tracts (APTA elasticity proxy)</div>'

    summary = f'''
<div class="impact-callout">
  <div class="headline">{name}</div>
  <div>{description} · Scope: {scope_label}</div>
  <div style="margin-top:14px;font-size:18px;color:#1D1D1F !important;font-weight:500">{headline}</div>
  {wait_line}
  {ride_line}
</div>
<div class="kpi-row">
  <div class="kpi-card">
    <div class="label">Tier upgrades</div>
    <div class="value">{s["n_tier_upgrades"]}</div>
    <div class="detail">moved to better tier</div>
  </div>
  <div class="kpi-card">
    <div class="label">Tracts improved</div>
    <div class="value">{s["n_improved"]}</div>
    <div class="detail">of {s["n_tracts"]} total</div>
  </div>
  <div class="kpi-card">
    <div class="label">Avg wait saved</div>
    <div class="value">{ext["avg_wait_saved_min"]:+.1f}<span style="font-size:24px;margin-left:4px">min</span></div>
    <div class="detail">per trip, peak AM</div>
  </div>
  <div class="kpi-card">
    <div class="label">Ridership change</div>
    <div class="value">{ext["avg_ridership_pct"]:+.1f}<span style="font-size:24px;margin-left:2px">%</span></div>
    <div class="detail">elasticity proxy</div>
  </div>
</div>'''

    before, after = before_after_maps(tdf)
    bars = tier_bar_chart(before_counts, after_counts)
    shift = tier_shift_html(result.tier_shifts)
    return summary, before, after, bars, shift


# ---------------------------------------------------------------------------
# Pre-compute preset outputs at startup (fixes HF performance)
# ---------------------------------------------------------------------------
print("Pre-computing preset scenarios...")
PRESET_CACHE = {}
for key, p in PRESETS.items():
    r = run_scenario(deltas=p["deltas"], targets=p["targets"],
                     tract_filter=p["scope"], label=p["label"])
    PRESET_CACHE[key] = format_scenario_output(r, p["label"], p["desc"], p["scope_label"])
    print(f"  {key}: {p['label']} cached")


def run_preset_cached(key):
    return PRESET_CACHE[key]


def run_manual(freq_peak, freq_early, weekend, rail, scope_label, custom_geoids):
    if custom_geoids and custom_geoids.strip():
        try:
            scope = [int(g.strip()) for g in custom_geoids.split(",") if g.strip()]
            scope_str = f"Custom ({len(scope)} tracts)"
        except Exception:
            empty = go.Figure()
            return ('<div class="impact-callout"><div class="headline" style="color:#B03A2E">Invalid GEOID list</div></div>',
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
        return ('<div class="impact-callout"><div class="headline">No changes applied</div></div>',
                empty, empty, empty, "")

    r = run_scenario(deltas=deltas, tract_filter=scope, label="custom")
    desc = " · ".join(f"{k.replace('_',' ')}{v:+g}" for k, v in deltas.items())
    return format_scenario_output(r, "Custom scenario", desc, scope_str)


# ---------------------------------------------------------------------------
# Narrative
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
    if hdy_min >= 60: return f'<span class="hdy-bad">{hdy_min} min</span>'
    if hdy_min >= 30: return f'<span class="hdy-warn">{hdy_min} min</span>'
    return f'<span class="hdy-good">{hdy_min} min</span>'


def generate_narrative(tract_input):
    if not tract_input or not str(tract_input).strip():
        return '<em>Enter a census tract GEOID above (11 digits, starts with 12086).</em>'
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

    # Network analysis
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
<h3 class="section-header">Network analysis</h3>
<div class="impact-callout">
  <div class="headline">Tract is disconnected from the Miami-Dade transit network</div>
  <div>No stops within 500m have weekday AM service in the GTFS feed.</div>
</div>'''

    # Route-level
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
  {int(round(best["best_headway_min"]))} min. Gap is demographic, not service.</div>
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
# Per-tract Recommendations
# ---------------------------------------------------------------------------
def tract_recommendations(tract_input):
    if not tract_input or not str(tract_input).strip():
        return '<em>Enter a tract GEOID above.</em>'
    try:
        tid = int(float(str(tract_input).strip()))
    except Exception:
        return f'<em>Invalid GEOID: {tract_input}</em>'

    bl_row = df[df["tract_geoid"].astype(int) == tid]
    if bl_row.empty:
        return f'<em>Tract {tract_input} not found.</em>'

    recs = recommend_for_tract(sim, run_scenario, tid, df, top_n=5)
    if not recs:
        return '<em>No interventions produced a measurable change for this tract.</em>'

    tier = str(bl_row.iloc[0]["equity_tier"])
    rows_html = []
    for i, r in enumerate(recs, start=1):
        tier_change = f'{r["tier_before"]} → {r["tier_after"]}' if r["tier_changed"] else 'no tier change'
        tier_color = "#1E8449" if r["tier_changed"] else MUTED
        rows_html.append(f'''
<tr>
  <td><strong>#{i}</strong></td>
  <td><strong>{r["label"]}</strong></td>
  <td>{r["delta_deficit"]:+.4f}</td>
  <td>{r["wait_saved_min"]:.1f} min</td>
  <td>{r["ridership_pct"]:+.1f}%</td>
  <td style="color:{tier_color}">{tier_change}</td>
</tr>''')

    top = recs[0]
    top_action = f'''
<div class="impact-callout">
  <div class="headline">Recommended intervention for tract {str(tid).zfill(11)}</div>
  <div style="margin-top:0.4rem;font-size:1.1rem;color:{INK}">
    <strong>{top["label"]}</strong> — expected
    <strong>{abs(top["wait_saved_min"]):.1f}-min wait saved per trip</strong>,
    <strong>{top["ridership_pct"]:+.1f}% ridership</strong>,
    and tier shift <strong>{top["tier_before"]} → {top["tier_after"]}</strong>.
  </div>
</div>'''

    return top_action + f'''
<h3 class="section-header">Top-5 interventions evaluated for this tract</h3>
<table class="data-table">
  <thead>
    <tr><th>Rank</th><th>Intervention</th><th>Deficit change</th><th>Wait saved</th><th>Ridership</th><th>Tier</th></tr>
  </thead>
  <tbody>{"".join(rows_html)}</tbody>
</table>
<p style="color:{MUTED};font-size:0.85rem;margin-top:0.5rem">
  Deficit change is simulator output from XGBoost v3. Wait-saved is
  deterministic from headway math. Ridership uses APTA/TCRP service
  elasticity (peak frequency 0.65, weekend 0.40, rail 1.20).
</p>'''


# Pre-compute county-wide ranking once
print("Computing county-wide intervention ranking...")
COUNTYWIDE_RANKING = recommend_countywide_top_levers(sim, run_scenario, CRITICAL_TRACTS, top_n=8)


# ---------------------------------------------------------------------------
# Priority Routes
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
  <div>The top-5 problem routes touch
  <strong>{n_tracts} Critical + High tracts</strong>. Investing in these
  captures the largest share of vulnerable populations per service hour added.</div>
</div>
<p>Route <strong>{worst["route_short_name"]}</strong>
(<em>{worst["route_long_name"]}</em>) is the #1 priority: reaches
{int(worst["n_critical_high_tracts"])} Critical + High tracts with a worst
AM-peak headway of {int(worst["worst_headway_min"])} minutes.</p>'''


# ---------------------------------------------------------------------------
# Network Analysis
# ---------------------------------------------------------------------------
def network_summary_html():
    covered = int(c2g_network["n_stops_served"].notna().sum())
    total = len(c2g_network)
    median_travel = c2g_network["min_travel_min_to_downtown"].median()
    worst_q = c2g_network["min_travel_min_to_downtown"].quantile(0.75)
    return f'''
<div class="impact-callout">
  <div class="headline">Network connectivity (NetworkX graph on Miami-Dade GTFS)</div>
  <div>Built with <strong>city2graph</strong>: 6,954 stops as nodes, 7,785
  service edges weighted by travel time, all from the real GTFS feed
  (weekday 06:00-09:00). {covered}/{total} tracts have at least one
  network-covered stop within 500m.</div>
</div>
<div class="kpi-row">
  <div class="kpi-card">
    <div class="label">Median travel to downtown</div>
    <div class="value">{median_travel:.0f}<span style="font-size:24px;margin-left:4px">min</span></div>
    <div class="detail">across all 504 tracts</div>
  </div>
  <div class="kpi-card">
    <div class="label">Worst 25 pct</div>
    <div class="value">{worst_q:.0f}+<span style="font-size:24px;margin-left:4px">min</span></div>
    <div class="detail">to reach downtown</div>
  </div>
  <div class="kpi-card">
    <div class="label">Unreachable tracts</div>
    <div class="value">{int(c2g_network["n_stops_served"].isna().sum())}</div>
    <div class="detail">no GTFS service within 500m</div>
  </div>
  <div class="kpi-card critical">
    <div class="label">Isolated stops</div>
    <div class="value">182</div>
    <div class="detail">cannot reach downtown on network</div>
  </div>
</div>'''


def network_table():
    t = c2g_network.copy()
    t = t[t["n_stops_served"].notna()].sort_values(
        "min_travel_min_to_downtown", ascending=False).head(20)
    t["equity_tier"] = t["GEOID"].map(df.set_index("tract_geoid")["equity_tier"])
    t = t[["GEOID", "equity_tier", "n_stops_served",
           "min_travel_min_to_downtown", "mean_closeness_rank",
           "pct_isolated"]].copy()
    t.columns = ["GEOID", "Tier", "Stops within 500m",
                 "Travel to downtown (min)", "Connectivity rank",
                 "Pct isolated stops"]
    return t.round(1)


def network_map():
    m = gdf.merge(c2g_network[["GEOID", "min_travel_min_to_downtown"]],
                  on="GEOID", how="left")
    m["min_travel_min_to_downtown"] = m["min_travel_min_to_downtown"].fillna(90)
    vmax = m["min_travel_min_to_downtown"].quantile(0.95)
    fig = px.choropleth_mapbox(
        m, geojson=gdf_geojson, locations="GEOID",
        featureidkey="properties.GEOID",
        color="min_travel_min_to_downtown",
        color_continuous_scale=[[0, "#F5F5F7"], [0.4, "#FFE0B2"],
                                [0.7, "#FF8C42"], [1, "#D93025"]],
        range_color=(10, vmax),
        mapbox_style="carto-positron",
        zoom=9, center={"lat": 25.77, "lon": -80.25},
        opacity=0.80,
        labels={"min_travel_min_to_downtown": "Min to downtown"},
    )
    fig.update_traces(marker_line_width=0.4, marker_line_color="#FFFFFF")
    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        height=560, paper_bgcolor="#FFFFFF",
        font=dict(family="-apple-system, SF Pro Text, sans-serif", color="#1D1D1F", size=12),
        coloraxis_colorbar=dict(
            title=dict(text="Minutes to downtown", font=dict(color="#1D1D1F", size=11)),
            tickfont=dict(color="#1D1D1F", size=11),
            thickness=10, len=0.5, outlinewidth=0, bgcolor="rgba(0,0,0,0)",
        ),
    )
    return fig


# ---------------------------------------------------------------------------
# Alerts tab
# ---------------------------------------------------------------------------
def alerts_html():
    fragile = df[df["flag_fragile"] == True].sort_values(
        "projected_need_2027", ascending=False).head(10)
    worsening = df[df["flag_worsening"] == True].sort_values(
        "deficit_predicted", ascending=False).head(10)
    crit = df[df["equity_tier"] == "Critical"]

    # Alert 1: tracts projected to tip into Critical by 2027
    alert1 = f'''
<div class="impact-callout" style="background:linear-gradient(135deg,#FDEDEC 0%,white 80%);border-left-color:#B03A2E">
  <div class="headline" style="color:#B03A2E">ALERT · {len(fragile)} tracts projected to worsen by 2027</div>
  <div>These tracts have fragile equity scores per the ACS time-series model.
  Without intervention, they will likely enter or deepen Critical service gaps.
  Top 10 by projected need shown below.</div>
</div>'''

    # Alert 2: top problem routes
    worst_route = c2g_problems.iloc[0]
    alert2 = f'''
<div class="impact-callout">
  <div class="headline">ALERT · Bottleneck route reaches {int(worst_route["n_critical_high_tracts"])} vulnerable tracts</div>
  <div>Route <strong>{worst_route["route_short_name"]}</strong>
  ({worst_route["route_long_name"]}) has a worst-case AM headway of
  {int(worst_route["worst_headway_min"])} minutes and serves
  {int(worst_route["n_critical_high_tracts"])} Critical + High tracts. It is the
  single highest-leverage route for investment.</div>
</div>'''

    rows = []
    for _, r in fragile.iterrows():
        rows.append(f'<tr><td>{r["tract_geoid"]}</td><td>{_tier_badge(r["equity_tier"])}</td>'
                    f'<td>{r["projected_need_2027"]:.1f}</td><td>{r["deficit_predicted"]:.3f}</td></tr>')

    return alert1 + alert2 + f'''
<h3 class="section-header">Top 10 fragile tracts (projected need 2027)</h3>
<table class="data-table">
  <thead><tr><th>GEOID</th><th>Current tier</th><th>Projected need 2027</th><th>Current deficit</th></tr></thead>
  <tbody>{''.join(rows)}</tbody>
</table>'''


# ---------------------------------------------------------------------------
# CSS + Hero
# ---------------------------------------------------------------------------
CUSTOM_CSS = f"""
/* Apple-inspired system — restrained typography, generous whitespace,
   hairline dividers, restrained color. */

.gradio-container {{
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text',
               'Helvetica Neue', 'Inter', system-ui, sans-serif !important;
  max-width: 1180px !important;
  background: #FFFFFF !important;
  padding: 0 2rem !important;
}}

html, body {{ background: #FFFFFF !important }}
/* Scoped text-color — explicitly avoid plotly/mapbox so tile layers keep their paint. */
body, .gradio-container > *, p, li, td, th, label, small, strong, em {{
  color: #1D1D1F !important;
}}
.gradio-container .block, .gradio-container .markdown, .gradio-container .form,
.gradio-container button, .gradio-container input, .gradio-container textarea,
.gradio-container h1, .gradio-container h2, .gradio-container h3, .gradio-container h4 {{
  color: #1D1D1F !important;
}}
a {{ color: #1D1D1F !important; text-decoration: underline; text-underline-offset: 3px }}

h1, h2, h3, h4 {{ color: #1D1D1F !important; letter-spacing: -0.01em }}

/* ── Hero ──────────────────────────────────────────────────────── */
.hero {{
  padding: 4rem 0 2rem 0;
  margin-bottom: 0;
  background: transparent;
  border: none;
  border-radius: 0;
}}
.hero .eyebrow {{
  color: #6E6E73 !important;
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 0.8px;
  text-transform: uppercase;
  margin-bottom: 20px;
}}
.hero h1 {{
  color: #1D1D1F !important;
  font-size: 52px;
  font-weight: 700;
  letter-spacing: -0.025em;
  line-height: 1.05;
  margin: 0 0 24px 0;
  max-width: 820px;
}}
.hero .tagline {{
  color: #515154 !important;
  font-size: 19px;
  font-weight: 400;
  line-height: 1.55;
  max-width: 640px;
}}

/* ── KPI row: horizontal stats with hairline dividers ────────── */
.kpi-row {{
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0;
  border-top: 1px solid #D2D2D7;
  border-bottom: 1px solid #D2D2D7;
  padding: 32px 0;
  margin: 3rem 0 2.5rem 0;
}}
.kpi-card {{
  background: transparent !important;
  border: none !important;
  border-right: 1px solid #D2D2D7 !important;
  border-radius: 0 !important;
  padding: 0 28px !important;
  box-shadow: none !important;
  transition: none !important;
}}
.kpi-card:last-child {{ border-right: none !important }}
.kpi-card:hover {{ transform: none !important; box-shadow: none !important }}
.kpi-card .label {{
  color: #6E6E73 !important;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.6px;
  text-transform: uppercase;
  margin-bottom: 12px;
}}
.kpi-card .value {{
  color: #1D1D1F !important;
  font-size: 48px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.025em;
  line-height: 1.05;
  margin: 0 0 8px 0;
}}
.kpi-card .detail {{
  color: #6E6E73 !important;
  font-size: 13px;
  line-height: 1.4;
}}
.kpi-card.critical .value {{ color: #D93025 !important }}

/* ── Section headers ──────────────────────────────────────────── */
.section-header {{
  color: #1D1D1F !important;
  font-weight: 600;
  font-size: 13px;
  letter-spacing: 0.6px;
  text-transform: uppercase;
  border-bottom: 1px solid #D2D2D7;
  padding: 0 0 10px 0;
  margin: 2rem 0 1rem 0;
}}

/* ── Tier badges & flag badges ────────────────────────────────── */
.tier-badge {{
  display: inline-block;
  padding: 4px 12px;
  border-radius: 4px;
  font-weight: 600;
  font-size: 11px;
  color: white !important;
  letter-spacing: 0.8px;
  font-variant: small-caps;
}}
.flag-badge {{
  display: inline-block;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.4px;
}}
.flag-fragile {{ background: #FFF5F4 !important; color: #D93025 !important; border: 1px solid #F8D7D4 }}
.flag-worsening {{ background: #FFF8E6 !important; color: #8B6B00 !important; border: 1px solid #FFE0A3 }}

/* ── Narrative card ───────────────────────────────────────────── */
.narrative-card {{
  background: #FFFFFF;
  border: 1px solid #D2D2D7;
  border-radius: 14px;
  padding: 28px 32px;
  margin-bottom: 1.5rem;
}}
.score-row {{ display: flex; gap: 3rem; margin-top: 1.5rem; flex-wrap: wrap }}
.score-item .score-label {{
  color: #6E6E73 !important;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  margin-bottom: 6px;
}}
.score-item .score-value {{
  color: #1D1D1F !important;
  font-size: 28px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.02em;
}}

/* ── Data tables — Apple quiet style ──────────────────────────── */
.data-table {{
  width: 100%;
  border-collapse: collapse;
  margin: 1rem 0 1.5rem 0;
  font-size: 14px;
  color: #1D1D1F !important;
}}
.data-table th {{
  background: transparent !important;
  color: #6E6E73 !important;
  font-weight: 600;
  font-size: 11px;
  letter-spacing: 0.6px;
  text-transform: uppercase;
  border-bottom: 1px solid #1D1D1F;
  padding: 12px 16px;
  text-align: left;
}}
.data-table td {{
  color: #1D1D1F !important;
  border-bottom: 1px solid #F5F5F7;
  padding: 14px 16px;
  text-align: left;
  font-weight: 400;
}}
.data-table.routes-table td:first-child {{ font-weight: 600 }}
.data-table.tier-shift td, .data-table.tier-shift th {{ text-align: center }}

.hdy-bad  {{ color: #D93025 !important; font-weight: 600; font-variant-numeric: tabular-nums }}
.hdy-warn {{ color: #C05500 !important; font-weight: 600; font-variant-numeric: tabular-nums }}
.hdy-good {{ color: #0F7938 !important; font-weight: 600; font-variant-numeric: tabular-nums }}

/* ── Callouts — quiet grey fill, no gradient ──────────────────── */
.impact-callout {{
  background: #F5F5F7;
  border: none;
  border-radius: 12px;
  padding: 20px 24px;
  margin: 1.25rem 0;
}}
.impact-callout .headline {{
  color: #1D1D1F !important;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: -0.01em;
  margin-bottom: 6px;
}}
.impact-callout div, .impact-callout p {{
  color: #515154 !important;
  font-size: 14px;
  line-height: 1.5;
}}

/* ── Preset buttons — minimalist ─────────────────────────────── */
button.preset-btn {{
  min-height: 88px !important;
  background: #FFFFFF !important;
  color: #1D1D1F !important;
  border: 1px solid #D2D2D7 !important;
  border-radius: 12px !important;
  font-weight: 500 !important;
  text-align: left !important;
  white-space: normal !important;
  padding: 16px 18px !important;
  transition: border-color 0.15s, background 0.15s !important;
  line-height: 1.4 !important;
  font-size: 14px !important;
  box-shadow: none !important;
}}
button.preset-btn:hover {{
  border-color: #1D1D1F !important;
  background: #F5F5F7 !important;
  transform: none !important;
}}

/* ── Primary CTA — solid ink, not orange (Apple-style) ───────── */
button.primary-cta {{
  background: #1D1D1F !important;
  color: #FFFFFF !important;
  border: none !important;
  border-radius: 980px !important;
  font-weight: 500 !important;
  padding: 12px 24px !important;
  box-shadow: none !important;
  letter-spacing: 0 !important;
  font-size: 14px !important;
}}
button.primary-cta:hover {{ background: #000000 !important }}

/* ── Tabs — Apple underline (full-width on active) ─────────────── */
.tabs, .tab-nav, [role="tablist"] {{
  background: transparent !important;
  border: none !important;
  border-bottom: 1px solid #D2D2D7 !important;
  padding: 0 !important;
  gap: 0 !important;
}}
button[role="tab"] {{
  font-weight: 500 !important;
  color: #86868B !important;
  font-size: 14px !important;
  letter-spacing: -0.01em !important;
  background: transparent !important;
  border: none !important;
  border-bottom: 2px solid transparent !important;
  border-radius: 0 !important;
  padding: 14px 16px !important;
  margin: 0 !important;
  box-shadow: none !important;
}}
button[role="tab"]:hover {{ color: #1D1D1F !important; background: transparent !important }}
button[role="tab"][aria-selected="true"] {{
  color: #1D1D1F !important;
  border-bottom: 2px solid #1D1D1F !important;
  font-weight: 600 !important;
  background: transparent !important;
  box-shadow: none !important;
}}
/* Neutralise any orange indicator Gradio may inject */
.tab-nav button[aria-selected="true"]::after,
.tab-nav button[aria-selected="true"]::before,
[role="tab"][aria-selected="true"]::after,
[role="tab"][aria-selected="true"]::before {{
  background: #1D1D1F !important;
  border-color: #1D1D1F !important;
}}
.tabs .selected {{ color: #1D1D1F !important; border-color: #1D1D1F !important }}

/* ── Gradio resets ────────────────────────────────────────────── */
footer {{ display: none !important }}
.block-title, .label-wrap label {{ color: #1D1D1F !important; font-weight: 500 !important }}
.markdown, .prose {{ color: #1D1D1F !important }}
.markdown h1, .markdown h2, .markdown h3 {{ color: #1D1D1F !important }}
.markdown ul, .markdown ol, .markdown li {{ color: #1D1D1F !important }}
.markdown strong {{ color: #1D1D1F !important; font-weight: 600 }}

/* Input fields — Apple clean */
textarea, input[type="text"], input[type="number"] {{
  background: #FFFFFF !important;
  color: #1D1D1F !important;
  border: 1px solid #D2D2D7 !important;
  border-radius: 10px !important;
  font-size: 15px !important;
  padding: 12px 16px !important;
}}
textarea:focus, input:focus {{ border-color: #1D1D1F !important; outline: none !important }}

/* Sliders */
.gr-slider, input[type="range"] {{ accent-color: #1D1D1F !important }}

/* ── Force light theme on every Gradio component ─────────────── */
.dark, .dark *, [class*="dark"] {{ background: #FFFFFF !important; color: #1D1D1F !important }}

/* Gradio Dataframe tables — Apple clean */
.gradio-container table, .gradio-container tbody, .gradio-container thead,
.gradio-container tr, .gradio-container td, .gradio-container th,
.gradio-container .table-wrap, .gradio-container .table-wrap *,
.gr-dataframe, .gr-dataframe *, .gr-dataframe table, .gr-dataframe td, .gr-dataframe th,
.svelte-virtual-table-viewport, .svelte-virtual-table-viewport * {{
  background: #FFFFFF !important;
  background-color: #FFFFFF !important;
  color: #1D1D1F !important;
  border-color: #F5F5F7 !important;
}}
.gradio-container thead th, .gr-dataframe thead th {{
  background: #F5F5F7 !important; background-color: #F5F5F7 !important;
  color: #6E6E73 !important;
  font-weight: 600 !important;
  text-transform: uppercase;
  font-size: 11px !important;
  letter-spacing: 0.6px;
  border-bottom: 1px solid #1D1D1F !important;
  padding: 12px 16px !important;
}}
.gradio-container tbody td, .gr-dataframe tbody td {{
  padding: 12px 16px !important;
  font-size: 14px !important;
  border-bottom: 1px solid #F5F5F7 !important;
}}

/* Accordion + Column + Row light backgrounds */
.gr-accordion, .gr-accordion-body, .gr-accordion-header,
.gr-row, .gr-column, .gr-group, .gr-form, .gr-box, .gr-panel,
details, details summary, details[open],
.panel, .block {{
  background: #FFFFFF !important;
  background-color: #FFFFFF !important;
  color: #1D1D1F !important;
  border-color: #D2D2D7 !important;
}}
.gr-accordion summary {{
  color: #1D1D1F !important;
  font-weight: 500 !important;
  background: #F5F5F7 !important;
  padding: 12px 16px !important;
  border-radius: 10px !important;
}}

/* Radio + Checkbox groups */
.gr-radio, .gr-radio *, .gr-checkbox, .gr-checkbox * {{
  background: #FFFFFF !important; color: #1D1D1F !important;
}}
.gr-radio label, .gr-checkbox label {{
  background: #FFFFFF !important;
  color: #1D1D1F !important;
  border: 1px solid #D2D2D7 !important;
  border-radius: 980px !important;
  padding: 8px 16px !important;
}}
.gr-radio input:checked + label, .gr-radio label[data-checked="true"] {{
  background: #1D1D1F !important; color: #FFFFFF !important;
  border-color: #1D1D1F !important;
}}

/* Slider labels */
.gr-slider label, .gr-slider .gr-block-label {{ color: #1D1D1F !important }}

/* Plot containers — keep Plotly/Mapbox rendering untouched.
   Do NOT force background or color here, or map tiles / choropleth
   will disappear. */
.js-plotly-plot .mapboxgl-map, .js-plotly-plot canvas,
.js-plotly-plot .plot-container {{
  background: transparent !important;
}}
"""

HERO_HTML = f'''
<div class="hero">
  <div class="eyebrow">Miami-Dade Transit Equity · University of Miami · Deloitte</div>
  <h1>Measure the gap.<br>Model the fix.</h1>
  <div class="tagline">
    504 census tracts. Four policy levers. One simulator that quantifies
    which transit investments move the most people out of service-gap
    crisis — and surfaces the exact routes and network gaps driving need.
  </div>
</div>
<div class="kpi-row">
  <div class="kpi-card critical">
    <div class="label">Critical tracts</div>
    <div class="value">{KPIS["critical"]}</div>
    <div class="detail">in severe service gap</div>
  </div>
  <div class="kpi-card">
    <div class="label">High-risk</div>
    <div class="value">{KPIS["high"]}</div>
    <div class="detail">significant service gap</div>
  </div>
  <div class="kpi-card">
    <div class="label">Fragile by 2027</div>
    <div class="value">{KPIS["fragile"]}</div>
    <div class="detail">projected to worsen</div>
  </div>
  <div class="kpi-card">
    <div class="label">Rail expansion</div>
    <div class="value">{KPIS["rail_pct"]}%</div>
    <div class="detail">of tracts improve</div>
  </div>
</div>'''


THEME = gr.themes.Soft(
    primary_hue=gr.themes.colors.slate,
    secondary_hue=gr.themes.colors.slate,
    neutral_hue=gr.themes.colors.slate,
).set(
    body_background_fill="white",
    background_fill_primary="white",
    background_fill_secondary=OFF_WHITE,
    block_background_fill="white",
    block_border_width="1px",
    body_text_color=INK,
    button_primary_background_fill="#1D1D1F",
    button_primary_background_fill_hover="#000000",
    button_primary_text_color="white",
)

# ---------------------------------------------------------------------------
# Gradio Blocks
# ---------------------------------------------------------------------------
with gr.Blocks(title="Miami-Dade Transit Equity Simulator", theme=THEME, css=CUSTOM_CSS) as demo:
    gr.HTML(HERO_HTML)

    with gr.Tabs():
        # ── Overview ─────────────────────────────────────────────────────
        with gr.Tab("Overview"):
            gr.HTML(f'''
<div class="impact-callout">
  <div class="headline">What are we looking at</div>
  <div>Each tract is scored on an <strong>equity priority index</strong>
  combining demographic need with service deficit.
  The {KPIS["critical"]} Critical tracts are where transit gaps meet the
  highest dependency — these are the places a policy dollar buys the most
  equity.</div>
</div>''')
            # Wrap Plotly in an iframe srcdoc — Gradio's gr.HTML strips
            # <script> tags, which killed the inline Plotly.newPlot() call.
            # Iframe content is not sanitised.
            import plotly.io as _pio
            _overview_full_html = _pio.to_html(
                overview_map(), full_html=True,
                include_plotlyjs="cdn",
                config={"displayModeBar": False},
            )
            _overview_escaped = _overview_full_html.replace('"', '&quot;')
            gr.HTML(
                f'<iframe srcdoc="{_overview_escaped}" '
                f'style="width:100%; height:620px; border:0;"></iframe>'
            )
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
Per our XGBoost v3 model (CV R²=0.823):
1. **Peak AM frequency** (SHAP 39.6%) — fastest single lever
2. **Weekend / weekday ratio** (SHAP 21.7%)
3. **Early AM frequency** (SHAP 6.9%)
4. **Rail modal share** — largest *county-wide* impact per lever

Head to **Simulate Policy** or **Recommendations** to test interventions.
''')

        # ── Tract Explorer ──────────────────────────────────────────────
        with gr.Tab("Tract Explorer"):
            gr.Markdown('''
Pick a tract to see demographics, service levels, network connectivity, and
the specific bus routes serving it.
''')
            with gr.Row():
                tract_input = gr.Textbox(label="Census tract GEOID",
                                         placeholder="e.g. 12086000220", scale=3)
                tract_btn = gr.Button("Generate narrative",
                                      elem_classes=["primary-cta"], scale=1)
            gr.Markdown("**Try these Critical tracts with a 90-min-headway route:** `12086000220`, `12086000307`")
            narrative_output = gr.HTML(value='<em>Enter a tract ID above and click Generate narrative.</em>')
            tract_btn.click(fn=generate_narrative, inputs=tract_input, outputs=narrative_output)
            tract_input.submit(fn=generate_narrative, inputs=tract_input, outputs=narrative_output)

        # ── Simulate Policy ─────────────────────────────────────────────
        with gr.Tab("Simulate Policy"):
            gr.Markdown("### Five reference policies · click to run (pre-computed at startup)")

            preset_buttons = {}
            with gr.Row():
                for key in ["S1", "S2", "S3"]:
                    p = PRESETS[key]
                    preset_buttons[key] = gr.Button(
                        f"{p['label']}\n{p['desc']}", elem_classes=["preset-btn"])
            with gr.Row():
                for key in ["S4", "S5"]:
                    p = PRESETS[key]
                    preset_buttons[key] = gr.Button(
                        f"{p['label']}\n{p['desc']}", elem_classes=["preset-btn"])
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
                map_before = gr.HTML(value="")
                map_after = gr.HTML(value="")
            with gr.Row():
                tier_bars = gr.Plot(label="Tier distribution", container=False)
                tier_shift_out = gr.HTML(value="")

            out_list = [scenario_summary, map_before, map_after, tier_bars, tier_shift_out]

            for key, btn in preset_buttons.items():
                btn.click(fn=lambda k=key: run_preset_cached(k), inputs=None, outputs=out_list)

            run_custom_btn.click(
                fn=run_manual,
                inputs=[s_freq_peak, s_freq_early, s_weekend, s_rail, s_scope, s_custom],
                outputs=out_list,
            )

        # ── Recommendations ─────────────────────────────────────────────
        with gr.Tab("Recommendations"):
            gr.HTML(f'''
<div class="impact-callout">
  <div class="headline">Actionable interventions per tract</div>
  <div>For any tract, the engine evaluates 8 candidate single-lever
  interventions, runs each through the simulator, and ranks by equity
  improvement. Reports wait-time saved, ridership change, and tier shift.</div>
</div>''')
            with gr.Row():
                rec_input = gr.Textbox(label="Census tract GEOID",
                                       placeholder="e.g. 12086000220", scale=3)
                rec_btn = gr.Button("Recommend interventions",
                                    elem_classes=["primary-cta"], scale=1)
            rec_out = gr.HTML(value='<em>Enter a tract GEOID above.</em>')
            rec_btn.click(fn=tract_recommendations, inputs=rec_input, outputs=rec_out)
            rec_input.submit(fn=tract_recommendations, inputs=rec_input, outputs=rec_out)

            gr.Markdown("### County-wide intervention ranking")
            gr.Markdown("*Each intervention applied to all Critical tracts. Ranked by # tracts moved out of Critical.*")
            gr.Dataframe(value=COUNTYWIDE_RANKING, interactive=False, wrap=True)

        # ── Priority Routes ─────────────────────────────────────────────
        with gr.Tab("Priority Routes"):
            gr.HTML(priority_routes_summary_html())
            gr.Markdown("### Top 15 problem routes — ranked by impact on Critical + High tracts")
            gr.Dataframe(value=priority_routes_table(), interactive=False, wrap=True)

        # ── Network Analysis ────────────────────────────────────────────
        with gr.Tab("Network Analysis"):
            gr.HTML(network_summary_html())
            gr.Markdown("### Travel-time to downtown from each tract (NetworkX shortest path)")
            gr.HTML(fig_to_iframe(network_map(), 560))
            gr.Markdown("### 20 tracts with longest travel time to downtown")
            gr.Dataframe(value=network_table(), interactive=False, wrap=True)

        # ── Alerts ──────────────────────────────────────────────────────
        with gr.Tab("Alerts"):
            gr.HTML(alerts_html())

        # ── About ───────────────────────────────────────────────────────
        with gr.Tab("About"):
            gr.Markdown(f'''
## Business questions this tool answers

1. **Where are the gaps?** · Overview + tier map show the {KPIS["critical"]} Critical tracts immediately.
2. **Why is this tract gapped?** · Tract Explorer pulls demographics, service levels, network metrics, bottleneck route.
3. **Which lever has the biggest impact here?** · Recommendations tab evaluates 8 interventions per tract, ranks by expected equity improvement.
4. **How much wait time do we save?** · Deterministic from headway math: *wait = headway / 2*, so *saved = Δheadway / 2*.
5. **How much ridership do we gain?** · APTA/TCRP service elasticity — {FREQUENCY_ELASTICITY} for peak frequency, {WEEKEND_WEEKDAY_ELASTICITY} weekend, {RAIL_SUBSTITUTION_FACTOR} rail substitution.
6. **Where should we invest first?** · Priority Routes shows which bus lines touch the most vulnerable tracts. County-wide ranking (in Recommendations) shows which policy moves the most tracts out of Critical.
7. **Who is getting worse?** · Alerts flags {KPIS["fragile"]} fragile tracts projected to worsen by 2027.

## Methodology

**Baseline.** 504 Miami-Dade census tracts × 29 columns. ACS 2019–2024
demographics, Sprint 2a equity composites, Sprint 2b XGBoost deficit
predictions (CV R²=0.823), time-series projections to 2027.

**Simulator.** User adjusts 4 service levers → XGBoost v3 re-predicts
deficit → proportional-change applied to Sprint 2a composite → tier
reassignment with Sprint 2a fixed cutoffs. 99.6% tier recovery at zero
delta.

**Wait-time saved.** Exact deterministic math for uniform arrivals:
*E[wait] = headway / 2*, so *wait_saved = Δheadway / 2*.

**Ridership change.** Service elasticity proxy from APTA *Understanding
Transit Ridership Dynamics* and TCRP Report 95, Chapter 9. Peak-frequency
elasticity = 0.65, weekend-service elasticity = 0.40, rail-substitution
factor = 1.20. Combined linearly per lever.

**Route-level diagnostic.** Miami-Dade GTFS 2026-03-24, 123 routes, 6,954
stops, 972K stop-events. Per (route, stop) weekday AM-peak headway from
06:00-09:00 service. Stops spatial-joined to tracts with 500m walking
buffer.

**Network analysis.** `city2graph` + NetworkX: 6,954 stops as nodes, 7,785
service edges weighted by travel time. Per-stop closeness + betweenness
centrality; shortest-path travel time to Downtown Government Center.

## What this tool is NOT

- Not a ridership forecaster using boarding data. The ridership metric
  here is an elasticity proxy, not APC or farebox data. Real boardings
  data would produce tighter per-route estimates.
- Not a cost-benefit analyzer. Service hours and operating cost are not
  modeled. A full investment ranking would add cost-per-hour and
  compute impact-per-dollar.
- Not a live dashboard. GTFS is a 2026-03-24 snapshot; ACS data is
  2019–2024. Refreshing the baseline is a quarterly task.

## Credits

- **Luna Sage** — Sprint 3.1 baseline + Sprint 3.2 simulator engine
- **Lina Graf** — Gradio V2/V3 dashboard prototypes
- **Daniel Regalado Cardoso** — Sprint 1/2 modeling, Sprint 3.3 validation,
  city2graph integration, extended metrics, recommendations engine, production UI
- **Partners:** University of Miami MSBA · Deloitte · Miami-Dade Transit

## Data sources

- [Miami-Dade Transit GTFS](https://www.miamidade.gov/transit/) 2026-03-24
- [US Census TIGERweb](https://tigerweb.geo.census.gov/) for geometries
- [American Community Survey](https://www.census.gov/programs-surveys/acs) 2019–2024
- [city2graph](https://pypi.org/project/city2graph/)
- Service elasticity: APTA / TCRP Report 95 Ch. 9

*Code + validation notebook open-source in the [project repo](https://github.com/DanielRegaladoUMiami/CapstoneProject-AI-for-Equitable-Transportation).*
''')


if __name__ == "__main__":
    # SSR=False is required: Gradio 5's experimental SSR pre-renders HTML
    # without triggering the Plotly/Mapbox WebGL initialization on the
    # client, which leaves the map container empty in some browsers.
    demo.queue(default_concurrency_limit=4).launch(ssr_mode=False)
