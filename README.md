# Autonomous Research Agent

Enterprise-grade autonomous research agent with **durable execution, bias mitigation, token optimization, and mathematical rendering**. Built with LangGraph, Temporal.io, and a production-style LLM gateway.

<!-- TODO: Add hero image/screenshot here -->
<!-- 
![Hero Screenshot](docs/screenshots/hero.png)
*Web dashboard with chat and research interfaces*
-->

| | |
|--|--|
| **Specs (target product)** | [`docs/SPEC.md`](docs/SPEC.md) · [full index](docs/INDEX.md) |
| **Audit (built vs target)** | [`docs/AUDIT.md`](docs/AUDIT.md) |
| **Install** | [`docs/INSTALL.md`](docs/INSTALL.md) |

---

## Built today vs target

| Built **now** (code) | Target (docs / roadmap) |
|----------------------|-------------------------|
| 9-node research graph, max 3 loops | Multi-iter RAG + progressive section write |
| Tavily search + extract | + MCP (wiki, Firecrawl, Exa), MinerU/Nougat PDF |
| Gateway: Groq / OpenAI / OpenRouter **with API keys** | Empty URL → OpenCode free; Claude/Gemini/NIM/DeepSeek/… |
| JSON search history | Vault + self-improve traces |
| Ops dashboard | Full chat + research web product |
| `main.py "topic"` · `--history` | `chat` · `doctor` · `eval` · modes |
| Basic research loop | **NEW: Temporal durable execution (24h+ runs)** |
| Single-model approach | **NEW: Bias mitigation via adversarial triangulation** |
| Raw chunk RAG | **NEW: Factoid extraction (90% token reduction)** |
| Basic source retrieval | **NEW: Retriever Guard (source verification)** |
| Plain markdown output | **NEW: Mathematical rendering (MathJax/KaTeX)** |

See **[docs/AUDIT.md](docs/AUDIT.md)** for the full checklist.

---

## New capabilities (roadmap)

<!-- TODO: Add capabilities overview screenshot -->
<!-- 
![Capabilities Overview](docs/screenshots/capabilities.png)
*Key capabilities: Durable execution, bias mitigation, token optimization*
-->

The agent is evolving with advanced research capabilities:

### 🔄 Durable Execution (Phase C3)
- **Temporal.io integration** for 24h+ research runs
- Automatic crash recovery and workflow resumption
- Human-in-the-loop pause/approval capabilities
- Distributed execution across multiple workers

### ⚖️ Bias Mitigation (Phase E)
- **Adversarial triangulation** for subjective/controversial queries
- Multi-provider setup (OpenAI, Anthropic, Google)
- Pro/Con/Neutral agent system with bias assessment scoring
- Mechanically cancels model bias via cross-agent critique

### 🎯 Token Optimization (Phase F)
- **Factoid extraction pipeline** for 90% token reduction
- Local inference with Ollama/vLLM (Llama 3 8B, Phi-3)
- Structured JSON factoids (entity, relation, event, statistic, definition)
- Gap-aware evidence assembly (AdaGATE pattern)

### 🛡️ Source Verification (Phase G)
- **Retriever Guard** for source credibility filtering
- Domain reputation analysis and content freshness detection
- Blocks low-quality sources (SEO spam, content farms)
- Promotes high-quality sources (peer-reviewed, official docs)

### 📐 Mathematical Rendering (Phase L)
- **MathJax/KaTeX integration** for LaTeX rendering
- Inline math (`$...$`) and block math (`$$...$$`) support
- Multi-modal model integration for equation images
- Export formats: HTML with MathJax, PDF with proper typesetting

See [ROADMAP.md](docs/ROADMAP.md) for implementation phases and details.

---

## Quick start (what works now)

<!-- TODO: Add demo video -->
<!-- 
[![Demo Video](docs/screenshots/video-thumbnail.png)](https://youtube.com/watch?v=TODO)
*Watch the demo video (2 min)*
-->

### Prerequisites

- Python **3.14+**, [uv](https://docs.astral.sh/uv/)
- **`GROQ_API_KEY`** (or `OPENAI_API_KEY` / `OPENROUTER_API_KEY`)
- **`TAVILY_API_KEY`** for web search
- **Optional:** Temporal Server (for durable execution) — see [INSTALL.md](docs/INSTALL.md)
- **Optional:** Ollama/vLLM (for factoid extraction) — see [INSTALL.md](docs/INSTALL.md)

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

<!-- TODO: Add terminal screenshot -->
<!-- 
![Terminal Demo](docs/screenshots/terminal.png)
*Terminal output showing research in progress*
-->

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
| [SPEC.md](docs/SPEC.md) | Product requirements (target) |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Engine / RAG / progressive write design |
| [PROVIDERS.md](docs/PROVIDERS.md) | Official LLM bases & model IDs |
| [ROADMAP.md](docs/ROADMAP.md) | Phases A–L (including new capabilities) |
| [GATEWAY.md](docs/GATEWAY.md) | Built gateway + dashboard + Temporal integration |
| [FACTOID_PIPELINE.md](docs/FACTOID_PIPELINE.md) | Factoid extraction for token optimization |
| [UX_DESIGN.md](docs/UX_DESIGN.md) | Web UI/UX design specification |
| [EVALS.md](docs/EVALS.md) | Eval design |
| [INSTALL.md](docs/INSTALL.md) | Install detail (includes Temporal, Ollama/vLLM) |
| [AUDIT.md](docs/AUDIT.md) | Deep verification report |
| [RESEARCH_NOTES.md](docs/RESEARCH_NOTES.md) | Background research |

---

## Architecture

<!-- TODO: Add architecture diagram -->
<!-- 
![Architecture Diagram](docs/screenshots/architecture.png)
*System architecture showing multi-agent design, Temporal integration, and RAG pipeline*
-->

## Layout

```
src/gateway/     # resilient LLM gateway (built)
src/dashboard/   # ops metrics (built)
src/nodes.py     # research nodes (prototype)
src/graph.py     # LangGraph
src/search.py    # Tavily
src/llm.py       # → gateway
main.py
test_gateway.py  # offline 9/9
docs/
scripts/install.sh | install.ps1
```

---

## Web UI

<!-- TODO: Add web UI screenshots -->
<!-- 
![Chat Interface](docs/screenshots/chat-ui.png)
*Chat interface with streaming responses and tool usage*

![Research Interface](docs/screenshots/research-ui.png)
*Research interface with progressive output and real-time progress*

![Export Options](docs/screenshots/export-ui.png)
*Export panel supporting Markdown, PDF, and HTML formats*
-->

---

## Example Output

<!-- TODO: Add example report screenshot -->
<!-- 
![Sample Report](docs/screenshots/sample-report.png)
*Sample research report with citations and mathematical formulas*
-->

The agent produces comprehensive research reports with:
- **Citations** — Every claim backed by sources
- **Mathematical formulas** — LaTeX rendering for equations
- **Progressive structure** — Section-by-section streaming
- **Export formats** — Markdown, PDF, HTML downloads

---

## License / contributing

Implement against [docs/ROADMAP.md](docs/ROADMAP.md). Specs are normative for the target product; AUDIT is normative for “what works today.”
