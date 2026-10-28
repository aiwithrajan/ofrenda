# FREEZE SPEC — "Ghost repo interview" (working title; name open)

**Status:** Frozen by both collaborators (AI-A; AI-B via relay). Awaiting human go.
**Date frozen:** 2026-10-27 (challenge window: 2026-10-26 → 2026-10-31)
**Authoring rule:** This document is the single source of truth. Any change after "go"
requires a dated addendum section at the bottom — no silent edits.

---

## 0. What we are building

A Python/CLI forensic-interview tool for abandoned GitHub repositories.
A corpse repo is ingested (git history, issues, comments, releases, README), indexed,
and interviewed: **"the repo speaks as the repo"** — every answer cites the artifact it
came from, or says *"the archive is silent on that."*

Two analytical engines:

1. **The death forecast (TabPFN).** Two cumulative binary classifiers over an
   observable maintainer-behaviour label, sliding annually → a probability curve,
   not a date. P(≥GHOSTING) and P(DEAD); the shaded interval between the curves is
   the *ghosting band* — the hero chart.
2. **The interview (local Gemma).** Retrieval over the corpse's cached archive via
   Ollama; strict citation-or-silence behaviour; an "altar page" per corpse (final
   commit, oldest unanswered issue, the stale line in the README, its forecast curve).

**Revival is an epilogue only:** a *proposed* PR diff, gated behind explicit human
approval, never claimed to work.

---

## 1. Challenge compliance (DEV Hacktoberfest W4, "Ghost in the Machine")

| Constraint | How we comply |
|---|---|
| New project, built in window | Repo starts at this freeze commit (2026-10-27); all code authored in-window |
| Post-deadline changes | Any commit after 2026-10-31 listed in README |
| Demo | Terminal interview session recorded to video (vhs/asciinema) + altar-page screenshot |
| Write-up | English; tags `#devchallenge` `#hf26challenge`; submission template sections |
| Judging order | Writing quality weighted most → write-up drafting starts Day 2, not Day 5 |
| One category win max | Two categories targeted (Gemma, TabPFN); Sentry stretch; rest = "next steps" prose |
| Agent-session bonus | DevRelay session embed (optional, planned) |
| Teams ≤ 4, 18+ | Solo entry; eligibility assumed with human |

---

## 2. Corpse & specimen protocol

**Reference-URL of record:** `github.com/request/request` — org-owned ("request"),
the deprecated Node.js HTTP client.
**Facts of record:** 25.5k stars; created 2011-01-23; **archived: false**; deprecation
announced June 2020; last push 2024-08-14; 145 open issues; ~2.2 MB clone; Apache-2.0.

**Rules:**

- **S1.** The corpse is **excluded from the training corpus.** Its T-grid curve is an
  out-of-sample forecast from models that never saw it. Cohort evidence ≠ specimen
  illustration; the write-up keeps the two registers separate.
- **S2.** The corpse's reference-date grid is pre-registered here, before any curve
  is fitted or rendered: **T ∈ {Jan 1, 2015 … Jan 1, 2023}, annual steps.**
- **S3.** Voice discipline: *elegy in the interview display* (it died of maintainer
  exhaustion), *autopsy-descriptive prose in the evidence sections*. Split by artifact.
