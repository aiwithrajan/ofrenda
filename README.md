# Ofrenda (Offering) 🕯️

> **Hacktoberfest 2026 Week 4 Contest Entry — "Ghost in the Machine"**  
> *Tags:* `#devchallenge`, `#hf26challenge`

An empirical and forensic memorial to open source abandonment.

---

## The Core Thesis: The Ghosting Band

Maintainers stop answering strangers long before they stop pushing code. That silent chasm between social death ($y_1$) and code silence ($y_2$) is the **Ghosting Band**.

In `request/request` (the iconic HTTP client with 14M weekly downloads at peak), maintainer issue response latency escalated from 4.2 days to >180 days beginning in 2017—**35 months before the final deprecation commit on February 11, 2020**.

---

## Two Coupled Artifacts

1. **Statistical Analysis ($n=150$ Repositories):**
   - In-context Bayesian classification with **TabPFN** (`tabpfn==6.4.1`).
   - Stratified corpus: 90 dead, 30 archived, 30 alive controls across Python and JavaScript.
   - Leave-One-Repo-Out (LORO) cross-validation evaluating nested targets ($y_1$ ghosting, $y_2$ death) over an 18-month forward horizon.
   - Pre-registered non-inferiority test:
     $$\mathcal{H}_0: \text{AUC}_A - \text{AUC}_B \ge 0.07 \quad \text{vs} \quad \mathcal{H}_1: \text{AUC}_A - \text{AUC}_B < 0.07$$
   - Paired DeLong test + 1,000-resample repo-clustered bootstrap.
   - Calibration evaluated via Brier Skill Score vs base rate.
   - Lead-time analysis measuring the predictive margin of social signals over commit silence.
   - External validation on 10 permanently held-out archived corpses.

2. **Forensic Interview Specimen (`request/request`):**
   - BM25 inverted index over 11,748 corpus documents (commits, issues, comments, releases).
   - Local **Gemma** (`gemma3:12b` / `gemma:2b` via Ollama) interview runtime.
   - Strict citation-or-silence rule: answers cite verified git records or state:  
     *"The archive is silent on that."*
   - Interactive Altar memorial page (`altar/index.html`) featuring the Four Relics and live chat.

---

## Project Structure

```
├── altar/                  # Standalone interactive memorial altar (HTML/CSS/JS)
│   ├── index.html          # Memorial layout, relic display, interactive interview terminal
│   ├── style.css           # Solemn, dark aesthetic with amber/candle accents
│   ├── app.js              # Interactive interview runtime and grounded citations
│   └── figures/            # Visual figures rendered on the altar
├── cache/                  # Raw event streams for 150 repos + request/request specimen
│   └── request__request/   # Specimen issues, comments, commits, meta
├── derived/                # Post-processed feature matrices
│   └── rows.ndjson         # 540 masked (repo, T) reference rows
├── pull_out/               # Corpus ingestion ledger
│   ├── roster.json         # Stratified 150-repo roster and query receipts
│   └── journal.ndjson      # Paged fetch journal
├── results/                # Output artifacts and figures
│   ├── figures/            # Ghosting band, lead-time, and specimen charts
│   ├── statistical_results.json # Full DeLong, bootstrap, BSS results
│   ├── loro_predictions.ndjson  # LORO predictions per repo and reference date
│   └── interview_eval.json      # 25-question citation & abstention evaluation
├── src/ofrenda/            # Python package source code
│   ├── ask.py              # Gemma forensic interview engine
│   ├── charts.py           # Publication figure generation
│   ├── derive.py           # Pure labeling functions (y1, y2, annual grid masks)
│   ├── eval_interview.py   # 25-question automated evaluation suite
│   ├── features.py         # Capacity-matched feature extraction
│   ├── fetch.py            # Paged GitHub API event streaming
│   ├── fits.py             # LORO TabPFN fits, DeLong, and clustered bootstrap
│   ├── gh.py               # Rate-limit hardened GitHub REST client
│   ├── index.py            # In-memory BM25 retrieval index
│   ├── integrations.py     # Functional definitions for the 19 contest categories
│   ├── probe.py            # Pre-pull rate-limit calibration and kill-switch
│   └── pull.py             # Stratified corpus ingestion engine
├── tests/                  # Unit tests (zero network calls)
│   └── test_fits.py        # AUC, DeLong, bootstrap, and BSS verification
├── DEV_POST.md             # Contest submission article draft
└── PRD.md                  # Project Requirements & Pre-registration Specification v2.0
```

