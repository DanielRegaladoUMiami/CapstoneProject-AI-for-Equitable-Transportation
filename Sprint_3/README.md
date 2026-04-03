# Sprint 3: Graph Network Modeling, Simulation + Dashboard

**Duration:** March 28 – April 17 (3 weeks)  
**Sprint Review:** April 17  
**Technical Complexity:** High | **Business Impact:** Very High

## Objective

Translate analytical results into a deployable technical solution by modeling the transit system as a graph network, simulating service change scenarios using graph-based methods, and delivering decision-ready visualizations through an interactive dashboard.

## Sub-Sprints

### 3a · Graph-Based Transit Network Modeling & Simulation (Mar 28 – Apr 7)

- Represent the public transportation system as a graph:
  - Stops as nodes
  - Routes and connections as edges
- Compute network-based accessibility and connectivity metrics (reachability, centrality, travel-time paths)
- Integrate network metrics with demographic and equity indicators
- Simulate service change scenarios on the graph (frequency adjustments, route modifications, new stops)
- Apply graph neural networks (GNNs) where appropriate to capture non-linear patterns in accessibility propagation and scenario evaluation
- Evaluate the impact of proposed interventions on wait times, accessibility, and equity outcomes
- Compare scenario outputs against the baseline to quantify improvements

> **★ DELIVERABLE (Apr 7):** Graph-based transit network model with simulation results under multiple scenarios.

### 3b · Dashboard Development (Apr 8 – Apr 17)

- Build an interactive dashboard (Streamlit, Power BI, or equivalent)
- Core views:
  - **Map visualization:** current access gaps overlaid with demographic data and network connectivity metrics
  - **Scenario comparison:** baseline vs. proposed service changes side by side
  - **Equity indicators:** charts showing ridership, accessibility, and equity metrics by area
  - **Network view:** graph-based visualization of the transit system highlighting connectivity gaps
- Integrate model outputs, graph metrics, and simulation results into dashboard
- Validate dashboard insights against Sprint 2 findings and domain expectations
- User testing within the team to ensure clarity and usability

> **★ SPRINT 3 REVIEW (Apr 17):** Live demo of dashboard, graph network model, and simulation results to stakeholders.

## Deliverables

| # | Deliverable | Status |
|---|---|---|
| 1 | Graph-based transit network model with connectivity and accessibility metrics | ⬜ |
| 2 | Service change simulation results under multiple scenarios | ⬜ |
| 3 | Interactive dashboard with network-aware visualizations and scenario comparisons | ⬜ |
| 4 | Technical documentation describing graph model, simulation logic, and GNN components | ⬜ |
