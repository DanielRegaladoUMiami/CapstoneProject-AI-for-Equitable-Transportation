# Miami-Dade Transit Equity Simulator — Glossary

A reference for every term used in the app. Use this when explaining the tool to a stakeholder, when writing the report, or when answering questions during the demo.

Each entry has three parts:
- **What it is** — the precise definition
- **How it's computed** — the math or data source
- **How to explain it** — the plain-English version for a non-technical audience

---

## Table of Contents

1. [Geography & Population](#1--geography--population)
2. [Equity & Priority](#2--equity--priority)
3. [Service / Access Side](#3--service--access-side)
4. [Need / Demographic Side](#4--need--demographic-side)
5. [Modeling](#5--modeling)
6. [Simulator Mechanics](#6--simulator-mechanics)
7. [Scenario Outputs / KPIs](#7--scenario-outputs--kpis)
8. [Network Analysis](#8--network-analysis)
9. [Recommendations Engine](#9--recommendations-engine)
10. [Data Sources & Standards](#10--data-sources--standards)

---

## 1 · Geography & Population

### Census Tract
- **What it is:** A small, statistically stable geographic unit defined by the U.S. Census Bureau, typically containing 1,200–8,000 people. The base unit of analysis in the app.
- **How it's computed:** Provided directly by the Census Bureau. Identified by an 11-digit GEOID (e.g., `12086000220`).
- **How to explain it:** "A neighborhood-sized area we use as the unit of measurement. Miami-Dade has 504 of them."

### GEOID
- **What it is:** The unique 11-digit identifier for a census tract.
- **How it's computed:** State (12 = Florida) + County (086 = Miami-Dade) + Tract (6 digits).
- **How to explain it:** "The tract's unique ID — like a zip code, but for census tracts."

### Miami-Dade County
- **What it is:** The geographic scope of the project.
- **Total tracts in baseline:** 504 (after excluding 3 tracts with insufficient ACS or GTFS coverage).

---

## 2 · Equity & Priority

### Equity Priority Score
- **What it is:** The headline number for each tract — a 0-to-1 index where higher means more equity-investment priority.
- **How it's computed:** `composite_need × composite_access_deficit`. Multiplicative so a tract only scores high if BOTH need AND service-gap are high.
- **How to explain it:** "Combines how much the population depends on transit with how poorly transit serves them. Higher = more urgent investment target."

### Priority Tier *(formerly "Equity Tier")*
- **What it is:** Categorical label assigned to each tract based on its equity priority score: **Critical**, **High**, **Moderate**, or **Low**.
- **How it's computed:** Fixed quartile cutoffs from the baseline equity-score distribution (Sprint 2a).
- **How to explain it:** "Stoplight grouping. Red (Critical) is the urgent quartile; green (Low) is fine for now."

### Critical
- **What it is:** Top quartile of priority — most urgent intervention targets.
- **Count in Miami-Dade:** **51 tracts** (baseline).
- **Color:** Red.

### High
- **What it is:** Second quartile — significant gap, second-priority for action.
- **Color:** Orange.

### Moderate
- **What it is:** Third quartile — some gap, watch list.
- **Color:** Yellow.

### Low
- **What it is:** Bottom quartile — adequately served relative to need.
- **Color:** Green.

### Tier Cutoffs
- **What it is:** The four boundary values that map an equity score to a tier label.
- **How it's computed:** Derived from the baseline distribution: each tier's upper bound = the max equity score among tracts originally labeled that tier.
- **Why it matters:** They're **fixed**. If we re-derived them every scenario, we'd never see tier improvements — every scenario would just re-quartile itself.

### Composite Need
- **What it is:** A 0–1 demographic index of how much a tract's residents *depend* on transit.
- **How it's computed:** Weighted combination of ACS variables — % low-income, % zero-vehicle households, % seniors, % disabled, % minority — normalized.
- **How to explain it:** "How much do the people here actually need the bus? Higher = more dependence."

### Composite Access Deficit
- **What it is:** A 0–1 service-side index of how poorly transit serves a tract relative to county standards.
- **How it's computed:** Built from headway, frequency, route-coverage, and connectivity variables, scaled to the 0–1 range.
- **How to explain it:** "How bad is the bus service here? Higher = bigger gap."

---

## 3 · Service / Access Side

### Headway
- **What it is:** The time between consecutive buses on a route, in minutes.
- **How it's computed:** From GTFS `stop_times.txt`, computed per route × stop × time-window.
- **How to explain it:** "How long you wait between buses. 15-min headway = a bus every 15 minutes."

### Headway (Peak AM)
- **What it is:** Headway measured during the 6–9 AM weekday window. The most policy-sensitive lever.
- **Variable name:** `headway_peak_am_min`

### Headway (Early AM)
- **What it is:** Headway measured during the 4–6 AM window. Captures service for early-shift workers.
- **Variable name:** `headway_early_min`

### Frequency (TPH = Trips Per Hour)
- **What it is:** Inverse of headway. `frequency = 60 / headway`.
- **Why both?** Planners think in frequency ("we run 4 buses an hour"); riders feel headway ("I wait 15 minutes"). The model uses both.

### Weekend / Weekday Ratio
- **What it is:** Weekend service hours divided by weekday service hours, on a 0–1 scale.
- **Typical values:** 0.4–0.6 in Miami-Dade. A "weekend parity" policy targets ≥ 0.80.

### Rail Trip Share
- **What it is:** Fraction of a tract's transit trips taken on rail (Metrorail) vs. bus.
- **Why it matters:** Rail service is faster and higher-capacity; shifting trips to rail produces a multiplier effect (1.2× ridership impact factor).

### Service Deficit *(predicted)*
- **What it is:** The model's continuous prediction of how much a tract's transit service falls short of demand.
- **How it's computed:** XGBoost v3 prediction from 13 service + demographic features.
- **How to explain it:** "How much worse the bus is here than it should be, given the population."

### Lever
- **What it is:** Any of the 4 user-adjustable service variables in the simulator: `freq_peak_am_tph`, `freq_early_tph`, `weekend_weekday_ratio`, `rail_trip_share`.
- **How to explain it:** "The knobs we can turn — the things a policy can actually change."

### Lever Catalog
- **What it is:** JSON config that defines each lever's valid range (`data_range`), units, and description. Prevents the simulator from running physically impossible scenarios (e.g., negative frequencies).

---

## 4 · Need / Demographic Side

### ACS (American Community Survey)
- **What it is:** The Census Bureau's annual demographic survey. Source for all our need-side variables.
- **Years used:** 2019–2024 (5-year ACS averages).

### Trend Variables
- **What they are:** Year-over-year change in commute behavior per tract. Used to project future need.
- **Variables:**
  - `trend_commute_public_transit_pct` — % commuters using transit
  - `trend_commute_drove_alone_pct` — % commuters driving alone
  - `trend_commute_wfh_pct` — % working from home
  - `trend_mean_commute_time_min` — average commute time

### Fragile *(flag)*
- **What it is:** A binary flag (`flag_fragile`) for tracts projected to worsen by 2027 based on demographic trends.
- **How it's computed:** Time-series projection of equity score forward 2 years; tract is "fragile" if projected score crosses into a worse tier.
- **How to explain it:** "Tracts that look OK today but are heading in the wrong direction. Get ahead of them now."

### Worsening *(flag)*
- **What it is:** Binary flag (`flag_worsening`) for tracts whose equity score is *currently* trending negative year-over-year.
- **Difference from Fragile:** Worsening = already declining today; Fragile = projected to *cross a tier boundary* by 2027.

### Neighbor Mean Equity Score
- **What it is:** The average equity score of a tract's spatial neighbors. Captures spillover and contiguity effects.
- **Variable name:** `neighbor_mean_equity_score`

### Neighbor Mean Headway (Peak)
- **What it is:** Average peak-AM headway of neighboring tracts. Captures network connectivity.

### N Neighbors
- **What it is:** Count of adjacent tracts (queen contiguity). Tracts with fewer neighbors (edges of the county) score differently in the model.

---

## 5 · Modeling

### XGBoost v3
- **What it is:** The gradient-boosted tree model that predicts service deficit from 13 features. Our production model.
- **Performance:** Cross-validated R² = **0.823**.
- **How to explain it:** "Machine learning model that learned what drives transit gaps from historical data. Forecasts what happens to deficit when service changes."

### CV R² (Cross-Validated R-Squared)
- **What it is:** A measure of predictive accuracy, ranging 0 (no skill) to 1 (perfect).
- **Our value:** 0.823 — the model explains 82% of variance in service deficit.
- **How to explain it:** "On unseen tracts, the model gets within 18% of the true value on average. Strong fit."

### SHAP Value
- **What it is:** A method for attributing each feature's contribution to a prediction. Tells us which levers matter most.
- **Top SHAP values in our model:**
  1. Peak AM frequency · 39.6%
  2. Weekend / weekday ratio · 21.7%
  3. Early AM frequency · 6.9%
  4. Rail trip share · also material
- **How to explain it:** "Tells us which knobs the model thinks matter most. Peak frequency is the single biggest one."

### Sprint 2a Composite
- **What it is:** The original baseline equity-score construction (need × access_deficit) from sprint 2a of the project. The *unsimulated* baseline.

### Sprint 2b XGBoost Model
- **What it is:** The deficit-prediction model trained in sprint 2b. The model file shipped in the dashboard (`Sprint2b_XGBoost_v3.pkl`).

### StandardScaler
- **What it is:** A scikit-learn preprocessor that z-scores features. Used by the Ridge regression baseline, **NOT** by XGBoost (which is scale-invariant).
- **Why it matters:** A common bug is to apply scaling before XGBoost prediction — that would corrupt the output. Our simulator skips it.

---

## 6 · Simulator Mechanics

### Scenario
- **What it is:** A complete specification of: (1) which levers change, (2) by how much, (3) on which tracts.
- **How to explain it:** "An if-statement: 'IF we add 2 buses/hr to peak service in Critical tracts, THEN what happens?'"

### Delta
- **What it is:** A change applied to a lever's baseline value. Example: `{"freq_peak_am_tph": 2.0}` means "+2 trips/hour at peak."
- **How to explain it:** "How much you're moving the knob from where it is today."

### Target
- **What it is:** A direct target value for a lever, overriding whatever the baseline is. Used for the "Weekend Parity" preset (`weekend_weekday_ratio = 0.80`).
- **Difference from Delta:** Delta is *change* (+2 tph). Target is *destination* (set ratio to 0.80, regardless of current).

### Tract Filter / Scope
- **What it is:** Which tracts the scenario's deltas apply to. Options: All 504, Critical only, High + Critical, Fragile only, or a custom GEOID list.
- **How to explain it:** "Where the policy lands — countywide, or just on the urgent neighborhoods."

### Proportional-Change Approach
- **What it is:** The math used to translate a deficit prediction into an updated equity score:
  ```
  ratio = scenario_deficit / baseline_deficit
  new_access_deficit = composite_access_deficit × ratio
  new_equity = composite_need × new_access_deficit
  ```
- **Why this approach:** Self-consistent regardless of scale mismatches between training and current data. Documented in the simulator docstring.
- **How to explain it:** "We don't predict the equity score directly — we predict the change, then apply that change to the existing baseline. Robust against drift."

### Tier Reassignment
- **What it is:** After the equity score is updated, each tract is re-binned into a tier using fixed cutoffs from the baseline.
- **Edge case (now fixed):** When `tier_before` was previously recomputed via the same cutoff logic, boundary tracts could flip — making the Critical row sum to 52 vs. the true 51. **Fix:** `tier_before` now uses the baseline's stored `equity_tier` column directly.

### Headway Auto-Derivation
- **What it is:** When the user changes a frequency lever, headway is auto-derived as `60 / frequency`, since the two move together.
- **Cap:** Headway capped at 120 min when frequency ≤ 0 (matches training data convention for "no service").

### Clamping
- **What it is:** Bounding all features to their observed historical range before prediction, to prevent the model from extrapolating beyond what it learned.

---

## 7 · Scenario Outputs / KPIs

### Tier Upgrades
- **What it is:** Number of tracts that moved to a *better* tier after the scenario.
- **How to explain it:** "How many neighborhoods got upgraded out of their current red/orange/yellow."

### Tier Downgrades
- **What it is:** Number of tracts that moved to a *worse* tier. Should be 0 for any well-designed policy.

### Tracts Improved
- **What it is:** Number of tracts whose equity score got better (deficit went down) — even if they didn't cross a tier boundary.
- **How to explain it:** "Total benefit reach — how many tracts saw any improvement, even small."

### Tracts Worsened
- **What it is:** Number of tracts whose score got worse. A policy with worsened tracts should be examined carefully (often a budget reallocation effect).

### Avg Wait Saved (per Trip, Peak AM)
- **What it is:** Average minutes of expected wait time saved per bus trip across affected tracts, at peak AM.
- **How it's computed:** `wait_saved = (headway_before − headway_after) / 2`. Deterministic; based on the uniform-arrival assumption that expected wait = headway / 2.
- **How to explain it:** "Direct rider impact, in minutes per trip. Math, not a model."

### Max Wait Saved
- **What it is:** The largest per-trip wait time saved among any single tract. Highlights the "best case" delivered by the policy.

### Ridership Change (%)
- **What it is:** Projected percentage change in ridership after the policy, county-wide.
- **How it's computed:** `% ridership change = elasticity × % frequency change`. Aggregated across affected tracts.
- **Elasticities used:** 0.65 (frequency, APTA midpoint), 0.40 (weekend service, TCRP), 1.20 (rail substitution multiplier).
- **Caveat:** This is an **elasticity proxy**, not a farebox-data forecast. Defensible directional estimate, not a guaranteed number.

### N Tracts Ridership Up
- **What it is:** Count of tracts where projected ridership goes up. A high count = broad benefit; a low count with high % = concentrated benefit.

### Tier Shift Matrix
- **What it is:** A 4×4 table showing how many tracts moved from each Before-tier to each After-tier. Rows = before, columns = after.
- **Diagonal:** Tracts that didn't change tier.
- **Below diagonal (left):** Tracts that improved (green in the app).
- **Above diagonal (right):** Tracts that worsened (red in the app, ideally empty).
- **Row totals:** Should match baseline tier counts (51 Critical, etc.).

### Headline (Scenario Summary)
- **What it is:** The single sentence at the top of every scenario output. Built dynamically — prefers "X tracts moved out of Critical" if any did, else "X tier upgrades," else "X tracts improved."

---

## 8 · Network Analysis

### city2graph
- **What it is:** Python library that converts a transit network into a graph (nodes = stops, edges = service connections).
- **Use in the app:** Powers the Network Analysis tab.

### NetworkX
- **What it is:** Python library for graph algorithms (shortest-path, centrality).
- **Use in the app:** Computes travel time and stop-level centrality from the city2graph network.

### Closeness Centrality
- **What it is:** A measure of how reachable a node is from all other nodes in the network. High closeness = "well-connected stop."

### Betweenness Centrality
- **What it is:** A measure of how often a node lies on the shortest path between other nodes. High betweenness = "bottleneck stop." Removing it fragments the network.

### Travel Time to Downtown
- **What it is:** Shortest-path travel time (in minutes) from each tract to Downtown Government Center, over the transit network.
- **How to explain it:** "How long it takes to get downtown using the bus + rail. Not driving — transit-dependent travel."

### Problem Routes
- **What they are:** Bus routes ranked by their headway × number of Critical/High tracts served. The top 15 are surfaced in the Priority Routes tab.

---

## 9 · Recommendations Engine

### Single-Lever Intervention
- **What it is:** A scenario that changes only ONE lever, applied to a specific tract or scope. The atomic unit of the recommendations engine.

### Intervention Catalog (8 candidates)
- **What it is:** The 8 single-lever interventions that the recommendations engine evaluates per tract. Examples:
  - +1, +2, +4 buses/hr at peak
  - +1, +2 buses/hr early AM
  - Weekend ratio → 0.6, 0.8
  - +5 pp rail share

### Per-Tract Ranking
- **What it is:** The recommendations engine runs all 8 interventions on the queried tract, sorts by equity improvement, and displays the top results with wait saved, ridership change, and tier shift.

### County-Wide Ranking
- **What it is:** For each of the 8 interventions, applied to ALL Critical tracts, how many tracts moved out of Critical? The output is a single sorted table — your prioritized investment list.

---

## 10 · Data Sources & Standards

### GTFS (General Transit Feed Specification)
- **What it is:** The industry-standard data format for transit schedules. Every transit agency publishes one.
- **Snapshot used:** Miami-Dade, March 24, 2026. 123 routes, 6,954 stops, 972K stop-events.

### APTA (American Public Transportation Association)
- **What it is:** The U.S. public-transit industry trade group. Source of the *Understanding Transit Ridership Dynamics* report we cite for elasticities.

### TCRP (Transit Cooperative Research Program)
- **What it is:** A federally funded research program that publishes peer-reviewed transit reports.
- **Specific source used:** TCRP Report 95, Chapter 9 — *Transit Pricing and Fares* + service-elasticity literature review.

### Frequency Elasticity = 0.65
- **What it is:** APTA midpoint estimate. A 10% increase in peak frequency drives a 6.5% increase in ridership.

### Weekend-Service Elasticity = 0.40
- **What it is:** TCRP estimate. Weekend service has lower elasticity because of trip-purpose mix (less commuting).

### Rail Substitution Factor = 1.20
- **What it is:** Multiplier applied to rail-mode shifts. Rail trips are longer than bus trips, so a mode-shift produces a larger ridership impact than a same-magnitude bus change.

### 500m Walking Buffer
- **What it is:** The radius used to spatially-join GTFS stops to census tracts. A tract "is served by" a stop if the stop falls within 500 meters of the tract boundary.
- **Why this number:** Standard transit-planning convention; roughly a 6-minute walk.

---

## Quick Reference · Term-to-Tab Map

| Tab | Key Terms |
|-----|-----------|
| **Overview** | Equity Priority Score, Priority Tier, Critical/High/Moderate/Low |
| **Tract Explorer** | GEOID, Composite Need, Composite Access Deficit, Fragile, Worsening, Neighbor Mean Equity |
| **Simulate Policy** | Scenario, Delta, Target, Lever, Tract Filter, Proportional-Change, Tier Shift Matrix, KPIs |
| **Scenario Comparison** | Tier Upgrades, Tracts Improved, Avg Wait Saved, Ridership Change |
| **Recommendations** | Single-Lever Intervention, Per-Tract Ranking, County-Wide Ranking |
| **Priority Routes** | GTFS, Problem Routes, 500m Walking Buffer |
| **Network Analysis** | city2graph, NetworkX, Closeness, Betweenness, Travel Time to Downtown |
| **Alerts** | Fragile, Worsening, Trend Variables |
| **About** | XGBoost v3, CV R², SHAP, APTA, TCRP, Elasticity values |

---

## Tips for Using This Glossary

- **During the demo:** keep the *How to explain it* lines memorized for the top 10 terms. Those are the words that come out of your mouth.
- **In the report:** use the *What it is* + *How it's computed* sections — they're audit-grade.
- **For Q&A:** if a Deloitte technical reviewer asks "how do you compute X," the math is here.
- **Update discipline:** if you change a number in the code (e.g., a new elasticity value), update this file in the same commit.
