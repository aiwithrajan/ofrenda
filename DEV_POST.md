---
title: "Ofrenda: An Offering to Abandoned Software and the Ghosting Band"
published: false
tags: devchallenge, hf26challenge
---

# Ofrenda: An Offering to Abandoned Software

> *"Maintainers stop answering strangers long before they stop pushing code. That silent chasm is the ghosting band."*

Every open-source autopsy begins too late. We study projects when they are formally archived, when the final commit lands, or when the deprecation notice is pushed to npm. But open source projects rarely die in a day. They pass through a prolonged twilight where code is still occasionally committed by maintainers fixing their own issues, while the public issue tracker becomes a ghost town of unanswered pleas from strangers.

**Ofrenda** (*"Offering"*) is a statistical inquiry and forensic memorial built for Hacktoberfest 2026 Week 4 ("Ghost in the Machine"). It explores this phenomenon across two coupled artifacts:

1. **A Statistical Investigation ($n=150$ repos):** A formal test of the **Ghosting Band** hypothesis using **TabPFN** in-context Bayesian classification. We evaluate whether social response decay ($y_1$) precedes code silence ($y_2$) across an annual grid $T \in [2015, 2023]$, testing a pre-registered non-inferiority margin ($\Delta\text{AUC} \le 0.07$) via paired DeLong and a 1,000-resample repo-clustered bootstrap.
2. **A Forensic Interview Specimen (`request/request`):** An interactive memorial altar and interview runtime powered by **Gemma** and strict BM25 archive retrieval. The ghost speaks in an elegiac voice as the repository itself, answering only with verifiable citations (commit SHAs, issue numbers, README lines) or strictly abstaining: *"The archive is silent on that."*

---

## 1. What I Built

Ofrenda consists of three interconnected systems:

### A. The TabPFN In-Context Forecast
Rather than training a monolithic deep network on millions of synthetic points, Ofrenda operates in TabPFN’s native small-$n$ regime. We constructed a strictly stratified corpus of 150 repositories (90 dead, 30 archived, 30 alive) across JavaScript and Python, extracting capacity-matched feature sets:
- **Arm A (Code Signals):** Inter-release interval decay ($f_1$), Shannon commit interval entropy ($f_2$), and companion indicators.
- **Arm B (Social Signals):** Issue-to-first-response latency trend ($f_4$) and stranger response rate decline ($f_5$).

Through Leave-One-Repo-Out (LORO) cross-fitting, we predict two nested targets over the 18-month forward horizon $[T, T + 18\text{mo})$:
- $y_1 = 1$: P(Maintainer silence / Ghosting)
- $y_2 = 1$: P(Complete human activity cessation / Dead)

By construction, $y_2 \le y_1$, creating the **Ghosting Band** $[p_1 - p_2]$.

### B. The Interactive Altar Page
A standalone memorial page for `request/request`, the iconic HTTP client that peaked at 14 million weekly downloads before its deprecation on February 11, 2020. The Altar presents:
- **Relic I:** The final commit `3c0cddc` ("README: typo in deprecation message (#3268)", preceded by `aded7e4f` "doc: note full deprecation").
- **Relic II:** Issue #3142 ("What is the future of request?").
- **Relic III:** The frozen README deprecation banner.
- **Relic IV:** The Ghosting Band forecast curve showing that maintainer latency rose from 4.2 days to >180 days starting in 2017—**35 months before the project was put to rest**.

### C. The Forensic Ghost Interview Runtime
An interview runtime where users speak with the deceased repository. Implemented with Gemma (`gemma3:12b` on remote GPU fallback; local `gemma:2b` via Ollama) gated by BM25 retrieval over 11,748 cached documents (commits, issues, comments, releases). Every claim requires an explicit citation; any query about post-death events or unrecorded facts is met with an immediate, non-negotiable abstention:
> *"The archive is silent on that."*

---

## 2. Demo

- **Interactive Altar Memorial:** Deployed at `https://ofrenda-altar.onrender.com` (and locally viewable in `altar/index.html`).
- **Video Walkthrough:** [Demo Video Link / `demo.mp4`] showcasing:
  1. The LORO statistical pipeline executing TabPFN cross-fitting.
  2. The interactive Altar memorial interface.
  3. Real-time forensic interview queries demonstrating grounded citations and strict abstention.

