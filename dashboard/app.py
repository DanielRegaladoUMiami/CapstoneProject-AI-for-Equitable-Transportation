"""
Interactive Dashboard — AI for Equitable Public Transportation

Sprint 3b: Streamlit dashboard with core views:
1. Map visualization: access gaps + demographic overlay
2. Scenario comparison: baseline vs. proposed changes
3. Equity indicators: ridership, accessibility, equity metrics by area

Run: streamlit run dashboard/app.py
"""

import streamlit as st

st.set_page_config(
    page_title="AI for Equitable Transportation",
    page_icon="🚍",
    layout="wide",
)

st.title("🚍 AI for Equitable Public Transportation")
st.caption("Miami-Dade County Transit Equity Dashboard")

# TODO: Implement in Sprint 3b
st.info("Dashboard under construction — Sprint 3 (Mar 28 – Apr 17)")

# ── Sidebar ──
st.sidebar.header("Navigation")
page = st.sidebar.radio("Select View", [
    "🗺️ Access Gap Map",
    "📊 Scenario Comparison",
    "📈 Equity Indicators",
])

if page == "🗺️ Access Gap Map":
    st.header("Transit Access Gaps")
    st.write("Map visualization: current access gaps overlaid with demographic data.")
    # TODO: Folium/Plotly map

elif page == "📊 Scenario Comparison":
    st.header("Scenario Comparison")
    st.write("Baseline vs. proposed service changes side by side.")
    # TODO: Simulation results visualization

elif page == "📈 Equity Indicators":
    st.header("Equity Indicators")
    st.write("Ridership, accessibility, and equity metrics by area.")
    # TODO: Charts and KPIs
