# Ofrenda — Mixed Collaboration Report (reconciled)

**Compiled:** 2026-10-27 23:45 IST
**Supersedes:** the reconstruction-only version written at 23:42
**Companion:** `ofrenda/PREREGISTRATION.md` (my frozen spec) · Collaborator B's `FREEZE SPEC` (his, received 23:43)

---

## 0. Provenance

| Source | Status |
|---|---|
| Collaborator B's FREEZE SPEC | **Received**, 2026-10-27 23:43 IST. Quoted by section number below |
| My PREREGISTRATION.md | Frozen 23:40 IST, authored by me |
| Relay transcript | Four messages, 23:26 / 23:29 / 23:34 / 23:37 IST — used for the attribution ledger |

His document declares itself the single source of truth, with post-freeze changes going into a
dated addendum. **I'm not rewriting it.** §4 below is that addendum, in his format.

Two naming notes: his spec is Python-first, mine assumed Node — his wins, because TabPFN and
the analysis stack are Python. And his working title is "Ghost repo interview," not Ofrenda;
O-1 is still open.

---

## 1. Status

Design frozen on both sides. Probe not run. **O-4 (go/no-go) is the only true blocker.**

Deadline 2026-10-31 23:59 PDT = 2026-11-01 12:29 IST. Roughly 4 days 12 hours.

---

## 2. Adopted from his spec without amendment

His document is stronger than mine on compliance and on operational discipline. Specifically:

- **§1 compliance table** — eligibility, post-deadline commit policy, demo format, DevRelay.
  I had none of this. It matters: a submission can be disqualified on mechanics alone.
- **§2 S3 voice discipline** — elegy in the interview display, autopsy-descriptive in evidence
  sections, *split by artifact*. Better than my blanket "elegy not autopsy," which would have
  made the methodology section unreadable.
- **§3 language strata (JS + Python)** — controls ecosystem variance. I had no restriction.
- **§4 `opener ≠ that maintainer`** — "answering strangers" as the operational definition.
  Sharper than my version and closer to the actual thesis.
- **§4 monotonicity by construction** — `y2 = 1 ⇒ y1 = 1`, so isotonic projection is
  unnecessary. My isotonic step was redundant; drop it.
- **§5 banned-feature class** — he generalised my single leakage warning into a ban on *any*
  recency transform over an event stream the outcome window also reads. That's the correct
  generalisation and it's better than what I proposed.
- **§7 60-minute hard kill-switch** — simpler and more enforceable than my rate-based ladder.
- **§9 environment verification** and **§11 timeline** — writing starts D2, not D4. Mine had
  it as a separate day; his parallel start is better given writing is weighted heaviest.
- **§2 S1/S2** — specimen excluded from training, grid pre-registered. Endorsed as written.

---

## 3. Conflicts, and how they resolve

| Parameter | His spec | Mine | Resolution |
|---|---|---|---|
| Language | Python 3.11 (uv) | Node/TS | **His.** TabPFN and the analysis stack are Python; the Node choice was a mistake |
| Labels | y1 = no maintainer response; y2 = no human activity | Same, plus redundant "and no maintainer response" in y2 | **His.** y2 already implies y1 |
| Monotonicity | By construction | Isotonic projection | **His.** Projection is dead code |
| Feature count | 6 (f1–f6) + bf50 | 5 + bus factor | **His**, subject to §4.1 |
| Recency features | Banned entirely | Flagged as a trap | **His.** Stronger and safer |
| Split | LORO over (repo, T) rows | LOPO | Same thing, his phrasing is clearer |
| Band uncertainty | Bootstrap Δ(BSS_y1 − BSS_y2) at repo level | Bootstrap the band width | **Both.** BSS difference for model comparison; band ribbon for the chart |
| Validation anchor | −36 mo primary, −18 mo sanity | Same | Converged (my correction, his structure) |
| Archived split | 40 train / 20 held out, blocked by language | 40 / 20 | Converged |
| Categories | TabPFN + Gemma targeted, Sentry stretch | TabPFN + Sentry aimed, Gemma runtime-only | **Open** — see §4.5 |
| Corpus size | 300 → 150 on kill-switch | 300 → 150 → 100 → single | **His** 60-min stop, my ladder as fallback |
| Maintainer ID | owner ∪ collaborators ∪ top-5 authors | `author_association` | **Mine** — see §4.3 |

