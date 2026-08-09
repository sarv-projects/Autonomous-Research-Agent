# Autonomous Research Agent

A **self-improving research and chat agent** that answers like a strong general assistant, produces **cited, progressive, high-signal research reports**, and renders mathematical formulas properly — powered by durable execution, bias mitigation, and token optimization.

Built with LangGraph + Temporal.io, an adversarial triangulation harness, a factoid extraction pipeline, and a production-style BYOK LLM gateway.

> **Status:** ✅ **Fully Functional** — All core features implemented including web UI, eval system, and Temporal integration.
> See [docs/IMPLEMENTATION_STATUS.md](docs/IMPLEMENTATION_STATUS.md) for detailed implementation status.

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

### 🖥️ Modern Web Interface
- **ChatGPT-like interface** with clean, intuitive design
- **Real-time chat** with streaming responses
- **Deep research mode** with progress tracking
- **History page** to view past research and conversations
- **Settings page** for configuring modes, autonomy, and providers
- **Dark mode** with automatic theme switching
- **Markdown rendering** with LaTeX math support
- **Responsive design** for desktop and mobile

---

## Quick start

### Prerequisites

- Python **3.14+** and [uv](https://docs.astral.sh/uv/)
- **Optional:** API keys for paid providers (Groq, OpenAI, OpenRouter, etc.) — uses OpenCode Zen free if not configured
- **Optional:** Temporal Server (durable execution) — see [INSTALL.md](docs/INSTALL.md)

### Bash

```bash
git clone <repo-url> && cd Autonomous-Research-Agent
bash scripts/install.sh
# edit .env with API keys (optional - uses free tier without keys)

# Start the web UI (recommended)
uv run python main.py server

# Then start the frontend (in a new terminal)
cd frontend
npm install
npm run dev

# Or use CLI commands
uv run python main.py chat                    # Interactive chat
uv run python main.py research "topic"         # Deep research
uv run python main.py doctor                   # System health check
uv run python main.py eval [suite]             # Run evaluations
uv run python main.py --history                # View past researches
```

### PowerShell

```powershell
git clone <repo-url>; cd Autonomous-Research-Agent
.\scripts\install.ps1
# edit .env (optional)

# Start the web UI (recommended)
uv run python main.py server

# Then start the frontend (in a new terminal)
cd frontend
npm install
npm run dev

# Or use CLI commands
uv run python main.py chat
uv run python main.py research "your topic"
uv run python main.py doctor
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
| [IMPLEMENTATION_STATUS.md](docs/IMPLEMENTATION_STATUS.md) | Current implementation status (~85% complete) |
| [frontend/README.md](frontend/README.md) | Frontend documentation |

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
main.py            # CLI: chat, research, doctor, eval, server, --history
src/graph.py       # LangGraph orchestration (9 nodes)
src/state.py       # ResearchState TypedDicts
src/llm.py         # LLM wrapper → gateway (fast / strong / thinker tiers)
src/gateway/       # resilient BYOK LLM gateway (stdlib-only)
src/providers/     # Provider catalog and configuration
src/engine/        # Multi-agent system and modes
  ├── agents/      # Planner, Researcher, Critic, Synthesizer, Compiler, Thinker, Triangulator
  ├── modes.py     # Research modes (chat, quick, standard, deep, etc.)
  ├── temporal/    # Temporal workflows and activities (durable execution)
src/rag/           # RAG pipeline with vector storage
  ├── factoid.py   # Factoid extraction (token optimization)
  ├── guard.py     # Retriever Guard (source verification)
  ├── pipeline.py  # RAG pipeline orchestration
  ├── vault.py     # Research vault and memory
src/render/        # Output rendering
  ├── math.py      # LaTeX math rendering
src/tools/         # MCP tools and adapters
  ├── adapters/    # Wikipedia, Firecrawl, built-in scraper
src/eval/          # Evaluation system
  ├── ComponentEvaluator, SystemEvaluator, OpsMetrics
src/web/           # FastAPI REST API server
  ├── Endpoints: /api/status, /api/chat, /api/research, /api/providers, /api/history
config/            # Configuration files
  ├── providers.yaml  # Provider configuration
  ├── modes.yaml      # Research modes
docs/              # spec, architecture, roadmap, audit, implementation status, …
scripts/           # install.sh | install.ps1
```

---

## License / contributing

Implement against [docs/ROADMAP.md](docs/ROADMAP.md). Specs are normative for the target product; AUDIT is normative for "what works today."
