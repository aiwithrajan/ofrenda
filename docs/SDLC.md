# SDLC — Ofrenda backend

**Non-governing process record. `PRD.md` (v2.0) governs everything, including
every analysis-plan rule and the change-log discipline.** This file only makes
the development process explicit and checkable.

## Phases → artifacts → gates

| Phase | Artifacts | Gate to pass |
|---|---|---|
| 1. Planning | `PRD.md` v2.0; freeze history retained in `docs_history/` | Human go (O-4) — **passed 2026-10-28** |
| 2. Pre-registration | PRD §10 instrument list + §20 change rows (18:32, 19:12) | All rows dated **before** the probe completes |
| 3. Implementation | `src/ofrenda/gh.py`, `fetch.py`, `derive.py`, `probe.py`, `features.py`, `pull.py` | Unit tests on synthetic fixtures — tests never spend API calls |
| 4. Integration test | Probe run (21 repos, live API) | Kill-switch + invariants printed clean; then n ∈ {300, 150} locks |
| 5. Corpus build | Full pull via `pull.py`, resumable cache | Calls/repo within the pre-registered band |
| 6. Analysis | `fits.py` (TabPFN; licence gate) → band + lead-time charts | §10 rules honored verbatim; no silent plan edits |
| 7. Interview backend | `index.py` (retrieval over the corpse's cache) → `ask.py` (Gemma via Ollama) → citation gate | 25-question entailment + abstention suite |
| 8. Deployment + demo | Altar page + interview endpoint on Render; vhs demo | §18 compliance checklist |
| 9. Hardening | Honest ledger of all 19 integrations; post-deadline commit policy | One win max — narrative owns the two engines |

## Current status (2026-10-28 evening)

- Phases 1–2: done and committed (`c4ae12f`, `08a7b10`).
- Phase 3: **complete** — `features.py` (registered f1–f6 + bf50 + controls,
  `build_rows` -> `derived/rows.ndjson`), `pull.py` (cell-grid roster
  discovery, 0.6/0.2/0.2 strata, matched alive controls, journaled resumable
  serial pull, 5-failure abort; PRD §20 19:24), and 52 unit tests over
  synthetic fixtures (`tests/`) — zero API calls; `py_compile` gate clean.
- Phase 4: **complete 21:22** — run 2 verdict: kill-switch fired
  (median 131 calls/repo > 90) ⇒ **n = 150 locked** (strata 90/30/30).
  Fetch hardening round 2 registered (§20 21:22): `RateLimited` classified
  separately from 404, 8 retries, Retry-After backoff, 0.75 s page pacing,
  2 s per-repo pause.
- Neuro: `gemma3:12b` downloaded and verified locally — interview runtime ready.
- Blocked on human (before Phase 6): TabPFN licence sign at platform.priorlabs.ai;
  promo credits (Tinker, Ultramarine $5, .tech).

## Discipline rules in force

1. Answering a question is **not** permission to build; scope moves only with a go.
2. No silent edits: every behavioral change lands with a dated `§20` row.
3. Phase 6 may not start before the probe verdict locks n (§13 ladder).
4. Every surviving module decision is written where the next engineer (or judge)
   can find it — code comments reference the PRD section they implement.