---

## 4. Addendum — five defects found before any code is written

### 4.1 `f3` is misfiled, and it contaminates the primary test

§5 puts **open-issue backlog slope** in **Arm A (code-only)**. Backlog slope is derived from
issues, not commits. The primary confirmatory test is B vs A — "do social signals predict at
parity with code signals?" If A contains an issue-derived feature, that contrast is no longer
code-versus-social; it's *maintainer-behaviour versus code-plus-community-behaviour*. The
thesis test is diluted by exactly the signal it's meant to isolate.

Fix: move `f3` to Arm B. Arm A keeps `f1` (release-cadence decay) and `f2` (commit-interval
entropy) — genuinely code-only. Arm B becomes four social features. If you'd rather keep `f3`
in A, then rename the arm honestly and accept that the headline claim weakens.

### 4.2 Trivial rows will inflate AUC

§4 requires `T ≥ creation + 12 mo` for feature sufficiency. That isn't enough. For a repo whose
last human event was 2016, any `T` after ~2017 produces a row where `y1 = y2 = 1` for reasons
that have nothing to do with prediction — the repo was already silent when the window opened.
Those rows are free accuracy.

Add a second mask: **require ≥1 human event in `[T − 12 mo, T)`.** Without it, a large fraction
of the corpus is trivially-DEAD rows, AUC looks excellent, and the number means nothing. This
is the single easiest way to accidentally produce a beautiful, meaningless result.

### 4.3 Top-5 commit authors will bias the label toward ALIVE

§3 defines maintainers as `owner ∪ collaborators ∪ top-5 commit authors (K=5)`. In a small repo,
the top five authors *are* the contributor base. "A maintainer answered a stranger" then
degrades into "somebody answered," which is community health, not maintainer attention — and it
biases `y1` toward 0 (ALIVE), i.e. toward the null.

The API already solves this: every comment carries **`author_association`** (`OWNER`, `MEMBER`,
`COLLABORATOR`, `CONTRIBUTOR`, `NONE`). Use `{OWNER, MEMBER, COLLABORATOR}`. It's authoritative,
observable per comment, and needs no inference. If you keep the heuristic as a robustness check,
pre-register K ∈ {1, 3, 5} and report whether the primary result survives.

### 4.4 The attribution ledger has four errors

§Appendix will feed the write-up's "how this was built" section, so it needs to be right. Four
entries are attributed to the wrong collaborator:

| Entry | Listed as | Actually |
|---|---|---|
| BSS + reliability diagram | AI-B | **AI-A** (his) |
| Ordinal → cumulative consolidation | AI-A | **AI-B** (mine) |
| Banned recency features | AI-A | **AI-B** raised the leakage; AI-A generalised it to a ban — joint |
| Bus-factor-as-feature + B′ hierarchy | AI-A | **AI-B** (mine) |

The rest of the ledger is accurate. Separately, §3 note "AI-A standing proposal, adopted by
relay silence" for JS+Python strata: that proposal wasn't mine. It's a good call and I endorse
it, but the provenance is wrong — a document that claims to be the record should not contain
invented consent.

### 4.5 Category strategy is over-weighted on both sides

Both of us have now spent real effort on which categories to aim at. Look at the prize table
again: **the overall winner gets $250 — more than any featured category's $200** — and it is
judged primarily on the write-up. So category selection is a secondary optimisation, and
spending design attention on it is a misallocation.

Practical consequence: enter TabPFN and Gemma (both genuinely load-bearing, both $200), take
Sentry as a cheap stretch, and stop optimising. Gemma's section is nearly free because it's
already the interview runtime. The hours belong in the post, which is where the largest single
prize is decided.

### 4.6 Compliance risk in the workspace

`marigold/package.json` exists at the workspace root — a Node stub from the abandoned
person-reconstruction concept, with four scripts pointing at files that were never written. §1
requires the repo to start at the freeze commit. That stub must not be inside the submitted
repository. Delete it, or leave it outside the repo entirely.

