# Lessons Learned — Sprint 2

## Session: March 11, 2026 — Composite Equity Indicators

### Lesson 1: Walking threshold has two distinct use cases
**Mistake:** Originally defined walking threshold as "20 min to reach a transit stop, job, or connection point."
**Correction (from Luna):** Walking 20 min to a transit stop defeats the purpose of transit. Two separate thresholds needed:
- Walk-to-job: 20 min (direct commute — reasonable)
- Walk-to-transit: 5-10 min (connector — must be short or transit fails)
**Rule:** Always distinguish walk-to-destination from walk-to-transit when setting thresholds.

### Lesson 2: Indicator saturation invalidates composite scores
**Mistake:** Time Tax (99.6% at max), Service Coverage (86% at max), and Temporal Mismatch (86% at zero) had almost no variance, making them effectively constants in the composite.
**Root cause:** Definitions were too binary — "does transit match auto?" (almost never) or "does block have a stop?" (almost never for 86% of blocks).
**Fixes applied:**
- Time Tax: changed from "match auto" to "reach viable job threshold (10K jobs)"
- Service Coverage: two-tier (blocks with stops use GTFS metrics; blocks without use transit_jobs as proximity proxy)
- Temporal Mismatch: three-tier (served blocks, transit-nearby blocks, no-transit blocks)
**Rule:** Before computing any indicator, check its variance. If std < 0.10 or >90% of values cluster at one point, the indicator lacks discriminating power and needs redesign.

### Lesson 3: Check ACS-to-GeoPackage geographic alignment before assuming 100% merge
**Issue:** GeoPackage covers the MPO planning area (36,507 blocks across 522 tracts) but ACS covers Miami-Dade county (707 tracts). Only 354 tracts overlap → 55% block match rate.
**Fix:** Fill unmatched blocks with county medians. Document the limitation.
**Rule:** Always verify merge rates when joining datasets from different sources. Don't assume geographic alignment.

### Lesson 4: Think like a data scientist, not a machine (Luna's recurring feedback)
**Pattern:** Tendency to apply formulas mechanically without questioning whether the output makes sense in the real world. E.g., "transit dependency = no-vehicle + poverty + low transit" without deeply reasoning about what each criterion means for an actual person.
**Rule:** For each indicator, write down the real-world story first ("A person in this block wakes up, has no car, and..."). Then derive the formula from the story, not the other way around.

### Lesson 5: Don't move forward without required materials
**Pattern:** Starting work before verifying all data is available.
**Rule:** At the start of any data task, list all required inputs. Verify each exists and is accessible. If any is missing, STOP and ask.

### Lesson 6: When asked a data question, check the actual data
**Pattern:** Giving approximate answers from memory instead of querying the actual dataset.
**Rule:** When the user asks about specific data values, always run a query. Never estimate or recall — verify.

### Lesson 7: Always get confirmation before building
**Pattern:** Luna shares a plan direction, I present the approach, then immediately start coding without waiting for her to confirm or adjust. This has happened multiple times.
**Rule:** After presenting a plan or approach, STOP and wait for explicit confirmation ("yes", "go ahead", "proceed") before writing any code. The plan phase exists so Luna can catch issues early — skipping it defeats the purpose. This is especially important for refactors or directional changes where Luna may want to adjust the approach.

### Lesson 8: Stay on task — don't go on tangents
**Pattern:** Was asked to build the tract-level indicators notebook. Spent excessive time on the validation/sanity-check cell (neighborhood mapping) instead of finishing the core task and handing it off.
**Rule:** Complete the core deliverable first. Validation is important but secondary. If an investigation starts consuming more effort than the main task, stop, note the finding, and move on. The user can direct deeper investigation if they want it.

### Lesson 9: Never hardcode values you can derive from data
**Pattern:** Hardcoded Census tract GEOIDs for neighborhoods (guessed from memory) instead of deriving them from the actual spatial data we already had loaded.
**Rule:** If the data exists in the project, query it. Don't hardcode IDs, coordinates, or values that can be computed. This applies to ALL identifiers, thresholds, and reference values.

### Lesson 10: A question is not a green light — wait for explicit confirmation
**Pattern (recurring):** Luna asks a question ("should we drop them?", "what's your plan?"). I answer the question AND immediately start implementing — without waiting for Luna to say "yes, go ahead."
**Root cause:** Treating the question as implicit approval. It is not. Luna is gathering information to make a decision. My job is to give her the analysis; her job is to decide.
**Rule:** After answering a question or presenting a recommendation, STOP. Do not write code, do not modify files. Wait for an explicit green light ("yes", "do it", "proceed", "go ahead"). This rule applies even if the change seems obvious or low-risk. No exceptions.

### Lesson 11: Census API sentinel values are valid numbers — they won't be caught by `errors='coerce'`
**Mistake:** Assumed `pd.to_numeric(col, errors='coerce')` would handle missing data from Census API. But Census returns -666666666 (missing estimate) and -999999999 (missing MOE) as actual integers, which parse as valid numbers.
**Impact:** Trend slopes computed via polyfit were astronomical (max 199 million) because a single sentinel (-666M) dominated the regression across 5 years.
**Rule:** After ANY Census API pull, explicitly replace sentinel values with NaN: `df[col].replace([-666666666, -999999999], np.nan)`. Do this BEFORE any computation. Never trust that `errors='coerce'` handles all bad data — it only catches non-numeric strings.

### Lesson 12: Understand what GTFS service_id represents before computing ratios
**Mistake:** Divided weekday arrivals by 5 assuming GTFS gives Mon-Fri combined. GTFS service_id already represents ONE day's schedule. Dividing by 5 made the weekend/weekday ratio 5x too high (median 2.7 instead of ~0.5).
**Rule:** Before writing GTFS computations, verify what each field represents. `service_id` ties to a single day pattern in `calendar.txt`. Each trip appears once per service_id regardless of how many days that service runs.

### Lesson 13: Validate output data distributions, not just shapes
**Mistake:** Notebook ran without errors, output shape looked right (507 tracts × 80 columns), but 4 critical data quality bugs existed. Only found them because Luna uploaded the CSV for review.
**Rule:** After generating any output dataset, check distributions (min/max/median/std) of key columns — especially computed features. A trend slope of 199 million or a ratio of 2.7 should be impossible. Add automated sanity checks that flag values outside expected ranges.
