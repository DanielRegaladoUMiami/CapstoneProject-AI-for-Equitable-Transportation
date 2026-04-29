# Speaker Script · Deloitte CEO Presentation

**Total time:** 20 min · **Demo:** ~8 min · **Slides:** ~12 min
**Pace:** slow, ~110 wpm. Pause after every period. Breathe at every em-dash.

---

## Slide 1 · Title  *(45 sec)*

"Good afternoon. Thank you for the time.

What I'm going to show you today is a decision tool we built for Miami-Dade County transit.

It answers a question that sounds simple, but that no existing tool actually answers: *where does a dollar of transit service buy the most equity?*

I'll spend a few minutes framing the problem and the approach. Then I'll hand you a live demo. Then we'll talk about what it means for Deloitte."

---

## Slide 2 · The Problem  *(90 sec)*

"Transit investment decisions today are made without equity in the loop.

Planners know where the buses run. They have GTFS feeds, on-time metrics, service hours.

Politicians know where the votes are. They have districts, constituencies, public comment records.

But neither of them knows, with any rigor, *where a dollar of service buys the most equity*.

That gap is the reason transit-dependent communities stay underserved — not because anyone chose it, but because nobody measured it.

Our project closes that gap."

---

## Slide 3 · 51 Critical tracts  *(60 sec)*

"This is the number that anchors everything we built.

Fifty-one census tracts in Miami-Dade are in what we call Critical equity priority. That's out of 504 total.

These are the places where two things overlap: the population depends on transit more than anywhere else in the county — and the service they're getting is weaker than the county average.

That's the target list. Every feature in the tool exists to help a planner move tracts *out* of that red category."

---

## Slide 4 · Four Questions  *(90 sec)*

"The app is organized around the four questions a planner actually asks.

First: **where** are the gaps? Overview and Tract Explorer answer that.

Second: **what** happens if we intervene? That's the Simulate Policy tab.

Third: **which** policy actually wins? That's the Scenario Comparison tab, and that's the one I'm proudest of — because that's where executive decisions get made.

Fourth: **where** do we deploy the dollars? Priority Routes and Recommendations translate policy into specific bus lines and specific tracts.

The whole thing sits on 504 tracts, 123 routes, roughly seven thousand stops, and about a million stop-events from the GTFS feed."

---

## Slide 5 · The Engine  *(120 sec)*

"A quick word on what's under the hood — at two levels, because I know this room has both.

For the technical side: we trained an XGBoost model on thirteen service and demographic features. Cross-validated R-squared of point-eight-two. When a user pulls a lever — say, adds two buses per hour at peak — the model re-predicts the service deficit, we propagate that change proportionally to our equity score, and we reassign tiers against fixed cutoffs derived from the baseline distribution.

For the business side: that entire pipeline runs in under a second. It answers *what if* questions without any new data collection. Ridership estimates use published APTA and TCRP elasticities — point-six-five for frequency, point-four for weekend service, one-point-two for rail substitution. Wait-time savings are deterministic math, not a model — so there's no black box on the number that matters most to a city council.

The short version: it's rigorous enough to defend in a technical review, and transparent enough to present to a mayor."

---

## Slide 6 · Demo transition  *(20 sec)*

"The best way to explain the rest is to show you. I'll spend about eight minutes walking through the live app, then come back to why this matters for Deloitte."

---

## DEMO  *(~8 min)*

**Pacing budget per tab:**

- **Overview (60s)** — "Red dots are the 51 Critical tracts. Tier distribution on the right. This is the county at a glance."
- **Tract Explorer (45s)** — Pick `12086000220`. "One tract, full narrative. Demographics, service, routes, network. When a stakeholder asks *why this one*, this is the answer."
- **Simulate Policy (2 min)** — Click S1 (Peak boost). Walk the before/after map. Read the tier shift table: "Notice the Critical row sums to 51 — that matches the baseline. Under this scenario, X tracts moved out of Critical." Then click S4 (Rail shift) and show the contrast.
- **Scenario Comparison (2 min)** — This is the money tab. Pick S1 vs S4. Walk the delta column row by row. "Peak boost moves more tracts out of Critical. Rail shift saves more wait time county-wide. The deltas are colored so the tradeoff is visible at a glance. This is the view an executive uses to make the call."
- **Recommendations (60s)** — Show the county-wide ranking. "For each of eight interventions, how many Critical tracts move out? This is your prioritized investment list."
- **Priority Routes (45s)** — "Top fifteen routes ranked by impact on Critical and High tracts. Policy is abstract; routes are concrete. This is the shortlist."
- **(Skip Alerts, Network Analysis, About unless time permits.)**

---

## Slide 7 · Three policies, three answers  *(75 sec)*

*(Back to the deck.)*

"So what we just saw, summarized: three policies, three different answers.

Peak frequency boost wins on wait-time reduction per tract.

Rail modal shift wins on county-wide ridership lift.

The combined strategy moves the most tracts out of Critical — and that's the policy we'd recommend, if we had to pick one today.

But the point isn't the specific winner. The point is that the tool lets an executive *see* the tradeoff and *defend* the choice."

---

## Slide 8 · Why this matters to Deloitte  *(90 sec)*

"Four reasons this is a Deloitte-shaped asset, not just a capstone.

One: it's reusable. The equity composite and simulator pattern port to any metro with ACS and GTFS. That's most of the United States.

Two: it's auditable. Every number in the app traces to a model coefficient, a published elasticity, or a fixed cutoff. Nothing is hand-waved.

Three: it's client-ready. It's built to explain to a mayor, not just a data team. That's a different design discipline, and it's one your clients will feel the second they use it.

Four: it's extensible. A cost layer and a live feed are the obvious next two sprints — and both are within reach."

---

## Slide 9 · Honesty  *(60 sec)*

"Before I scale anything, let me be explicit about what this tool is *not*.

It's not a ridership forecaster. The ridership number is an elasticity proxy, not farebox data. A real boardings model would be tighter.

It's not a cost-benefit analyzer — yet. Service hours and operating cost aren't in this version. Adding them is the next sprint.

It's not a live dashboard. The GTFS snapshot is March 2026. Refreshing the baseline is a quarterly task.

I'm telling you these things up front. The worst thing we can do with a tool like this is oversell it."

---

## Slide 10 · What's next  *(60 sec)*

"Four next steps, in priority order.

Cost layer — so we can report impact per dollar, not just impact per tract.

Live GTFS feed — quarterly refresh, automated.

A second metro — Tampa or Orlando — to prove the method ports.

And an API — so other Deloitte tools can call the scenario engine directly."

---

## Slide 11 · Close  *(30 sec)*

"Two takeaways.

One: transit equity is measurable, and we measured it.

Two: the hard part wasn't the model. The hard part was designing the tool so a non-technical decision-maker could use it to make a better call.

I'd love your questions."

---

## Backup · if asked

- **Why XGBoost over a neural net?** Data size (~500 tracts, 13 features) — tree models fit this better and retrain fast. A neural net would overfit and lose interpretability.
- **What's the elasticity source?** APTA *Understanding Transit Ridership Dynamics* and TCRP Report 95, Chapter 9.
- **How do you know the tier cutoffs are right?** Sprint 2a used quartile-based tiers on the baseline equity distribution. The cutoffs are fixed, not re-estimated per scenario.
- **What about modes other than bus and rail?** Not in scope. Micro-mobility and paratransit would be separate models.
- **Who validated the equity composite?** Built from ACS variables with documented weights. Sensitivity analysis in the Sprint 2a report.