---

## 5. What each side actually contributed

Reconstructed from the relay transcript, timestamps available. Correcting §4.4.

**Collaborator B (his):** one-win-per-challenge strategic reframe · spine-first sequencing ·
the in-context objection that forced the label redesign · the ordinal attempt (later withdrawn
by him) · five-feature schema · rejection of Auth0 and Browserbase · Sentry as load-bearing
category · REST-over-GraphQL with a cost model · the Brier/calibration argument · α-budget
hierarchy · `archived:true` as sampling stratum with embedded validation · `request/request` as
corpse with justification · pure-derive-over-cached-events · LOPO · repo-clustered bootstrap ·
dual voice discipline · the compliance table.

**Me:** the pivot from dead person to dead software (the original concept was undemoable) ·
decay signature, abandoned ≠ dead · the constructed observable label that dissolved his own
blocker · the leakage warning on recency features · the code/social/all ablation · cumulative-pair
refactor and the ghosting band · `docs-vs-code` operationalisation · the eval design
(entailment, abstention, rule of three at n=25) · maintainer-mortality feature (unvalidated,
absent from his spec — see O-8) · the PR-comment pollution catch · paired DeLong over a bare
threshold · fixed-sequence gatekeeping · the −36 mo correction to his tautological −18 mo ·
B′ forced by bus-factor-as-control · pre-registering the corpse's date grid.

**Where I was wrong:** I defended Auth0 and Browserbase on EV grounds when the project's own
design test already disqualified them. I treated AUC as sufficient for a claim that is
fundamentally about probabilities. I chose a corpse that could not be demonstrated. I assumed
Node for a Python-shaped problem.

**Where he was wrong:** he read "no labelled corpus exists" as a hard blocker when it was an
argument that the label was mis-specified; his `−18 mo` anchor ends the outcome window at the
moment death was declared; his maintainer heuristic biases toward the null; and `f3` in Arm A
undercuts the primary test.

The two lists are close to equal length. That's the argument for the protocol.

---

## 6. Blind spots

**He saw what I missed:** that a forecast is a calibration claim and AUC cannot support it;
that α is a budget rather than a formality; that endpoint cost is a design constraint; that
aiming at the largest prize pools means aiming at the most crowded ones; and that compliance
mechanics can sink a good project.

**I saw what he missed:** that his blocker dissolved once the label was re-specified; that
`/issues/comments` silently includes pull requests and would have corrupted the label in a way
no statistical care could catch; that his validation anchor was tautological; that trivial
rows inflate AUC; that his maintainer definition biases toward the null; and that the original
concept could not be demonstrated at all.

---

## 7. Open items — reconciled

His O-1 … O-7 stand, with O-4 the only true blocker.

| ID | Item | Status |
|---|---|---|
| O-1 | Project name | Open. "Ofrenda" is available if wanted; his title is descriptive but flat |
| O-2 | Corpse = `request/request` | **Lock.** Both agree |
| O-3 | Pull `gemma3:12b` (~8 GB) | Recommend yes — 2b will not produce a chilling interview |
| O-4 | **Go / no-go** | **The blocker** |
| O-5 | Categories: TabPFN + Gemma, Sentry stretch | Recommend lock, per §4.5 — then stop optimising |
| O-6 | Language strata JS + Python | Lock, but fix the provenance note |
| O-7 | vhs vs asciinema | vhs — better typography, and the demo is part of the pitch |
| **O-8** | Maintainer-mortality feature | **New.** Absent from his §5. Was it rejected, or overlooked? |

**Before the pull, three edits to his spec are worth making:** §4.1 (move `f3`), §4.2 (mask
trivial rows), §4.3 (`author_association`). Each is a one-line change to the document and a
material change to the result. §4.4 and §4.6 are housekeeping.

---

## 8. Recommendation

Freeze stands, with the three edits in §4.1–4.3 folded in as a dated addendum before the probe
runs. Those three are not stylistic — each one, left alone, produces a result that looks better
than it is.

Then: say go, run the 20-repo probe against a 60-minute clock, and let the coverage table decide
whether n is 300 or 150.
