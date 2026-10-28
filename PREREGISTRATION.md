# Ofrenda — Frozen Design and Pre-Registration

**Status:** FROZEN, awaiting human go
**Frozen at:** 2026-10-27 23:40 IST
**Hard deadline:** 2026-11-01 12:29 IST (Oct 31, 23:59 PDT) — **4 days 13 hours remaining**
**Entry:** Hacktoberfest Open-Source AI Challenge, Week 4 — "Ghost in the Machine"

> Nothing in the Analysis Plan below may be altered after the first outcome is observed.
> Additions are permitted only if timestamped before the probe completes, and must be
> logged in §10.

---

## 1. What the project is

Ofrenda reconstructs an abandoned open-source project as a mind — commits as memory,
issues as arguments, docs as self-image — lets you interview it, and then forecasts when
it died. Revival is epilogue, not the product.

The claim under test: **a project dies years before its last commit.** Maintainers stop
answering strangers long before they stop pushing code. That gap is measurable, and it is
the difference between *abandoned* and *dead*.

The emotional register is elegy, not autopsy. `request/request` did not die of neglect; it
died of maintainer exhaustion while serving millions of dependents. The write-up must not
read as a critique of the people who burned out on it.

---

## 2. Strategic position

The contest allows **one win per challenge**, so category breadth buys odds, not prizes.
Judging weights writing quality most heavily. Therefore breadth is entered, but only
differentiated categories are *aimed* at.

| Category | Prize | Decision | Reasoning |
|---|---|---|---|
| Best Use of TabPFN | $200 | **Aimed** | Small-n tabular forecasting is TabPFN's exact regime; the death-forecast is load-bearing |
| Best Use of Sentry Agent Tracing | $100 | **Aimed** | Cheap to wire; the debugging narrative is the submission, not the dashboard |
| Best Use of Gemma | $200 | Entered, not aimed | "Ran Gemma locally" is the most crowded pool in the challenge |
| Best Use of Auth0 | $100 | **Withdrawn** | A local YAML consent file does the same job in ten lines — fails the "unavoidable" test |
| Best Use of Browserbase | $100 | **Withdrawn** | archive.org's CDX API returns JSON; a headless browser is ornamental here |
| Arduino | $200 | **Withdrawn** | Requires physical hardware |
| Remaining 13 | — | Entered only if genuinely used | See §9 |

The withdrawals are not a setback to the submission. Applying the "unavoidable, not
ornamental" test in public and publishing the count *is* the thesis of the write-up.

---

## 3. Corpus and sampling

| Parameter | Value |
|---|---|
| Target n | 300 repositories |
| Dead cohort | `pushed:<2021-01-01 stars:>100 archived:false` |
| Archived stratum | ≥ 60 of 300, split **40 train / 20 held out for validation** |
| Alive controls | `pushed:>2025-06-01` — prevents a model that can only recognise corpses |
| Age floor | Repos created after 2012 (issue data before this is unreliable or migrated) |
| Authentication | `gh auth token` — 5,000 core/hr, 30 search/min, verified |

**`archived:true` is the only non-opinion ground truth available.** It is also selected —
owners archive what they care about — so it is treated as a stratum, not as a clean sample.
Archival status is a **label source and must never enter the feature schema.**

### Cost model (corrected)

The label cannot be computed from one endpoint. `/issues/comments` returns comments on pull
requests as well, so without a join to issue metadata the label degrades to "responded to
anything," and PR review comments count as answering strangers — which is not the thesis.

- `/issues?state=all&since=` → issue author, `created_at`, filter `pull_request`
- `/issues/comments?since=` → comment author, timestamp

≈ 18,000 calls for 300 repos ≈ **3.5–4 hours** at 5,000/hr.

**Fetch in stages:** comments first (labels need only these), compute labels, then fetch
issue metadata only for repos clearing a coverage threshold. Bail out of empty corpses
before paying for them.

---

## 4. Labels — two cumulative binaries

At reference date `T`, outcome window `[T, T+18 months]`. Maintainer = issue comment author
with association `OWNER | MEMBER | COLLABORATOR`, excluding bots.

| Label | Definition |
|---|---|
| **ALIVE** | A maintainer commented on an issue inside the window |
| **GHOSTING** | No maintainer issue response, but some activity (commits, bot, or community) |
| **DEAD** | No maintainer issue response and no activity at all |

Two stacked binary targets, not a 3-class label:

- `y₁ = P(not ALIVE)` → reported as **P(≥GHOSTING)**
- `y₂ = P(DEAD)` → reported as **P(≥DEAD)**

Monotonicity is enforced post hoc by isotonic projection. **The shaded band between the two
curves is the ghosting interval** — a reading, not a class. Its width answers "how long was
this abandoned before it died?"

*Implementation note:* if `y₂` is instead fitted conditionally on `not ALIVE`, monotonicity
holds by construction and isotonic projection becomes a no-op check. Either formulation is
acceptable; report the monotonicity violation rate before projection.

**Derive is a pure function over cached NDJSON.** Raw issue and commit events are cached at
fetch time; labels are computed separately. This makes relabelling free and allows competing
label definitions to be tested against one fetch. Aggregates are the expensive thing to
retract, so store events, not features.

