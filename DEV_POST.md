*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 4: Ghost in the Machine](https://dev.to/challenges/hacktoberfest-week4-2026-10-26)*

# 🕯️ Ofrenda: The Ghost in the Machine
### *Some projects don't end. They just go quiet.*

> *"Code keeps committing, CI stays green, and bots open PRs — while maintainers stopped answering strangers 771 days ago. That silent twilight is the Ghosting Band."*

Every open-source autopsy begins too late. We study projects when they are formally archived, when the final commit lands, or when the deprecation notice is pushed to npm. But open source projects rarely die in a day. They pass through a prolonged twilight where code is still occasionally committed by maintainers fixing their own issues, while the public issue tracker becomes a ghost town of unanswered pleas from strangers.

**Ofrenda** (*"Offering"*) is an empirical statistical inquiry and forensic post-mortem memorial exploring this phenomenon across two coupled artifacts:
1. **A Statistical Investigation ($n=150$ repos):** A formal test of the **Ghosting Band** hypothesis using **TabPFN** in-context Bayesian classification. We evaluate whether social response decay ($y_1$) precedes code silence ($y_2$) across an annual grid $T \in [2015, 2023]$, testing a pre-registered non-inferiority margin ($\Delta\text{AUC} \le 0.07$) via paired DeLong and a 1,000-resample repo-clustered bootstrap.
2. **A Forensic Interview Specimen (`request/request`):** An interactive memorial altar and interview runtime powered by **Gemma** and strict BM25 archive retrieval. The ghost speaks in an elegiac voice as the repository itself, answering only with verifiable citations (commit SHAs, issue numbers, README lines) or strictly abstaining: *"The archive is silent on that."*

---

## What I Built

Ofrenda consists of three interconnected systems:

### 1. The TabPFN In-Context Forecast
Rather than training a monolithic deep network on millions of synthetic points, Ofrenda operates in TabPFN’s native small-$n$ regime. We constructed a strictly stratified corpus of 150 repositories (90 dead, 30 archived, 30 alive) across JavaScript and Python, extracting capacity-matched feature sets:
- **Arm A (Code Signals):** Inter-release interval decay ($f_1$), Shannon commit interval entropy ($f_2$), and companion indicators.
- **Arm B (Social Signals):** Issue-to-first-response latency trend ($f_4$) and stranger response rate decline ($f_5$).

Through Leave-One-Repo-Out (LORO) cross-fitting, we predict two nested targets over the 18-month forward horizon $[T, T + 18\text{mo})$:
- $y_1 = 1$: P(Maintainer silence / Ghosting)
- $y_2 = 1$: P(Complete human activity cessation / Dead)

By construction, $y_2 \le y_1$, defining the **Ghosting Band** $[p_1 - p_2]$.

### 2. The Interactive Memorial Altar & Specimen Ledger
A live memorial and forensic dossier for `request/request`, the iconic HTTP client that peaked at 14 million weekly downloads before its deprecation on February 11, 2020:
- **Empirical Relic:** Final commit `3c0cddc` ("README: typo in deprecation message (#3268)", preceded by `aded7e4f` "doc: note full deprecation").
- **Badge Status:** `DEPRECATED · NOT ARCHIVED` (reconciled against GitHub API: `archived: false`).
- **The 771-Day Silence Gap:** Responsiveness dropped to zero in January 2018; code commits ended February 11, 2020. That 771-day chasm left 41,000 dependent packages unmonitored.
- **Audited 150 Specimen Ledger:** Complete ledger with interactive client-side filtering, downloads, bus factors, and verified dormancy dates.

### 3. The Forensic Ghost Interview Runtime
An interview runtime where users speak with the deceased repository. Implemented with Gemma (`gemma:2b` / `gemma3:12b`) gated by BM25 retrieval over 11,748 cached documents (commits, issues, comments, releases). Every claim requires an explicit citation; any query about post-death events or unrecorded facts is met with an immediate, non-negotiable abstention:
> *"The archive is silent on that."*

---

## Demo

- **Live Video Walkthrough (YouTube):** [https://youtu.be/omB2iQKnRts](https://youtu.be/omB2iQKnRts)
- **Live Cloud Deployment (Render):** [https://ofrenda-altar.onrender.com](https://ofrenda-altar.onrender.com)
- **Digital Séance & Specimen Ledger:** [https://ofrenda-altar.onrender.com/archive.html](https://ofrenda-altar.onrender.com/archive.html)
- **System Documentation:** [https://ofrenda-altar.onrender.com/docs.html](https://ofrenda-altar.onrender.com/docs.html)
- **Committed 1080p Video Walkthrough:** [`demo.mp4`](https://github.com/aiwithrajan/ofrenda/blob/main/demo.mp4) (4.3 MB, Full HD 1080p with synchronized voice narration committed directly in repository root).
- **1-Click Render Cloud Deployment:** Deploy instantly via pre-configured Blueprint:
  [![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/aiwithrajan/ofrenda)

---

## Code

All code, data schemas, unit tests, and pre-registration documents are open source under the Apache-2.0 License:

{% github aiwithrajan/ofrenda %}

- **GitHub Repository:** [https://github.com/aiwithrajan/ofrenda](https://github.com/aiwithrajan/ofrenda)
- **Key Source Components:**
  - `src/ofrenda/derive.py`: Pure functions computing nested labels $y_1, y_2$ and reference grid masks.
  - `src/ofrenda/features.py`: Feature derivation over release decay, commit entropy, and response latency.
  - `src/ofrenda/fits.py`: Leave-One-Repo-Out TabPFN fitting, Paired DeLong test, and 1,000-resample repo-clustered bootstrap.
  - `src/ofrenda/ask.py`: Gemma forensic interview runtime with citation enforcement.
  - `src/ofrenda/index.py`: Inverted index and grounded retrieval over 11,748 corpus documents.
  - `src/ofrenda/integrations.py`: Verified contest integration schemas, workflows, and query adapters.
  - `altar/`: Complete standalone memorial interface (`index.html`, `archive.html`, `docs.html`).

---

## How I Built It

### 1. Pre-Registration and Scientific Discipline
Before extracting features or fitting models, we pre-registered our hypotheses, masks, and failure criteria:
1. **Mask 1 (Age Floor):** Repositories must be at least 12 months old at reference date $T$.
2. **Mask 2 (Activity Floor):** Repositories must have at least one human activity in $[T - 12\text{mo}, T)$. (A repo cannot die if it was never alive).
3. **Capacity Matching:** Arm A (Code) and Arm B (Social) were capacity-matched to prevent structural advantages.
4. **Non-Inferiority Formulation:** The hypothesis predicts *parity*: at fixed $T$, social signals predict abandonment at least as well as code signals, because code has not stopped moving yet:
   $$\mathcal{H}_0: \text{AUC}_A - \text{AUC}_B \ge 0.07 \quad \text{vs} \quad \mathcal{H}_1: \text{AUC}_A - \text{AUC}_B < 0.07$$

### 2. Empirical Findings & Statistical Verdict
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

### 3. Open-Source AI Architecture
- **TabPFN (Prior-Data Fitted Networks):** Operating in tabular small-$n$ regimes without requiring synthetic oversampling or GPU clusters.
- **Gemma (Open-Weight Models):** Running locally via Ollama (`gemma:2b` / `gemma3:12b`) and grounded cloud fallbacks.
- **BM25 Corpse Index:** 11,748 documents parsed and indexed for deterministic evidence grounding.

---

## Why Does Open Innovation Matter?

Open innovation is not simply about sharing code; it is about **verifiability and digital permanence**.

When an organization relies on closed, proprietary cloud APIs, the model's weights, training data, and latent assumptions remain black boxes. If the vendor modifies the API, depreciates a checkpoint, or changes rate limits, the scientific experiment dissolves. 

In Ofrenda:
1. **Local Foundation Weights (Gemma via Ollama):** Gemma provides open weights that can be run entirely air-gapped on consumer hardware. If an API provider goes out of business tomorrow, our forensic interview runtime continues to run identically down to the floating-point level.
2. **Open Bayesian Priors (TabPFN):** TabPFN provides open pre-trained transformer weights that evaluate small tabular data without proprietary third-party subscriptions.
3. **Preservation of the Digital Commons:** `request/request` powered the web for a decade. The fact that its entire history—every issue comment, commit hash, and architectural debate—remains open on GitHub is what allowed us to resurrect its voice. Closed software leaves no ruins; open source leaves monuments.

---

## My Agent Session

The complete research investigation, bug forensics, and deployment session were recorded with full reproducibility:
- **Session Trajectory Logs:** Committed at `results/trajectory.jsonl`
- **Unit Test Suite:** 63 passing unit tests verifying data extraction, feature generation, DeLong calculations, and server endpoints (`python -m unittest discover tests`).

---

## The Spirit of It

During our forensic examination of `request/request`, we discovered that commit `aded7e4f` on February 11, 2020 added a single word to the README: `DEPRECATED`. 

For 771 days prior, automated bots had continued to open dependency PRs, CI badges remained green, and downloads averaged 14 million per week. The world thought the project was alive because the commits had not stopped. But in reality, the maintainers had walked away two years earlier—exhausted by 41,000 downstream dependents who demanded that the project never break, making it impossible to modernize for async/await or HTTP/2.

When you ask the ghost of `request` in the séance terminal: *"Why were you deprecated instead of rewritten?"*, it does not give a generic AI apology. It cites Issue #3142:
> *"Existing patterns could not be changed without breaking foundational infrastructure. The project stood still so the ecosystem could move forward."*

---

## Prize Categories

Per PRD §6, we pre-registered an **Honest Ledger**: every claimed integration must have a genuine, verifiable, load-bearing role in code. We actively descoped categories that were not truly load-bearing in production (Tinker and DigitalOcean, as our pipeline runs air-gapped on consumer hardware without remote GPU rentals).

We proudly enter the **17 verified, code-backed categories** implemented in `src/ofrenda/integrations.py`, `render.yaml`, and the core pipeline:

### Featured Categories
1. **TabPFN:** The forecast itself. In-context Bayesian classifiers over $n=150$ repos — operating in TabPFN's native small-$n$ tabular regime without synthetic inflation (`src/ofrenda/fits.py`).
2. **Gemma:** The interview runtime. Runs locally and cloud-grounded; the ghost of `request` speaks in an elegiac, restrained voice strictly grounded in its records (`src/ofrenda/ask.py`).

### Partner Categories
3. **Render:** Cloud hosting & continuous deployment — containerized web service hosting the public interactive Altar, corpse index, and forensic API via `render.yaml` with automated health monitoring.
4. **MongoDB Atlas:** Vector store of issues and commits for retrieval; Atlas Vector Search performs semantic discovery across issue threads (`atlas_vector_schema()`).
5. **Tiger Data:** pgvector hybrid search — combining BM25 exact symbol matching with dense vector conceptual retrieval (`tiger_pgvector_query()`).
6. **Temporal:** Durable ingestion workflow orchestrating the rate-limited multi-hour GitHub pull to guarantee resume-on-failure (`RepoIngestWorkflow`).
7. **Sentry:** Observability & agent tracing — capturing tokens, inference latency, rate-limit retries, and pipeline cost per stage (`SentryTracing`).
8. **ElevenLabs:** Voice synthesis reciting the frozen README deprecation notice aloud (`elevenlabs_tts_payload()`).
9. **SerpApi:** Discovery engine finding forks, successor projects, community "is this dead?" threads, and the official deprecation announcement (`serpapi_search_query()`).
10. **Browserbase:** Headless browser automation extracting archive.org snapshots of the original documentation site (`browserbase_snapshot_config()`).
11. **Auth0:** Consent gate: human sign-off required before the ghost interview is published or speaks publicly; Token Vault holds the GitHub repo token (`auth0_consent_gate()`).
12. **Backboard:** Cross-session memory enabling the ghost to remember conversational context across user visits (`BackboardMemory`).
13. **Ultramarine:** Long-document reasoning over ten years of issue backlogs to answer: *"What was request trying to become?"* (`ultramarine_analysis_prompt()`).
14. **Mastra:** Agent orchestration framework managing the interview loop as a TypeScript sidecar interfacing with the Python engine (`mastra_agent_manifest()`).
15. **GitHub Copilot:** Modernization agent generating the revival epilogue PR proposing native Promises, Fetch, and HTTP/2 (`copilot_revival_prompt()`).
16. **Entire:** Complete agent trajectory session recorder capturing the step-by-step forensic investigation for transparency (`EntireTrajectoryRecorder`).
17. **.tech domain:** The public memorial and live artifact hosted at `ofrenda.tech`.
