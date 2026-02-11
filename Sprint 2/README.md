# Sprint 2: Model Design & Analysis

**Duration:** February 21 – March 27 (5 weeks)  
**Sprint Review:** March 27  
**Technical Complexity:** High | **Business Impact:** High

## Objective

Design and validate interpretable baseline predictive models that identify current transit accessibility gaps and anticipate emerging equity issues, enabling the prioritization of geographic areas for targeted transit interventions.

## Sub-Sprints

### 2a · Feature Engineering (Feb 21 – Mar 6)

- Engineer demographic features: income levels, population density, car ownership rates, age distribution
- Engineer transit features: stop density per area, route frequency, average headway, service hours
- Create equity composite indicators (e.g., access score combining multiple dimensions)
- Integrate demographic and transit features at appropriate geographic level
- Feature selection: correlation analysis, variance checks, domain relevance

> **★ DELIVERABLE (Mar 6):** Validated feature set ready for modeling.

### 2b · Baseline Modeling (Mar 7 – Mar 20)

- Build regression models to estimate transit demand and accessibility outcomes
- Apply time-series analysis to capture evolving service needs and demand trends
- Identify geographic areas at higher risk of future accessibility and equity gaps
- Evaluate model performance: RMSE, R², cross-validation, out-of-sample testing
- Interpret results: identify top drivers of inequity from model coefficients/feature importance

### 2c · Validation & Documentation (Mar 21 – Mar 27)

- Sensitivity analysis to understand which features most influence equity outcomes
- Validate model results against observed transit patterns and domain assumptions
- Rank and prioritize geographic zones for transit intervention with rationale
- Document model methodology, performance metrics, and interpretation

> **★ SPRINT 2 REVIEW (Mar 27):** Present model results, geographic priorities, and insights linking predictions to policy-relevant decisions.

## Deliverables

| # | Deliverable | Status |
|---|---|---|
| 1 | Baseline predictive model outputs with documented performance metrics | ⬜ |
| 2 | Ranked geographic zones for transit intervention with supporting rationale | ⬜ |
| 3 | Interpretable insights linking model results to equity-focused decision-making | ⬜ |