---

## 5. Feature schema

Five decay signals, all computable from a window that **ends at T**.

| Feature | Definition | Trap |
|---|---|---|
| `release_cadence_decay` | Releases in trailing 365d ÷ prior 365d | Many dead repos have zero releases ever — needs a `never_released` indicator |
| `days_since_last_human_commit` | Windowed at T, bot commits excluded | **Near-leaky.** Strongest feature, and the one that can make the thesis unfalsifiable |
| `median_issue_response_latency` | Maintainer first reply, trailing 365d | Undefined where issues are disabled |
| `docs_vs_code_divergence` | `days since last docs change ÷ days since last code change`, clipped | Underspecified until operationalised — this is the definition |
| `backlog_slope` | Slope of open **human-opened** issues, trailing 365d | Bot-opened issues (dependabot) will corrupt it |
| `bus_factor` | Author concentration, top-1 share | **Structural control** — in A, B′, C. Never in B |

**Excluded from the schema, with reasons:** archival status (label source), stars and forks
(popularity, not decay — invites "popular projects die slower," which is trivial), language
(not a decay signal), anything observed after T.

### The leakage trap, stated plainly

`days_since_last_human_commit` is nearly the label in disguise. Include it carelessly and
the model learns "recent commit → alive," which is trivially true and *refutes* rather than
supports the thesis. The ablation in §6 exists to separate the two claims.

---

## 6. Models and analysis plan

Four fits on identical data, **LOPO cross-validation** (leave-one-project-out — required
because multiple reference dates per repo would otherwise leak a project's own time points
across the split).

| Model | Features | Question it answers |
|---|---|---|
| **A** | Code only | How well does the code signal predict? |
| **B** | Social only | How well does the social signal predict? |
| **B′** | Social + bus factor | Does structure add anything beyond social? |
| **C** | All | Descriptive ceiling |

### Comparison hierarchy — fixed-sequence gatekeeping

Not a pairwise matrix. Six tests at α=0.05 gives ~26% family-wise error, spending α to learn
nothing.

1. **Primary (confirmatory):** **B vs A**, α = 0.05. Effect-size threshold ΔAUC ≥ 0.07.
2. **Secondary (confirmatory):** **B′ vs B**, tested at α = 0.05 **only if the primary is
   significant**. Fixed-sequence gatekeeping controls FWER at 0.05 without taxing a test
   already earned.
3. **Tertiary (pending human decision):** **B′ vs A**. Required to support any sentence of
   the form *"the social signal survives structural controls."* If not registered, that
   claim is struck from the write-up. It must not appear in the abstract as though tested.
4. Everything else is **descriptive**: C, per-stratum AUC, calibration, band width.

### Statistical instruments

- **Paired DeLong test** for correlated AUCs — not a bare threshold. The models are fit on
  identical data, so paired comparison is far more sensitive than comparing point estimates.
  An unpaired SE at n=300 is ~0.045, so ΔAUC 0.07 sits *inside the noise band* if read
  naively.
- **Brier Skill Score** against the base rate (`1 − Brier/Brier_ref`), not raw Brier. Raw
  Brier is uninterpretable without a reference.
- **Reliability diagram** — Brier conflates calibration with resolution.
- **Bootstrapped band width** (≥1,000 resamples, LOPO-aware). The band is a *difference* of
  two probabilities, so calibration error compounds in the subtraction. Without an interval
  the band is decoration.

### Stratified reporting

Bus factor is a feature for modelling and a stratum for *reporting*. After fitting, split
predictions by bus-factor quartile and report AUC per quartile. This surfaces the likely
interaction — social signals dominate in solo projects, structural ones in teams — without
paying for it in n.

---

## 7. External validation

`archived:true` is GitHub's own death certificate, and the only ground truth in this project
that is not an opinion.

| Test | Reference date | Purpose |
|---|---|---|
| **Primary** | `T = archive_date − 36 months` | Window closes 18 months *before* declaration, leaving genuine uncertainty |
| **Sanity check** | `T = archive_date − 18 months` | Window ends at declaration — near-tautological, boundary check only |

**20 of the 60 archived corpses are held out entirely.** Validating on repos that appear in
training would be in-sample and worth nothing.

---

## 8. The corpse: `request/request`

Deprecated June 2020, still receiving pushes in 2024, never archived. Org-owned, ~25.5k
stars, created 2011, ~145 open issues.

**Excluded from the training corpus.** Its forecast is out-of-sample and its interview cites
the deprecation notice and the unanswered issues as artifacts.

- **Pre-registered reference-date grid:** 1 January, 2015 → 2023 (nine points). Which years
  are plotted is a researcher degree of freedom; the grid is fixed before any curve is seen.
- **The maintainer is not named.** The ghost speaks as *the project*, not the person. This
  removes the puppeting problem and is the single most important ethical decision here.
- Expected shape: ALIVE through ~2019, the band opening around the deprecation announcement,
  DEAD by ~2023. If the curve does not show that, the model is wrong and we say so.

