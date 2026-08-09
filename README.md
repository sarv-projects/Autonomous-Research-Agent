# Autonomous Research Agent

A **self-improving research and chat agent** that answers like a strong general assistant, produces **cited, progressive, high-signal research reports**, and renders mathematical formulas properly — powered by durable execution, bias mitigation, and token optimization.

Built with LangGraph + Temporal.io, an adversarial triangulation harness, a factoid extraction pipeline, and a production-style BYOK LLM gateway.

> **Status:** the repository currently runs a subset (LangGraph research loop + Tavily + resilient gateway with API keys).
> See [docs/AUDIT.md](docs/AUDIT.md) for the built-vs-target matrix — [docs/SPEC.md](docs/SPEC.md) is the goal.

| | |
|--|--|
| **Specs (target product)** | [`docs/SPEC.md`](docs/SPEC.md) · [full index](docs/INDEX.md) |
| **Audit (built vs target)** | [`docs/AUDIT.md`](docs/AUDIT.md) |
| **Install** | [`docs/INSTALL.md`](docs/INSTALL.md) |

---

## Capabilities

### 🔄 Durable Execution
- **Temporal.io integration** for 24h+ research runs (`ultra-long` mode)
- LangGraph graph wrapped as a Temporal workflow; nodes become activities
- Durable state checkpoints with automatic crash recovery and workflow resumption
- **Human-in-the-loop** pause/approval via Temporal signals
- Cost and token budget enforcement at workflow level

### ⚖️ Bias Mitigation
- **Adversarial triangulation** for subjective/controversial queries
- Pro / Con / Neutral agent systems that mechanically cancel model bias
- Synthesis Arbiter for bias detection with explicit bias assessment scores
- Multi-provider setup (OpenAI, Anthropic, Google)

### 🎯 Token Optimization
- **Factoid extraction pipeline** — ~90% token reduction vs raw page dumps
- Cheap local model (Llama 3 8B / Phi-3) extracts structured JSON factoids (entity, relation, event, statistic, definition, citation)
- Anti-hallucination quote gate, dedup/merging, PostgreSQL/pgvector storage
- Gap-aware evidence assembly (AdaGATE pattern) — full page bodies never enter the main LLM context

### 🛡️ Source Verification
- **Retriever Guard** filters sources for credibility before RAG
- Domain reputation analysis, content freshness detection, citation quality scoring
- Blocks low-quality sources (SEO spam, content farms); promotes peer-reviewed / official docs
- 3-tier retry pyramid: backoff → provider failover → semantic rephrase

### 🧠 Multi-Agent Harness
- Specialized roles instead of one super-agent: **Planner · Researcher · Thinker · Critic · Synthesizer · Compiler**, plus Triangulator, Factoid Extractor, Retriever Guard
- **Thinker** (Gemini free tier) handles large-context reasoning only — no tool calls, structured JSON out
- **Staged autonomy**: L1 Report (default) · L2 Human gate · L3 Unattended with hard budgets
- **Dynamic task graph** — users can inject new tasks mid-research; the DAG auto-replans without restart
- Model-agnostic harness with constrained decoding for consistent output across models

### 🚀 Relentless Retrieval & RAG
- RAG with **LanceDB** (default embedded) / **Qdrant** (production) / **SQLite FTS5** (always-on fallback)
- Hybrid dense + keyword retrieval over run corpus, vault, and chat memory
- **MCP tool bus**: Tavily, Wikipedia, Firecrawl, Exa, arXiv, **MinerU** / **Nougat** PDF parsers, vault tools
- Retrieval on compressed factoids, not raw chunks

### 📐 Mathematical Rendering
- **MathJax/KaTeX** rendering with inline `$...$` and block `$$...$$` support
- LaTeX syntax detection, validation, and sanitization; symbol enrichment via constrained decoding
- Export: HTML with MathJax, PDF with proper typesetting, MathML for accessibility

### 🧭 Modes & Quality Dials
`chat` · `quick` · `standard` · `deep` · `recency` · `academic` · `compare` · `ultra-long` (24h durable)

Quality dials overlay mode budgets: **ultra-fast · balanced · accurate · comprehensive**