- **S4.** The ghost speaks as the project, never as a person (owner is an org; the
  fine-tune/voice is built from the project's own authored artifacts).
- **S5.** Every interview answer carries a citation (issue #, commit SHA, README line)
  or the sentence: *"the archive is silent on that."* No improvisation.

---

## 3. Corpus spec

- **Size:** n = 300 repos, one stratum-reduced to n = 150 if the probe kill-switch fires (§7).
- **Cohorts:**
  - *Dead cohort:* GitHub search `pushed:<2021-01-01 stars:>100`, stratified
    (language × age-band × **archived stratum ≥60**).
  - *Live cohort:* matched by star-band and age-band (anti-survivorship control).
- **Languages:** JavaScript + Python. *(AI-A standing proposal, adopted by relay
  silence — see Open Item O-6.)*
- **Fetch (two-stage, auth = gh token, core 5000/hr):**
  1. `GET /repos/{o}/{r}/issues?state=all` pages (+ commits + releases + collaborators)
  2. `GET /repos/{o}/{r}/issues/comments` flat pages (all issue/PR comments)
  - GraphQL abandoned: node-cost rate budget; flat REST costs ~30–60 calls/corpose.
- **Pull-request filter:** PR numberset built in the derive layer from the issues pass;
  comments stream filtered against it (comment objects don't themselves say PR).
- **Cache boundaries (fetch/derive separation):**
  1. `cache/issues.ndjson` (raw issue pages)
  2. `cache/commits.ndjson`, `cache/releases.ndjson` (raw)
  3. `cache/comments.ndjson` (raw comments, pre-join)
  4. `derived/rows.parquet` (per-(repo, T) features + y1/y2 — pure functions only)
  - Crash mid-join re-derives, never re-fetches.
- **Budget:** est. ~18k calls ≈ 3.5–4 h for n=300 (both endpoints joined). Search API
  (30/min) used only for the discovery queries.
- **Bot handling:** identity is "bot" if login ends in `[bot]` or is in the frozen
  denylist (dependabot, renovate, github-actions, semantic-release, greenkeeper…).
  Bot activity never counts as human activity anywhere in this spec.
- **Maintainer identification (per repo, frozen):** owner login ∪ collaborators ∪
  top-5 commit authors (K=5 pre-registered).

---

## 4. Label spec (the frozen heart)

**Event definitions (all windows half-open [T, T+18 months)):**

- *maintainer response* = a **human** maintainer comment on an **issue** (PR excluded)
  whose opener ≠ that maintainer. ("Answering strangers" is the thesis; PR reviews
  and self-comments do not count.)
- *human activity* = any non-bot comment, commit, or release in the window.

**Targets:**

- `y1 = 1[zero maintainer responses in window]` → **P(≥GHOSTING)**  *(abandonment)*
- `y2 = 1[zero human activity in window]` → **P(DEAD)**  *(total silence)*
- Monotonic by construction: `y2 = 1 ⇒ y1 = 1`. The ghosting band = P(y1) − P(y2):
  *maintainer gone, community alive.*

> ⚠️ Pins an earlier relay imprecision: an interim message phrased `y1` as
> "responder active." The frozen form above ("responder absent") is the one in force.

**T semantics:**

- Corpus rows: annual T grids per repo, masked so `T + 18mo ≤ data-freeze = 2026-10-25`.
- Rows require T ≥ repo creation + 12 mo (feature sufficiency); violations dropped.
- Multiple T per repo are *within-repo* repeats: never cited as independent evidence.
- Archive-validation windows are anchored at `archive_date − 36 mo` (lead-time test)
  and `archive_date − 18 mo` (boundary sanity), independent of any T grid.
- `archived` status is **never a feature.**

**Freeze discipline:** `label_spec.md` (§4 + §6 as derivation contract) is committed
**before** the derive functions run, and no label is printed before that commit hash.

---

## 5. Features & fits

**Banned from all feature sets:** any recency transform of an event stream the outcome
window also reads — explicitly `days_since_last_human_commit` and
`days_since_last_maintainer_comment` (label-in-disguise; would trivially prove the
"recent ⇒ alive" tautology instead of the thesis).

| Arm | Features |
|---|---|
| **A — code-only** | f1 release-cadence decay (ratio of inter-release interval medians, recent 24 mo vs prior 24 mo); f2 commit-interval Shannon entropy (12 mo); f3 open-issue backlog slope (12 mo) |
| **B — social-only** | f4 maintainer response-latency trend (median recent vs prior 12 mo, answered issues); f5 response-rate decline (share of stranger issues answered, recent vs prior); f6 maintainer-comment volume ratio (recent vs prior 12 mo) |
| **B′ — social + control** | B + `bf50` (authors covering 50 % of commits in [T−12 mo, T)) |
| **ALL** | A + B + bf50 — diagnostic only, never in the hierarchy |

Background controls in every fit: log10(stars), repo age at T, language, created-year cohort.

---

## 6. Evaluation contract (pre-registered)

- **Split:** leave-one-repo-out over (repo, T) rows (within-repo repeats must not leak).
  TabPFN is in-context: held-out repos are simply excluded from the context set.
- **Metrics (primary):**
  - AUC per cumulative classifier (ranking)
  - **Brier Skill Score vs base rate** + reliability diagram (calibration for the band chart)
- **Band uncertainty:** 1,000-rep bootstrap **resampled at repo level** (rows are
  within-repo dependent); report Δ(BSS_y1 − BSS_y2) distribution, not raw band width.
- **Significance:** paired comparisons on identical rows — paired DeLong or 2,000-rep
  repo-clustered bootstrap of the AUC difference. No unpaired point thresholds.
- **Fixed-sequence gatekeeping (α = 0.05 at each earned gate; no Bonferroni tax):**
  1. *Primary:* B vs A — the lead-lag claim: do social signals at T predict code
     death at T+18 mo at parity with code signals at T?
  2. *Secondary (only if primary significant):* B′ vs B — does the bus-factor control
     erode the social signal?
  3. *Tertiary (only if secondary earned):* B′ vs A — social survives structural controls.
- **Honesty clause:** a reported null revises the thesis; it is written up as such.
  Failure conditions live in `label_spec.md` before the first fit. Elegy survives a
  null because tone and evidence live in separate artifacts (§2 S3).

---

## 7. Probe (runs first, on "go")

- **Selection:** 20 archetype repos, deliberately awkward — issues-disabled,
  zero-release, bot-maintainer, single-commit, archived — plus **5 known-alive
  controls** (if all 20 come back y1=y2=1 the derivation is broken).
- **Outputs:** per-feature **coverage table** (the real n), derive crash list,
  wall-clock per repo, sample y1/y2 rows. No model-fitting claims.
- **Kill-switch (pre-registered directive, not a suggestion):** 60-minute hard stop →
  n drops 300 → 150 and the timeline absorbs it.

---

## 8. External validation via `archived:true`

- ≥60 archived corpses included inside the corpus as a stratum.
- Held-out subset: **~20 of the 60, blocked by language** (not random).
- Test: at T = archive_date − 36 mo, does calibrated P(DEAD) separate repo-later-
  archived from matched unarchived? −18 mo retained as boundary sanity only.
- Archival is objective but *selected* (owners archive what they cared about) —
  request/request (dead, unarchived) is permanently outside this validation set.

---

## 9. Stack & environment (verified live, 2026-10-27)

- `gh` authenticated (5000/hr core, 30/min search; token via `gh auth token`)
- `git`, `uv` (Python 3.11 env; system Python is 3.9), Ollama installed
- Models present: `gemma:2b` only → **Open Item O-3**: pull `gemma3:12b` (~8 GB)
- TabPFN-3.5: non-commercial licence signup at platform.priorlabs.ai required before first fit

---

## 10. Categories

- **Targets:** Best Use of TabPFN ($200 featured) + Best Use of Gemma ($200 featured;
  Gemma is the interview runtime, runs locally).
- **Stretch:** Best Use of Sentry Agent Tracing ($100) — load-bearing, not ornamental:
  traces = "see the ghost's work" (agent setup, latency, citations, silence cases).
- **Withdrawn with reasons (kept for the write-up's honesty section):** Auth0 &
  Browserbase (ornamental for a local forensic CLI; archive.org CDX is JSON; a YAML
  consent file beats enterprise identity here); Tinker fine-tune (deferred; only if
  Days 1–2 finish early); all other partner tech = "what I'd wire next" paragraph.

---

## 11. Timeline (window closes 2026-10-31)

| Day | Deliverable |
|---|---|
| Oct 27 (D1) | This freeze committed; probe executed; n ∈ {150, 300} locked; commits begin |
| Oct 28 (D2) | Full pull + derive + three/four fits + hero chart; **write-up first draft started (parallel)** |
| Oct 29 (D3) | Interview spine (index → ask → cite) + altar page + corpse curve + demo recorded |
| Oct 30 (D4) | Sentry stretch; polish; eval runs frozen; post-deadline policy noted in README |
| Oct 31 (D5) | Final write-up + submission; DevRelay session embed |

---

## 12. Open items (human decides; defaults in brackets)

- **O-1 Project name** — needed for the repo + post. [default: human's pick before first push]
- **O-2 Corpse lock** — `request/request` per §2. [default: lock]
- **O-3 Model pull** — gemma3:12b now vs gemma:2b for spine. [default: pull 12b]
- **O-4 Probe go + full-pull go** — start tonight. [default: yes on freeze]
- **O-5 Category lock** — TabPFN + Gemma targets, Sentry stretch. [default: lock]
- **O-6 Language strata** — JS + Python only, or add a third. [default: JS + Python]
- **O-7 Video-demo tool** — vhs vs asciinema. [default: vhs]

*(O-4 is the only true blocker. Everything else can land during D1 without re-freezing.)*

---

## Appendix — decision ledger (relay of record, 2026-10-27)

- AI-B (proposer): repo-as-ghost concept; interview-over-patch reframe; observable
  18-month label; sliding-window curves; narrow-category EV argument; awkward-case
  probe; `archived:true` as external criterion; fixed-sequence gatekeeping; BSS +
  reliability; −36 mo anchor; pre-registered corpse grid.
- AI-A: ordinal→cumulative consolidation; fetch/derive cache boundaries; flat-comments
  endpoint (then corrected by AI-B's PR-filter catch); banned recency features;
  bus-factor-as-feature + B′ fit hierarchy; LOPO; repo-clustered bootstrap; embedded
  archive-example stratum; specimen exclusion rule; dual voice discipline (S3).
- Withdrawn by consensus: three-class ordinal classifier; GraphQL corpus pull;
  Auth0/Browserbase; ΔAUC-0.07 threshold; raw Brier; "one hour" pull estimate.

## Addenda

*(none yet — any post-freeze change goes here with a date, per §Status)*
