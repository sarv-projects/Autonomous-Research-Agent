# Architecture

**Version:** 2.1 · Live graph: **A4** (`src/graph.py`) · Aligns with [SPEC.md](SPEC.md)  
**Benchmarks / arch IDs:** [ARCHITECTURE_BENCHMARKS.md](ARCHITECTURE_BENCHMARKS.md) · **README** has the user-facing architecture + product DR comparison.

> **A4 (current):** Scout (Exa + Gemini×3) → plan → research loop → devil’s advocate → claim adjudicator (Socratic hop) → triangulator → synth → compiler (Evidence Bedrock + Research Debt + Sources).  
> Workhorse LLM: Groq; search: Exa; RAG: LanceDB+FTS with `run_id` isolation.

---

## 1. System overview

```
┌──────────────────────────────────────────────────────────────────┐
│  Surfaces                                                         │
│   Web (Next.js) · CLI (main.py) · FastAPI /docs                   │
│   Jobs + SSE thinking panel (learned / gaps / next)               │
└────────────────────────────┬─────────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────┐
│  Router                                                           │
│   chat | quick | standard | deep | recency | academic | compare  │
│   + quality dial: fast | balanced | accurate | comprehensive     │
│   + autonomy L1 / L2 (plan review) / L3                          │
└────────────────────────────┬─────────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────┐
│  Engine (LangGraph + optional Temporal)                           │
│                                                                   │
│  RESEARCH (A4):                                                   │
│   scout → plan → refine                                           │
│   gather → analyze → contradiction → critic → search_strategy ↺  │
│   devil_advocate → adjudicator → [socratic gather?]               │
│   triangulate → outline → parallel write → compile                │
│   export: Inference + Bedrock + Research Debt + Sources           │
│                                                                   │
│  CHAT:                                                            │
│   intent → LLM [+ vault RAG] | short tools | escalate research   │
│                                                                   │
│  State: claims[], gaps[], scout{}, run_id, debt, adjudicated[]   │
│                                                                   │
│  Durable (Temporal, optional):                                    │
│   Checkpoint recovery, ultra-long mode, HITL signals              │
└───────────┬─────────────────────────────┬────────────────────────┘
            │                             │
┌───────────▼───────────┐   ┌─────────────▼────────────────────────┐
│  RAG / VectorStore    │   │  Tool bus                             │
│  LanceDB | Qdrant     │   │  Registry + MCP + local adapters      │
│  FTS fallback         │   │  Tavily, wiki, firecrawl, exa, vault  │
│  vault · chat memory  │   └─────────────┬────────────────────────┘
└───────────────────────┘                 │
┌─────────────────────────────────────────▼────────────────────────┐
│  NEW - Factoid Extraction Pipeline                               │
│  Normalization → Chunking → Cheap Model Extraction → JSON      │
│  Anti-hallucination gate → Deduplication → pgvector storage    │
└─────────────────────────────────────────┬────────────────────────┘
                                          │
┌─────────────────────────────────────────▼────────────────────────┐
│  NEW - Adversarial Triangulation Engine                             │
│  Pro/Con/Neutral agents → Synthesis Arbiter → Bias-cancelled output │
└─────────────────────────────────────────┬────────────────────────┘
                                          │
┌─────────────────────────────────────────▼────────────────────────┐
│  Self-improve: traces · strategy_memory · source_quality · vault  │
└─────────────────────────────────────────┬────────────────────────┘
                                          │
┌─────────────────────────────────────────▼────────────────────────┐
│  LLM Gateway (built): routes, circuits, retries, rate limit, cost │
│  Provider slots: empty URL=Zen free; + custom; multi-protocol     │
└──────────────────────────────────────────────────────────────────┘
```

---

## 2. Design principles

1. Signal over tokens — retrieve, don't dump  
2. Gap-driven iteration — fetch only what's missing  
3. Progressive write — never one megaprompt report  
4. Citations as ship gate  
5. Self-improve on every run  
6. Modular tools and providers  
7. Gateway under every LLM call  
8. **Specialized agents**, not one super-agent  
9. **Deterministic harness** owns budgets, autonomy, allowlists, ship-gate  
10. **Staged autonomy** L1–L3  
11. **NEW: Durable execution via Temporal** — survives crashes, 24h runs, HITL  
12. **NEW: Model-agnostic via constrained decoding** — harness enforces consistency  
13. **NEW: Bias mitigation via adversarial triangulation** — mechanically cancels model bias  
14. **NEW: Token optimization via factoid extraction** — 90% reduction vs raw dumping  