### 🌐 Universal Providers
- Empty `base_url` → OpenCode free; empty key → no auth
- First-wave presets: OpenCode free, NVIDIA NIM, OpenRouter, North Mini Code, Cohere, OpenAI, Claude, Gemini, Groq, DeepSeek v4, MiMo
- `+` provider / `+` model — user-extensible OpenAI-compatible endpoints
- All calls through the resilient gateway: failover chains, circuit breakers, rate limits, retries + jitter, cost accounting, Prometheus metrics

### ♻️ Self-Improving
- On every run: sources persisted to a **vault**, structured run traces (JSONL), strategy memory (what worked/failed), source-quality scores
- Next similar query searches the **vault before paid fetch**

---

## Quick start

### Prerequisites

- Python **3.14+** and [uv](https://docs.astral.sh/uv/)
- **`GROQ_API_KEY`** (or `OPENAI_API_KEY` / `OPENROUTER_API_KEY`)
- **`TAVILY_API_KEY`** for web search
- **Optional:** Temporal Server (durable execution) — see [INSTALL.md](docs/INSTALL.md)

### Bash

```bash
git clone <repo-url> && cd Autonomous-Research-Agent
bash scripts/install.sh
# edit .env with Groq + Tavily keys
uv run python main.py "latest developments in quantum computing"
uv run python main.py --history
uv run python -m src.dashboard --port 8080
uv run python test_gateway.py
```

### PowerShell

```powershell
git clone <repo-url>; cd Autonomous-Research-Agent
.\scripts\install.ps1
# edit .env
uv run python main.py "your research topic"
```

---

## Documentation

| Doc | Role |
|------|------|
| [SPEC.md](docs/SPEC.md) | Product requirements — the target (normative) |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Engine / RAG / progressive write design |
| [PROVIDERS.md](docs/PROVIDERS.md) | Official LLM bases & model IDs |
| [ROADMAP.md](docs/ROADMAP.md) | Phases A–L implementation plan |
| [GATEWAY.md](docs/GATEWAY.md) | Gateway (built) + dashboard + Temporal integration |
| [FACTOID_PIPELINE.md](docs/FACTOID_PIPELINE.md) | Factoid extraction for token optimization |
| [UX_DESIGN.md](docs/UX_DESIGN.md) | Web UI/UX design specification |
| [EVALS.md](docs/EVALS.md) | Eval design |
| [PRODUCTION_CHECKLIST.md](docs/PRODUCTION_CHECKLIST.md) | Production hardening checklist |
| [INSTALL.md](docs/INSTALL.md) | Install detail (incl. Temporal, Ollama/vLLM) |
| [AUDIT.md](docs/AUDIT.md) | Built vs target verification report |

---

## Architecture

Plan–Act–Observe harness with specialized agents (target):

```
Planner (DAG / outline / budgets)
  → [Thinker: refine plan if large/complex]
  → Researcher: tool_select → gather → ingest → retrieve → analyze
  → [Thinker: contradiction / multi-source reason]
  → Critic / reflect (gaps | stop | retry) ↺
  → Synthesizer: outline → per section: retrieve → draft (streamed)
  → Critic: citations pass / fact-check sample
  → Compiler: polish → export (ship-gate)
```

Ultra-long horizon (24h): the LangGraph graph is wrapped in a Temporal workflow with durable checkpoints, heartbeats, crash recovery, and human-in-the-loop signals.

**Ship gate:** end Sources section present · key claims have evidence ids · no empty body · progressive write completed.

### Layout (current codebase)

```
main.py            # CLI: research a topic, --history
src/graph.py       # LangGraph orchestration (9 nodes)
src/nodes.py       # research nodes (parse → plan → search → extract → dedup → analyze → evaluate → synthesize → export)
src/state.py       # ResearchState TypedDicts
src/llm.py         # LLM wrapper → gateway (fast / strong tiers)
src/search.py      # Tavily parallel search + page extraction
src/memory.py      # JSON search history (~/.xiarch_memory.json)
src/export.py      # Markdown report export → reports/
src/gateway/       # resilient BYOK LLM gateway (stdlib-only)
src/dashboard/     # zero-dependency ops dashboard (SSE + Prometheus)
test_gateway.py    # offline gateway tests (9/9)
test_run.py        # e2e live tests (5/5, needs keys)
docs/              # spec, architecture, roadmap, audit, …
scripts/           # install.sh | install.ps1
```

---

## License / contributing

Implement against [docs/ROADMAP.md](docs/ROADMAP.md). Specs are normative for the target product; AUDIT is normative for "what works today."