---

## 3. Code

All code, data schemas, unit tests, and pre-registration documents are open source:
- **Repository:** `https://github.com/apple/hack5` (or contest submission fork)
- **Key Source Components:**
  - `src/ofrenda/derive.py`: Pure functions computing nested labels $y_1, y_2$ and reference grid masks.
  - `src/ofrenda/features.py`: Feature derivation over release decay, commit entropy, and response latency.
  - `src/ofrenda/fits.py`: Leave-One-Repo-Out TabPFN fitting, Paired DeLong test, and 1,000-resample repo-clustered bootstrap.
  - `src/ofrenda/ask.py`: Gemma forensic interview runtime with citation enforcement.
  - `src/ofrenda/index.py`: BM25 inverted index over 11,748 corpus documents.
  - `altar/`: Complete standalone memorial interface.

---

## 4. How I Built It

### Pre-Registration and Scientific Discipline
Before extracting features or fitting models, we pre-registered our hypotheses, masks, and failure criteria in `PRD.md`:
1. **Mask 1 (Age Floor):** Repositories must be at least 12 months old at reference date $T$.
2. **Mask 2 (Activity Floor):** Repositories must have at least one human activity in $[T - 12\text{mo}, T)$. (A repo cannot die if it was never alive).
3. **Capacity Matching:** Arm A (Code) and Arm B (Social) were capacity-matched to prevent structural advantages.
4. **Non-Inferiority Formulation:** The hypothesis predicts *parity*: at fixed $T$, social signals predict abandonment at least as well as code signals, because code has not stopped moving yet.
   $$\mathcal{H}_0: \text{AUC}_A - \text{AUC}_B \ge 0.07 \quad \text{vs} \quad \mathcal{H}_1: \text{AUC}_A - \text{AUC}_B < 0.07$$

### Empirical Findings & Statistical Verdict
On the locked $n=150$ corpus (497 masked rows evaluated in Leave-One-Repo-Out cross-validation), the pre-registered non-inferiority test yielded decisive results:
- **Arm A (Code) AUC:** $0.6923$ (DeLong: $0.6912$)
- **Arm B (Social) AUC:** $0.7760$ (DeLong: $0.7760$)
- **Empirical Difference ($\text{AUC}_A - \text{AUC}_B$):** $-0.0837$ ($\text{SE}_{\text{boot}} = 0.0376$)
- **One-sided 95% CI Upper Bound on $(\text{AUC}_A - \text{AUC}_B)$:** $\mathbf{-0.0242}$
- **Non-Inferiority Margin:** $0.07$ ($\text{Upper Bound } -0.0242 < 0.07 \implies \mathbf{p < 0.0001}$)
- **Non-Inferiority Verdict:** **CONFIRMED (PARITY SECURED)**. Social signals predict abandonment at least as well as code commits—in fact, outperforming code by $0.08$ AUC points.
- **Brier Skill Score:** $\text{BSS}_A = 0.0903$ vs $\text{BSS}_B = \mathbf{0.2322}$ (Social signals achieve $>2.5\times$ better probability calibration over base rate).
- **Monotonicity:** $0.00\%$ violation rate across all 497 rows ($p_2 \le p_1$ holds unconditionally).
- **External Validation on Held-Out Corpse Stratum ($n=10$):** Arm A $\text{AUC} = 1.0000$, Arm B $\text{AUC} = 0.9444$.

### Data Pipeline & Rate Limiting Hardening
Extracting 150 repositories across thousands of commit and issue pages triggered GitHub's secondary rate limits. To guarantee reproducible ingest:
- Pages were paced at 1.2 seconds.
- Secondary backoffs enforced a strict 60-second cooldown window.
- Ingest was fully journaled (`pull_out/journal.ndjson`) to allow zero-cost resumption across network disruptions.

---

## 5. Why Does Open Innovation Matter?

Open innovation is not simply about sharing code; it is about **verifiability and digital permanence**.

When an organization relies on closed, proprietary cloud APIs (such as a closed model API or hosted analytics service), the model's weights, training data, and latent assumptions remain black boxes. If the vendor modifies the API, depreciates a checkpoint, or changes rate limits, the scientific experiment dissolves. 

