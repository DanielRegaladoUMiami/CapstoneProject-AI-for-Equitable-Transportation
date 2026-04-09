# Sprint 3 — Deferred Features

Files in this folder are preserved work that is **not used in the v1 simulator** but may be re-enabled in v2.

## Sprint3_Need_OLS_Coefficients.json

**Purpose:** Local linearization for need-side stress-test scenarios (e.g., "what if poverty rises 5pp in fragile tracts by 2027?"). Maps (delta_poverty, delta_no_vehicle) → delta_composite_need.

**Why deferred:** v1 simulator only exposes transit-service parameters that a transit agency can directly control. Demographic variables (poverty, no-vehicle households) are forecast outputs from the ACS TimeSeries model, not policy levers. They flow into `projected_need_2027` as fixed baseline inputs.

**If re-enabling:** Review for circularity before use — `composite_need` was constructed from these same features in Sprint 2a, so the OLS (R²=0.817) is partially fitting a formula to its own components. Recommend using the Sprint 2a composite formula weights directly instead of the OLS regression, which would be both more transparent and more honest.

**Author:** Daniel (Apr 6, 2026). Quarantined Apr 9 per team decision.
