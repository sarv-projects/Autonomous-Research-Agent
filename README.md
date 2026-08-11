<div align="center">

# Providence

**A research engine whose reports cannot fake their evidence.**

Most deep-research tools *ask* the model to be honest. Providence makes it impossible to be otherwise: only sources it actually fetched in this run can appear in the report, every claim is checked against those sources, and a ship-gate refuses to publish anything with fabricated citations.

**Measured, not promised.** On a 15-topic stress suite scored against independently researched ground truth: **86% fact-check accuracy**, **zero fabricated sources across 15/15 reports**, reports up to **47,895 words**, ~8 min average runtime (vs 5–30 min for product deep research). Runs with zero API keys; scales with Groq/OpenAI/Gemini/Exa.

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![LangGraph](https://img.shields.io/badge/orchestration-LangGraph-FF6F00.svg)](https://github.com/langchain-ai/langgraph)
[![Next.js](https://img.shields.io/badge/UI-Next.js-000000.svg?logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)

</div>

---

## What is this?

Providence turns a research question into a **cited technical report** — the kind of deep-dive you'd ask a human analyst for, not a chat answer.

Give it something like *"How does RAG reduce hallucination in LLMs?"* and it will:

1. **Plan** the investigation — break your question into subtopics and decide what to look for
2. **Search and read** — pull from Exa, arXiv, Wikipedia, news wires and more; hundreds of pages per run
3. **Hunt counter-evidence** — actively look for limitations, retractions, and arguments against the mainstream view
4. **Verify every claim** — each statement is checked against the sources this run actually read, then labeled `supported` / `contested` / `synthetic`
5. **Compile the report** — with inline citations, an Evidence Bedrock (verbatim source quotes), a Research Debt section (what it *couldn't* verify), and LaTeX-rendered math

Every URL in the report's Sources list was fetched and read in that run. The report can't cite a page it never opened, and it can't claim something it couldn't back up — it says what it couldn't prove instead.

**What you get per run:** a Markdown report + an interactive HTML export (saved to `reports/`).

---

## Quick start

**You need:** Python 3.10+ and [uv](https://docs.astral.sh/uv/). That's it — no API keys required to start.

```bash
# 1. Clone + install
git clone https://github.com/sarv-projects/providence.git
cd providence
bash scripts/install.sh          # Windows: .\scripts\install.ps1

# 2. Run your first research
uv run python main.py research "How does RAG reduce hallucination in LLMs?" --mode standard

# 3. Open the web UI (optional)
bash scripts/start-dev.sh
# UI at http://localhost:3000
```

The first run works out of the box on the free OpenCode Zen provider. Adding keys makes research faster and deeper:

| To get… | Add |
|---|---|
| **Faster, smarter runs** | `GROQ_API_KEY` (primary) · `GEMINI_API_KEY` (planning tier) |
| **Better web search** | `EXA_API_KEY` (recommended) · `TAVILY_API_KEY` · `FIRECRAWL_API_KEY` |
| **Fresh news coverage** | `NEWSDATA_API_KEY` (optional) |

Create a `.env` file from `.env.example` and fill in what you have.

---

## Usage

### Command line

```bash
# Check the system is ready (gateway routes, tools, free-model probe)
uv run python main.py doctor

# Research — pick a mode that matches the job (see table below)
uv run python main.py research "Your question" --mode deep
uv run python main.py research "Rust vs Go for backends" --mode compare
uv run python main.py research "Latest diffusion-model work" --mode recency
uv run python main.py research "Quantum cryptography survey" --mode academic
uv run python main.py research "Quick facts on transformers" --mode quick

# Chat (conversation memory, auto-escalates research-y questions)
uv run python main.py chat

# API server for the web UI / integrations
uv run python main.py server

# See past runs
uv run python main.py --history
```

### Web UI

```bash
bash scripts/start-dev.sh
```

The UI gives you **chat**, a **research launcher** (mode + autonomy + live progress), a **thinking panel** showing what the engine learned/found missing mid-run, a **model picker**, **history**, **vault search**, and **settings**. For hands-off runs, autonomy L1 runs end-to-end; L2 pauses for your plan approval before gathering.

### Which mode?

| Mode | Use it when… | Roughly how long |
|------|--------------|------------------|
| `quick` | You need facts fast, not a thesis | ~1 min |
| `standard` | Balanced default for most questions | ~3–4 min |
| `deep` | Full integrity pipeline: counter-evidence, verification, research debt | ~5–8 min |
| `academic` | Papers-first, scholarly tone | ~3–5 min |
| `compare` | "A vs B" with a structured comparison matrix | ~3–5 min |
| `recency` | Current events, latest papers/news | ~2–4 min |
| `ultra-long` | Very large surveys (optional Temporal durability) | Custom |

---

## How it works (the short version)

A pipeline of ten specialized agents runs the investigation, with a critic deciding after each round whether to research more, move on, or abort. The two things that make it different from a "search + summarize" tool:

- **The verification loop** — a claim-adjudication stage checks every claim against the run's actual corpus before anything is written, and a devil's-advocate stage deliberately searches for reasons the conclusions are wrong.
- **The ship-gate** — the final compiler re-checks all citations against the sources actually fetched this run, strips anything fabricated, and refuses to ship a report that fails evidence checks.

Diagram and deep-dive: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — the README stays user-facing.

---

## Proof it works

15 high-complexity topics (geopolitics, climate, energy, space, AI, medicine, macro-economics…) were run end-to-end and scored against **independently web-researched ground truth** — not the model's own claims.

| Metric | Result |
|---|---|
| Fact-check accuracy | **86%** (76/91 ground-truth facts correct, 0 hallucinated-and-shipped) |
| Ship-gate | **15/15 passed — zero fabricated sources** |
| Avg report | 12 sections · ~164K chars · **34 real citations** |
| Largest report | **47,895 words** |
| Avg runtime | **8.1 min** (vs 5–30 min for product Deep Research) |
| Rubric coverage | 79% across 6 quality checkpoints (thesis 100%, contrarian fork 87%) |

Grades: **8× A, 6× B, 1× C**. Full per-topic matrix, logs, and methodology: [`benchmarks/RESEARCH_BENCHMARK.md`](benchmarks/RESEARCH_BENCHMARK.md).

Known weak spots from the suite: tier-1 newswire coverage and Global South sources are thinner than the rubric wants (both improved in later rounds with the GDELT/NewsData integration), and one topic (lunar infrastructure hardware specs) scored C.

---

## Limitations (read this)

- **Output quality scales with your keys.** On free-only defaults, retrieval breadth and synthesis quality are lower than with Exa + a paid workhorse model.
- **It synthesizes literature; it doesn't run experiments.** No paper-code reproduction.
- **Free models are slower.** Deep runs on Zen free can take significantly longer than the benchmark averages.
- **Embeddings degrade without a key** — falls back to keyword matching (BoW).
- **Temporal is optional** — without a cluster, `ultra-long` runs in-process and won't survive restarts.
- **Evals are smoke tests**, not academic leaderboards.

---

## For developers & contributors

- **Install:** `docs/INSTALL.md` · **Providers/keys:** `docs/PROVIDERS.md` · **Architecture:** `docs/ARCHITECTURE.md`
- **Tests:** `uv run python main.py eval all` (offline suites) · `test_gateway.py` (gateway) · `test_phase_*.py` (integration)
- **Docs index:** [`docs/INDEX.md`](docs/INDEX.md) · Benchmarks: [`benchmarks/`](benchmarks/)
- **License:** MIT — see [LICENSE](LICENSE)

Contributions welcome — open an issue first for large changes, and keep the existing conventions: graceful degradation without optional deps, zero-key setup always works, and new evidence paths must respect the ship-gate.

---

## License

MIT — see [LICENSE](LICENSE).