---

## 9. Probe — 20 repositories, ≤ 90 minutes

The probe's job is to break the pipeline, not confirm it. A random sample tests the happy
path; spend the 20 on the cases that will kill the full pull.

| Group | n | Purpose |
|---|---|---|
| Issues disabled | 3 | `median_issue_response_latency` undefined — how bad is the hole? |
| Zero releases ever | 3 | `release_cadence_decay` divide-by-zero path |
| Bot "maintainer" | 3 | Bot-detection filter correctness |
| Single commit | 3 | Degenerate history |
| `archived:true` | 3 | Label-source join correctness |
| Known-alive controls | 5 | If all 20 return DEAD, the label is broken, not the corpus |

**Outputs:** per-feature coverage table · label distribution · monotonicity violation rate ·
**wall-clock per repo**.

**Frozen before printing any label.** No eyeball-tuning of thresholds after the first look.

**Bail criteria:** median wall-clock > 4.5 min/repo means 300 repos > 22 hours and the plan
is already dead. Descope ladder: 300 → 150 → 100 → single-cohort, decided by the probe, not
by optimism.

---

## 10. Decisions log

Record of what changed, and why. The corrections matter more than the original plan.

| # | Position | Outcome |
|---|---|---|
| 1 | Predict a death *date* via TabPFN | **Rejected.** TabPFN is a prior-fitted in-context model; n=1 gives it nothing to condition on |
| 2 | Find a corpus of repos with known death dates | **Rejected.** No such label exists. "Death" is an opinion, not a field |
| 3 | Predict an observable binary instead | **Adopted.** "Did a maintainer respond in 18 months" is retrievable and is the social-death signal |
| 4 | 3-class ordinal ALIVE/GHOSTING/DEAD | **Withdrawn** in favour of two cumulative binaries. Ordinal also raised label complexity while cutting n — the two changes pulled against each other |
| 5 | n=150 × 5 features | **Rejected.** Rows and feature count are independent axes; 300 × 5 dominates unless complete-case analysis is what was meant |
| 6 | Aim at TabPFN + Gemma | **Rejected.** Aims at the two most crowded pools. Replaced by TabPFN + Sentry |
| 7 | Aim at Auth0 + Browserbase | **Withdrawn by both parties.** Both fail the "unavoidable, not ornamental" test |
| 8 | GraphQL for the corpus pull | **Withdrawn.** Node-cost based; blows the budget on heavily-commented corpses |
| 9 | One REST endpoint suffices for labels | **Rejected.** `/issues/comments` includes PR comments; the join is mandatory for a thesis-valid label |
| 10 | ΔAUC 0.07 as the decision rule | **Corrected.** A threshold gives an effect size, not inference. Paired DeLong required |
| 11 | Raw Brier score | **Corrected** to Brier Skill Score + reliability diagram |
| 12 | `T = archive − 18mo` as validation | **Corrected.** Ends the window at the moment death was declared — near-tautological. `−36mo` is the real test |
| 13 | Archived corpses as training data only | **Corrected.** 20 held out; validating in-sample is worthless |
| 14 | Bus factor as feature *or* stratum | **Resolved:** feature for modelling, stratum for reporting. Forces the B′ fit |

---

## 11. Known limitations — stated before a judge finds them

1. **Two DEAD definitions coexist.** Declared (archived) and inferred (silence). The model
   learns a blend, and the write-up must say so.
2. **The archived stratum is selected.** Owners archive what they care about; `request` is
   deprecation-dead and was never archived.
3. **Missingness correlates with age.** Pre-2012 repos have unreliable issue histories.
4. **Issue features are undefined** where issues are disabled — not missing at random.
5. **n=300 is small** for three latent states; confidence intervals will be wide and must be
   reported as intervals, never as point estimates.
6. **The label is a proxy** for social death, not death itself.
7. **The interview half is n=1.** One corpse, one conversation. That is a story, not evidence,
   and should not be presented as the latter.

---

## 12. Schedule

| Window | Work |
|---|---|
| Tonight | Probe (20 repos), freeze results |
| Day 1 | Full pull, feature extraction, cached NDJSON |
| Day 2 | Four fits, DeLong, BSS, reliability, band charts |
| Day 3 | Interview layer, demo, deploy |
| Day 4 | **Write-up.** Heaviest-weighted criterion — it gets a full day, not the leftovers |

The post skeleton starts on Day 1, not Day 4. Writing is what wins this, and writing
compressed into the final hours reads like it.

---

## 13. Waiting on the human

1. **Go / no-go** on the probe. Everything above is frozen until then.
2. **Confirm the 40/20 archived split** and that archival status stays out of the schema.
3. **Decide on B′ vs A.** Register it as tertiary-confirmatory, or strike *"survives
   structural controls"* from the write-up. Both are defensible; silence is not, because the
   claim will otherwise drift into the abstract untested.

---

## 14. Cleanup note

`marigold/package.json` at the workspace root is a leftover stub from the abandoned
person-reconstruction concept. It contains four script entries pointing at files that were
never written. Delete or repurpose when the real scaffold lands.