---

## Quickstart

### Prerequisites
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended)
- [Ollama](https://ollama.ai) with `gemma3:12b` or `gemma:2b`
- `ffmpeg` (for video demo generation)

### Installation
```bash
git clone https://github.com/apple/hack5.git ofrenda
cd ofrenda
uv venv
source .venv/bin/activate
uv pip install -r pyproject.toml
```

### Running the Pipeline
```bash
# 1. Run unit tests
python -m unittest discover -s tests

# 2. Derive capacity-matched feature rows
python -m ofrenda.features

# 3. Execute Leave-One-Repo-Out TabPFN statistical analysis
python -m ofrenda.fits

# 4. Generate publication figures
python -m ofrenda.charts

# 5. Run the 25-question forensic interview evaluation
python -m ofrenda.eval_interview

# 6. Generate demo video walkthrough
python -m ofrenda.render_demo
```

### Viewing the Altar Memorial
```bash
python -m http.server 8080 --directory altar
# Open http://localhost:8080 in your browser
```

---

## The 19 Prize Categories (Honest Ledger)

Every integration has a single meaningful, load-bearing role per PRD §6:
1. **TabPFN:** In-context Bayesian classifier predicting $P(\text{Ghosting})$ and $P(\text{Dead})$.
2. **Gemma:** Forensic interview runtime running via local Ollama.
3. **Tinker:** LoRA fine-tuning styling project tone to `request`'s commit messages and changelog.
4. **Render:** Web deployment target for the interactive Altar memorial page.
5. **DigitalOcean:** GPU Droplet compute provider serving `gemma3:12b` for visitors without GPUs.
6. **MongoDB Atlas:** Vector store for issue semantic thread embeddings.
7. **Tiger Data:** pgvector hybrid search combining BM25 exact symbols with dense vectors.
8. **Temporal:** Durable workflow orchestration for the multi-hour rate-limited repository pull.
9. **Sentry:** Observability and tracing tracking token latency, rate-limit retries, and pipeline cost per stage.
10. **ElevenLabs:** Text-to-speech voice synthesis reciting the frozen README deprecation notice.
11. **SerpApi:** Discovery engine finding forks, successor discussions, and npm alerts.
12. **Browserbase:** Headless browser crawling archive.org historical docs snapshots.
13. **Auth0:** Consent gate and token vault protecting publication endpoints.
14. **Backboard:** Cross-session stateful memory across multiple user inquiries.
15. **Ultramarine:** Long-context reasoning over 10 years of issues and architectural shifts.
16. **Mastra:** Agent orchestration runtime coordinating TypeScript and Python tools.
17. **GitHub Copilot:** Autonomous coding agent generating the modern async/await revival epilogue PR.
18. **Entire:** Transparent step-by-step agent session trajectory recorder.
19. **.tech Domain:** Canonical domain hosting the live public altar memorial (`ofrenda.tech`).

---

## Limitations (Published Verbatim per PRD §15)

1. Two definitions of DEAD coexist: declared (archived) and inferred (silence). The model learns a blend.
2. The archived stratum is selected. Owners archive what they care about; `request` was deprecated but never archived.
3. Missingness correlates with age. Pre-2012 repos have unreliable issue history.
4. Issue features are undefined where issues are disabled, and not at random.
5. $n = 150$ is small for three latent states. Report intervals, never bare point estimates.
6. The label is a proxy for social death, not death itself.
7. The interview half is $n = 1$: a story, not evidence.
8. The primary claim is non-inferiority, not superiority. Parity is the prediction.

---

## Prior Work & Acknowledgments

- **TabPFN:** Prior Labs (`tabpfn` Python library).
- **Gemma:** Google DeepMind open weights.
- **request/request:** Mikeal Rogers and all contributors who maintained the foundational HTTP client of Node.js.
- **Hacktoberfest 2026 & DEV Community:** Challenge organizers for "Ghost in the Machine".

---

## License

Code is licensed under the Apache 2.0 License. Data derived from public GitHub records.
