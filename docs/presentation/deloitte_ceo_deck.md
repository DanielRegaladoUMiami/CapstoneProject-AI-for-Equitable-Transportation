---
marp: true
theme: default
paginate: true
size: 16:9
style: |
  section {
    background: #FFFFFF;
    color: #1D1D1F;
    font-family: -apple-system, "SF Pro Display", "SF Pro Text", system-ui, sans-serif;
    padding: 80px 100px;
    font-size: 26px;
    line-height: 1.45;
    letter-spacing: -0.01em;
  }
  h1 { font-size: 54px; font-weight: 600; letter-spacing: -0.03em; color: #1D1D1F; margin: 0 0 28px 0; }
  h2 { font-size: 36px; font-weight: 500; letter-spacing: -0.02em; color: #1D1D1F; margin: 0 0 24px 0; }
  h3 { font-size: 22px; font-weight: 500; color: #6E6E73; text-transform: uppercase; letter-spacing: 0.08em; margin: 0 0 16px 0; }
  strong { color: #1D1D1F; font-weight: 600; }
  em { color: #6E6E73; font-style: normal; }
  .eyebrow { color: #86868B; font-size: 14px; letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 24px; }
  .kpi { font-size: 120px; font-weight: 200; letter-spacing: -0.04em; color: #005587; line-height: 1; margin: 20px 0; }
  .kpi-label { color: #6E6E73; font-size: 20px; }
  .accent { color: #86BC24; }
  .deloitte-green { color: #86BC24; font-weight: 600; }
  .muted { color: #86868B; }
  .rule { border: none; border-top: 1px solid #D2D2D7; margin: 24px 0; }
  footer { color: #86868B; font-size: 13px; letter-spacing: 0.08em; }
  ul { list-style: none; padding: 0; }
  ul li { padding: 10px 0; border-bottom: 1px solid #F5F5F7; }
  ul li:last-child { border-bottom: none; }
  .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 60px; }
  section.title { background: #000000; color: #FFFFFF; }
  section.title h1 { color: #FFFFFF; font-size: 68px; }
  section.title .eyebrow { color: #86BC24; }
  section.kpi-slide { text-align: center; }
footer: "University of Miami · Deloitte Capstone · April 2026"
---

<!-- _class: title -->
<!-- _paginate: false -->

<div class="eyebrow">Deloitte × University of Miami · Capstone</div>

# Miami-Dade<br>Transit Equity Simulator

<div class="muted" style="margin-top:48px;font-size:22px">A decision tool for where a transit dollar buys the most equity.</div>

<div style="margin-top:120px;color:#86868B;font-size:16px">Daniel Regalado · MSBA 2026</div>

---

<div class="eyebrow">The Problem</div>

# Transit investment decisions<br>are made without equity in the loop.

<div class="rule"></div>

Planners know *where* buses run.

Politicians know *where* the votes are.

**Neither knows where a dollar of service buys the most equity.**

---

<!-- _class: kpi-slide -->

<div class="eyebrow">Miami-Dade today</div>

<div class="kpi">51</div>
<div class="kpi-label">census tracts in <strong>Critical</strong> equity priority</div>

<div style="margin-top:60px;color:#6E6E73;font-size:20px">
of 504 tracts countywide · home to Miami-Dade's most transit-dependent residents
</div>

---

<div class="eyebrow">What we built</div>

# One tool. Four questions.

<div class="rule"></div>

<ul>
<li><strong>Where</strong> are the equity gaps? &nbsp; · &nbsp; <em>Overview + Tract Explorer</em></li>
<li><strong>What</strong> if we intervene? &nbsp; · &nbsp; <em>Simulate Policy</em></li>
<li><strong>Which</strong> policy wins? &nbsp; · &nbsp; <em>Scenario Comparison</em></li>
<li><strong>Where</strong> do we deploy dollars? &nbsp; · &nbsp; <em>Priority Routes + Recommendations</em></li>
</ul>

<div class="muted" style="margin-top:48px;font-size:18px">Built on 504 census tracts, 123 bus routes, ~7,000 stops, ~1M stop-events.</div>

---

<div class="eyebrow">The engine</div>

# An XGBoost model that understands<br>*service* — wrapped around an index<br>that understands *need*.

<div class="two-col" style="margin-top:40px">
<div>
<h3>Technical</h3>
<ul>
<li><strong>XGBoost v3</strong> · cross-validated R² = 0.82</li>
<li>13 service + demographic features</li>
<li>Proportional-change propagation to equity score</li>
<li>Fixed-cutoff tier reassignment</li>
</ul>
</div>
<div>
<h3>Business</h3>
<ul>
<li>Re-scores every tract in under a second</li>
<li>Answers "what if" without new data collection</li>
<li>Uses <strong>APTA / TCRP</strong> elasticities for ridership</li>
<li>Deterministic wait-time math · no black box</li>
</ul>
</div>
</div>

---

<!-- _class: title -->

<div class="eyebrow">Demo</div>

# Live walkthrough

<div style="margin-top:60px;font-size:24px;color:#D2D2D7">~8 minutes · huggingface.co/spaces/DanielRegaladoCardoso/miami-transit-equity</div>

<div style="margin-top:80px;color:#86BC24;font-size:16px;letter-spacing:0.12em">OVERVIEW → EXPLORER → SIMULATE → COMPARISON → RECOMMENDATIONS → ROUTES</div>

---

<div class="eyebrow">What the demo showed</div>

# Three policies, three answers.

<div class="rule"></div>

<div class="two-col">
<div>
<h3>Peak frequency boost</h3>
<p style="font-size:38px;font-weight:300;color:#005587;margin:0">+2 bus/hr</p>
<p class="muted">on Critical tracts</p>
<p>Largest wait-time reduction per tract.</p>
</div>
<div>
<h3>Rail modal shift</h3>
<p style="font-size:38px;font-weight:300;color:#005587;margin:0">+10 pp</p>
<p class="muted">Metrorail mode share</p>
<p>Largest county-wide ridership lift.</p>
</div>
</div>

<div style="margin-top:30px">
<h3>Combined strategy</h3>
<p>Moves the most tracts out of Critical. <strong>This is the policy we'd recommend.</strong></p>
</div>

---

<div class="eyebrow">Why this matters to Deloitte</div>

# A defensible, repeatable method —<br>not a one-off dashboard.

<div class="rule"></div>

<ul>
<li><strong>Reusable</strong> · the equity composite + simulator pattern ports to any metro with ACS + GTFS</li>
<li><strong>Auditable</strong> · every number traces to a model, a cutoff, or a cited elasticity</li>
<li><strong>Client-ready</strong> · built to explain to a mayor, not just a data team</li>
<li><strong>Extensible</strong> · cost-per-service-hour overlay and live GTFS refresh are next</li>
</ul>

---

<div class="eyebrow">What this tool is <em>not</em></div>

# Honesty before scale.

<div class="rule"></div>

<ul>
<li>Not a ridership forecaster &nbsp; · &nbsp; <em>elasticity proxy, not farebox data</em></li>
<li>Not a cost-benefit analyzer &nbsp; · &nbsp; <em>service hours and cost are next sprint</em></li>
<li>Not a live dashboard &nbsp; · &nbsp; <em>GTFS snapshot March 2026; refresh is quarterly</em></li>
</ul>

<div class="muted" style="margin-top:40px;font-size:18px">Stated up front so nobody oversells the tool.</div>

---

<div class="eyebrow">What's next</div>

# From prototype to platform.

<div class="rule"></div>

<ul>
<li><strong>Cost layer</strong> · operating cost per service hour → impact per dollar</li>
<li><strong>Live feed</strong> · quarterly GTFS refresh, automated baseline update</li>
<li><strong>Second metro</strong> · prove the method ports — Tampa or Orlando pilot</li>
<li><strong>API</strong> · scenario endpoint other Deloitte tools can call</li>
</ul>

---

<!-- _class: title -->
<!-- _paginate: false -->

<div class="eyebrow" style="color:#86BC24">Thank you</div>

# Questions.

<div style="margin-top:120px;color:#86868B;font-size:16px">
Daniel Regalado &nbsp; · &nbsp; dxr1491@miami.edu<br>
huggingface.co/spaces/DanielRegaladoCardoso/miami-transit-equity
</div>