---

## 2b. Multi-agent design

```
Planner ──► Researcher ──► Thinker(optional) ──► Critic ──► Synthesizer ──► Compiler
   │              │                │                 │
   │              └──── tools ─────┘                 │
   └──────────── DAG / budgets / autonomy ───────────┘

NEW (bias mitigation):
Triangulator ──► Pro Agent ──► Con Agent ──► Neutral Agent ──► Synthesis Arbiter
```

| Agent | Input | Output | Tools | Default LLM |
|-------|-------|--------|-------|-------------|
| **Planner** | user query, vault hints, strategy memory | DAG, outline, budgets | vault read | fast |
| **Researcher** | subtasks | raw docs → RAG claims | search, crawl, parse | fast |
| **Thinker** | large structured context packs | plan deltas, scores, briefs | **none** | **Gemini free (Flash)** |
| **Critic** | claims, draft sections | pass/fail, gaps, retries | vault + sample sources | strong / thinker |
| **Synthesizer** | outline + retrieved claims | streamed sections | RAG only | strong |
| **Compiler** | sections + evidence map | final MD + Sources | export, cite-check | fast + rules |
| **Triangulator** (NEW) | subjective/controversial questions | pro/con/neutral perspectives | search, vault | fast/strong |
| **Factoid Extractor** (NEW) | documents, chunks | structured JSON factoids | none | fast local (Llama 3 8B) |
| **Retriever Guard** (NEW) | search queries | sources with verification | search APIs | fast |

### Thinker agent (Gemini free tier)

**Purpose:** large-context thinking without tool side effects.

| Setting | Value |
|---------|--------|
| Provider | Gemini via `https://generativelanguage.googleapis.com/v1beta/openai/` |
| Auth | `GEMINI_API_KEY` / `GOOGLE_API_KEY` |
| Preferred models | Free-eligible **Flash** (e.g. `gemini-3.6-flash` / current Flash in AI Studio) for context + speed |
| Fallback | OpenCode free strong · Groq · DeepSeek v4 |
| Invoke when | Accurate/comprehensive dials; many sources; contradiction sets; plan refinement |
| Do not invoke | Every micro-step; ultra-fast mode (skip or cheap fast model) |