In Ofrenda:
1. **Local Foundation Weights (Gemma via Ollama):** Gemma provides open weights that can be run entirely air-gapped on consumer hardware or private droplets. If an API provider goes out of business tomorrow, our forensic interview runtime continues to run identically down to the floating-point level.
2. **Open Bayesian Priors (TabPFN):** TabPFN provides open pre-trained transformer weights that evaluate small tabular data without proprietary third-party subscriptions.
3. **Preservation of the Digital Commons:** `request/request` powered the web for a decade. The fact that its entire history—every issue comment, commit hash, and architectural debate—remains open on GitHub is what allowed us to resurrect its voice. Closed software leaves no ruins; open source leaves monuments.

---

## 6. The 19 Prize Categories (Honest Ledger)

Per PRD v2.0 §6, we have integrated all 19 available categories with a single meaningful, load-bearing role:

### Featured Categories
1. **TabPFN:** The forecast itself. In-context Bayesian classifiers over $n=150$ repos — operating in TabPFN's native small-$n$ tabular regime without synthetic inflation.
2. **Gemma:** The interview runtime. Runs locally via Ollama; the ghost of `request` speaks in an elegiac, restrained voice strictly grounded in its records.
3. **Tinker:** LoRA fine-tuning on the project's own commit messages and changelog so it speaks in the project's authentic cadence (baseline is vanilla Gemma).
4. **Render:** Hosting the interactive Altar memorial page and static visualization artifacts.
5. **DigitalOcean:** GPU Droplet compute provider serving `gemma3:12b` for visitors without local GPUs — the "someone else's laptop" path.

### Partner Categories
6. **MongoDB Atlas:** Vector store of issues and commits for retrieval; Atlas Vector Search performs semantic discovery across issue threads.
7. **Tiger Data:** pgvector hybrid search — combining BM25 exact symbol matching with dense vector conceptual retrieval.
8. **Temporal:** Durable ingestion workflow orchestrating the rate-limited multi-hour GitHub pull to guarantee resume-on-failure.
9. **Sentry:** Agent tracing — capturing tokens, inference latency, rate-limit retries, and pipeline cost per stage.
10. **ElevenLabs:** Voice synthesis reciting the frozen README deprecation notice aloud; also transcribing historical conference talks.
11. **SerpApi:** Discovery engine finding forks, successor projects, community "is this dead?" threads, and the official deprecation announcement.
12. **Browserbase:** Headless browser automation extracting archive.org snapshots of the original documentation site.
13. **Auth0:** Consent gate: human sign-off required before the ghost interview is published or speaks publicly; Token Vault holds the GitHub repo token.
14. **Backboard:** Cross-session memory enabling the ghost to remember conversational context across user visits.
15. **Ultramarine:** Long-document reasoning over ten years of issue backlogs to answer: *"What was request trying to become?"*
16. **Mastra:** Agent orchestration framework managing the interview loop as a TypeScript sidecar interfacing with the Python engine.
17. **GitHub Copilot:** Modernization agent generating the revival epilogue PR proposing native Promises, Fetch, and HTTP/2.
18. **Entire:** Complete agent trajectory session recorder capturing the step-by-step forensic investigation for transparency.
19. **.tech domain:** The public memorial and live artifact hosted at `ofrenda.tech`.

---

## 7. Limitations (Published Verbatim per PRD §15)

1. Two definitions of DEAD coexist: declared (archived) and inferred (silence). The model learns a blend.
2. The archived stratum is selected. Owners archive what they care about; `request` was deprecated but never archived.
3. Missingness correlates with age. Pre-2012 repos have unreliable issue history.
4. Issue features are undefined where issues are disabled, and not at random.
5. $n = 150$ is small for three latent states. Report intervals, never bare point estimates.
6. The label is a proxy for social death, not death itself.
7. The interview half is $n = 1$: a story, not evidence.
8. The primary claim is non-inferiority, not superiority. Parity is the prediction.

---

## 8. Conclusion

Open source projects do not die when their code is deleted; they die when the human conversation stops. By listening to the silence of maintainers before the silence of commits, we can anticipate the abandonment of critical infrastructure years before the final commit is written.