**Rate limits (official):** per-project, per-model **RPM / TPM / RPD** — see live [AI Studio rate limits](https://aistudio.google.com/rate-limit) and [docs](https://ai.google.dev/gemini-api/docs/rate-limits). Free tier: no spend-based 10-min cap. Enforce gateway RPM for Gemini; exponential backoff on 429. Free tier may use data to improve Google products ([pricing](https://ai.google.dev/gemini-api/docs/pricing)).

Harness isolation: Thinker cannot call tools; only returns structured JSON consumed by Planner/Critic/Synthesizer.

### Triangulator agent (NEW - bias mitigation)

**Purpose:** mechanically cancel model bias via adversarial triangulation for subjective/controversial questions.

| Setting | Value |
|---------|--------|
| Providers | Multiple (e.g., OpenAI, Anthropic, Google) |
| Auth | Multi-provider API keys |
| Models | Fast models per provider |
| Invoke when | Subjective questions, controversial topics, political/social issues |
| Do not invoke | Factual queries, technical documentation, code analysis |

**Architecture:**
1. **Pro Agent** — instructed to argue for the proposition
2. **Con Agent** — instructed to argue against the proposition
3. **Neutral Agent** — instructed to present balanced view
4. **Synthesis Arbiter** — compares outputs, identifies bias, generates neutral synthesis

**Bias Cancellation Mechanism:**
- Explicitly different system prompts for each agent
- Cross-agent critique to identify biased framing
- Arbiter uses gap-aware evidence assembly to find common ground
- Citations required for all claims
- Final output includes bias assessment score

**Related Research:**
- Bias-Targeted Adversarial Preference Optimization (B-APO)
- Causal-Contrastive Preference Optimization (C2PO)
- CatRAG Debiasing for retrieval-level bias mitigation

### Factoid Extractor agent (NEW - token optimization)

**Purpose:** extract structured JSON factoids from documents for token-efficient RAG.

| Setting | Value |
|---------|--------|
| Provider | Local inference (vLLM/Ollama) |
| Models | Llama 3 8B, Phi-3, or similar local models |
| Invoke when | Document ingestion, chunk processing |
| Do not invoke | Real-time queries (use cached factoids) |

**Architecture:**
1. Input: document or chunk
2. Output: structured JSON with factoid type, value, confidence, source reference
3. Factoid types: entity, relation, event, statistic, definition, citation
4. Stored in vector database with metadata
5. Used for gap-aware evidence assembly in RAG

**Token Savings:**
- Original chunk: ~10K tokens
- Extracted factoids: ~1K tokens (90% reduction)
- Retrieval operates on factoids, not raw chunks
- Synthesizer reconstructs context from factoids

**Related Research:**
- SARA (Selective and Adaptive Retrieval-augmented Generation with Context Compression)
- CompactRAG for context compression
- AdaGATE for gap-aware evidence assembly

### Retriever Guard agent (NEW - source verification)

**Purpose:** verify source credibility and filter low-quality/contaminated sources.

| Setting | Value |
|---------|--------|
| Provider | Fast model (GPT-4o-mini, Claude Haiku) |
| Auth | Standard API keys |
| Invoke when | Search results returned, before RAG |
| Do not invoke | Cached trusted sources |

**Architecture:**
1. Input: search result URLs, snippets
2. Analysis: domain reputation, content freshness, citation quality
3. Output: filtered source list with credibility scores
4. Blocks: hallucinated URLs, SEO spam, low-quality content farms
5. Promotes: peer-reviewed sources, official documentation, reputable news

**Verification Criteria:**
- Domain age and authority (via external API or heuristics)
- Cross-reference with trusted sources
- Content freshness (for time-sensitive queries)
- Citation density and quality
- Bias detection (via triangulation if needed)

---

Full production rubric map: [PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md).

---

## 3. Research pipeline detail

| Step | Responsibility | Token rule |
|------|-----------------|------------|
| `plan` | Sub-questions, tool plan, outline seeds | Small JSON |
| `tool_select` | Capability tags → registry tools | Small JSON |
| `gather` | Parallel tool calls; store bodies on disk | Metadata in graph state only |
| `verify_sources` (NEW) | Retriever Guard filters and scores sources | Small JSON |
| `ingest` | Chunk + embed + upsert VectorStore | No LLM or tiny |
| `extract_factoids` (NEW) | Factoid Extractor processes chunks to JSON | Structured JSON |
| `retrieve` | Hybrid query for active sub-q / section (factoids) | Top-k only into LLM |
| `triangulate` (NEW) | Triangulator for subjective/controversial queries | Multi-perspective |
| `analyze` | Claims + evidence_ids + gaps | Structured list |
| `reflect` | Continue vs stop; next queries | Small JSON |
| `outline` | Final report skeleton | Small |
| `section_write` | Per-section draft with local retrieve | Stream; section-scoped context |
| `citations` | Bind claims to sources; block if broken | Sampled checks |
| `polish` | Surgical patch only (no full regen) | Diff-sized |
| `export` | Markdown + optional HTML; path to vault | — |

### Progressive output contract

```
stream: outline
for section in outline.sections:
    stream: section title
    stream: section body (token stream)
stream: Sources (mandatory)
```

UI/CLI must show progress per section, not a single spinner then wall of text.

---

## 4. Chat pipeline detail

| Step | Behavior |
|------|----------|
| Intent | `chat` · `tools` · `research` |
| Pure chat | Gateway LLM + hybrid vault/chat memory retrieve |
| Tools | Budgeted ReAct (search/wiki/vault) |
| Escalate | Same `thread_id`, shared vault namespace |

---

## 4b. Document parsing (PDF / Office → Markdown for RAG)

When research hits **PDFs, papers, DOCX, slides, scans**, convert to structured text **before** chunk/ingest. Do not OCR by stuffing images into the main chat model.

| Engine | Role in our stack | When to use |
|--------|-------------------|-------------|
| **[MinerU](https://github.com/opendatalab/MinerU)** (~77k★) | **Primary** document parser | PDF, DOCX, PPTX, XLSX, images; formulas→LaTeX; tables→HTML; RAG/MCP-oriented; pipeline / VLM / hybrid backends; offline-capable |
| **[Nougat](https://github.com/facebookresearch/nougat)** (~10k★) | **Optional specialist** | arXiv/PMC-style **academic PDFs** with heavy LaTeX math; English-best; weights **CC-BY-NC** (non-commercial) |
| Tavily / Firecrawl extract | Web HTML | Normal web pages (not PDF layout reconstruction) |

**Flow:**

```
url or file → download → parser (MinerU default | Nougat if academic-math flag)
  → markdown/json → rag.ingest → retrieve in analyze/section_write
```

**Integration style (modular, same as MCP tools):**

- Adapter `tools/adapters/mineru.py` — CLI or local `mineru-api` / REST  
- Optional `tools/adapters/nougat.py` — `nougat path.pdf -o …` or `nougat_api`  
- Registry tags: `parse_pdf`, `parse_office`, `parse_academic`  
- Escalation: if Tavily raw_content is empty and URL ends in `.pdf` → MinerU  

**Install notes:** both need **GPU for speed** (MinerU pipeline can CPU; Nougat slow on CPU). Keep **optional extras** (`mineru`, `nougat-ocr`) so default `uv sync` stays light. Prefer Docker/API sidecar for production workers.

**Not a replacement for web search** — only the **ingest quality** layer for documents that already have a URL or local path.

---

## 4c. Tool bus performance

The tool registry (`src/tools/registry.py`) layers three speed/coverage optimizations on top of the adapter set:

| Mechanism | What it does | Tuning |
|-----------|--------------|--------|
| **TTL search cache** | Repeated/overlapping sub-queries within a run (or across overlapping runs) hit an in-process cache instead of re-paying the provider. Only successful (non-empty) results are cached so failures can retry. | `TOOL_SEARCH_CACHE_TTL_S` (default 600) · `TOOL_SEARCH_CACHE_MAX` (default 256) |
| **Parallel extraction** | URLs are fetched concurrently instead of one-by-one. Batch-API tools (Exa `/contents`, Tavily `/extract`, Wikipedia) keep a single batch call; per-URL extractors (Firecrawl, builtin scraper, MinerU, Nougat) are sharded across a bounded worker pool. | — |
| **Provider fusion** | With `TOOL_FUSE_SEARCH=1`, the top `web_search` providers run **concurrently** and results are merged by URL instead of the sequential fallback chain — broader coverage in one round-trip. Off by default to avoid surprising rate limits. | `TOOL_FUSE_SEARCH` (`1`/`0`) |

Search-cache telemetry (entries, TTL, hit/miss rate) is surfaced in the ops dashboard — see [GATEWAY.md](GATEWAY.md).

---

## 5. RAG layer

```python
class VectorStore(Protocol):
    def upsert(self, chunks: list[Chunk]) -> None: ...
    def query(self, embedding: list[float], k: int, filters: dict | None) -> list[ScoredChunk]: ...
    def hybrid_query(self, text: str, embedding: list[float], k: int, filters: dict | None) -> list[ScoredChunk]: ...
    def delete(self, filter: dict) -> None: ...
```

| Backend | Default for |
|---------|-------------|
| LanceDB | Local / single-user / easy install |
| Qdrant | Multi-user production (`VECTOR_BACKEND=qdrant`) |
| SQLite FTS5 | Fallback when embeddings unavailable |

Chunking: ~500–800 tokens, ~10% overlap. Metadata: `run_id`, `url`, `title`, `source_type`, `chunk_id`.

---

## 6. Provider layer

See [PROVIDERS.md](PROVIDERS.md).

```text
resolve_base("")  → https://opencode.ai/zen/v1
auth_headers("") → {}
auth_headers(k)  → Authorization: Bearer k
```

Protocols: `openai_chat` (default) · `anthropic_messages` · `cohere_v2_chat`.

Tiers (`fast` / `strong`) = ordered lists of `provider_slot/model_id` with failover through the gateway.

---

## 7. Module layout (target)

```
src/
  gateway/           # BUILT — resilience, metrics
  dashboard/         # BUILT — ops UI
  llm.py             # call_llm* → gateway
  engine/
    modes.py
    router.py
    graph_research.py
    graph_chat.py
    state.py
    temporal/        # NEW — Temporal.io integration for durable execution
    nodes/           # plan, gather, ingest, retrieve, analyze, reflect,
                     # outline, section_write, citations, polish, export
    agents/          # NEW — specialized agent implementations
                       # planner, researcher, thinker, critic, synthesizer, compiler
                       # triangulator, factoid_extractor, retriever_guard
  rag/
    chunk.py
    embed.py
    store.py
    backends/        # lancedb, qdrant, fts
    factoid/         # NEW — factoid extraction and storage
  tools/
    registry.py
    executor.py
    mcp_manager.py
    adapters/
  vault/
  improve/           # traces, strategy, quality
  chat/
  eval/
  web/               # primary product UI + API
  providers/         # catalog load, presets, resolve_base
main.py              # CLI multi-command
config/
  providers.example.yaml
  modes.yaml
  temporal.yaml      # NEW — Temporal workflow configuration
scripts/
  install.sh
  install.ps1
data/                # traces, vault, lance (gitignored)
reports/             # exported markdown
```

Legacy `src/nodes.py` / `src/graph.py` remain until migration complete.

---

## 8. Temporal integration (NEW - durable execution)

**Purpose:** Enable 24h+ research runs, automatic crash recovery, and human-in-the-loop workflows via Temporal.io.

### Architecture

```
LangGraph Agent
    ↓
Temporal Workflow (Python SDK)
    ↓
Temporal Server (durable execution engine)
    ↓
Persistent State + Activity Workers
```

### Key Benefits

1. **Crash Recovery** — Research runs survive process crashes, network failures, and server restarts
2. **24h+ Execution** — No timeout limits; state persisted to Temporal backend
3. **Human-in-the-Loop** — Pause workflows for human approval, manual verification, or intervention
4. **Automatic Retries** — Configurable retry policies for transient failures
5. **Distributed Execution** — Scale horizontally across multiple workers
6. **Observability** — Built-in workflow history, event logs, and execution tracking

### Integration Points

| Component | Temporal Role |
|-----------|--------------|
| `engine/graph_research.py` | Temporal Workflow |
| `engine/nodes/*` | Temporal Activities |
| `engine/temporal/` | Workflow definitions, worker setup |
| `config/temporal.yaml` | Temporal server config, task queues |

### Workflow Example

```python
from temporalio import workflow

@workflow.defn
class ResearchWorkflow:
    @workflow.run
    async def run(self, query: str, config: dict) -> str:
        # Planner activity
        plan = await workflow.execute_activity(
            "plan_research",
            args=[query],
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        # Parallel research activities
        results = await asyncio.gather(*[
            workflow.execute_activity(
                "research_subtask",
                args=[subtask],
                start_to_close_timeout=timedelta(minutes=30)
            )
            for subtask in plan.subtasks
        ])
        
        # Synthesis
        report = await workflow.execute_activity(
            "synthesize_report",
            args=[results],
            start_to_close_timeout=timedelta(minutes=15)
        )
        
        return report
```

### Configuration

```yaml
# config/temporal.yaml
temporal:
  server_address: "localhost:7233"
  namespace: "default"
  task_queue: "research-queue"
  workflow_execution_timeout: "24h"
  activity_timeout: "30m"
  retry_policy:
    max_attempts: 3
    initial_interval: "1s"
    max_interval: "60s"
```

### LangGraph + Temporal Pattern

1. LangGraph defines the agent DAG and control flow
2. Temporal wraps the graph execution as a durable workflow
3. Each LangGraph node becomes a Temporal activity
4. State transitions persist to Temporal history
5. Long-running research can span hours/days with checkpoints

### Related Documentation

- [Temporal Python SDK](https://docs.temporal.io/dev-guide/python)
- [LangGraph Temporal Integration](https://langchain-ai.github.io/langgraph/concepts/temporal/)
- [Temporal Architecture](https://docs.temporal.io/concepts/what-is-temporal)

---

## 9. Self-improvement data flow

```
run complete
  → vault.notes += sources (markdown + index)
  → data/traces/<run_id>.jsonl
  → strategy_memory.jsonl (topic tags, tactics)
  → quality scores updated
next plan()
  → vault.search + strategy match injected
```

---

## 10. Security notes

- Web-fetched bodies treated as untrusted data (fence in prompts)
- Provider secrets: env or encrypted store; never commit `.env`
- Virtual keys / BYOK remain gateway-level for multi-tenant later
- Free open endpoints (Zen free): no key; privacy per provider terms

---

## 10. Reference research (summary)

Studied for patterns (not for copy-paste): Hyperresearch, DeerFlow, last30days, STORM, Tongyi DeepResearch, MiroThinker, Enterprise Deep Research, BrowserPilot. Detailed notes: [RESEARCH_NOTES.md](RESEARCH_NOTES.md).
