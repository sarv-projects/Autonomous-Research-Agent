# Implementation roadmap (final)

Priority order. Old “Phase 2–4” (Postgres HITL fleet, K8s) remain **deferred** until engine product is solid.

---

## Done (current codebase)

| Item | Location |
|------|----------|
| LangGraph research prototype (9 nodes, Tavily) | `src/nodes.py`, `src/graph.py` |
| Resilient LLM gateway | `src/gateway/` |
| Ops dashboard + Prometheus | `src/dashboard/` |
| Offline gateway tests | `test_gateway.py` |
| Specs & architecture docs | `docs/` |

---

## Phase A — Providers + modes + CLI surfaces

- Provider slots: empty URL → OpenCode free; empty key → no auth; `+` models  
- Presets: NIM, OpenRouter, OpenAI, Claude, Gemini, Groq, DeepSeek v4, MiMo, North Mini (Zen/OR)  
- `doctor`, `chat` stub, `research --mode`  
- Modes + budgets + quality dials  

**Exit:** chat works on Zen free; doctor lists providers.

---

## Phase B — RAG + VectorStore

- LanceDB default + FTS fallback + Qdrant adapter  
- Gather → ingest → retrieve for analyze/section write  
- Prove token cut vs page-dump baseline  

**Exit:** synthesis/section paths never receive full multi-page dumps.

---

## Phase C — Multi-iteration research + multi-agent skeleton

- Agent roles as graph nodes: **Planner · Researcher · Critic · Synthesizer · Compiler**  
- plan → gather → ingest → retrieve → analyze → reflect ↺  
- Progressive outline + section write + **citations ship-gate**  
- Autonomy **L1** default; hooks for L2 interrupts  

**Exit:** multi-iter cited report with clear agent boundaries in traces.

---

## Phase C2 — Thinker agent (Gemini free)

- Wire Gemini OpenAI-compat provider (`GEMINI_API_KEY`)
- **Thinker** node: large-context only, **no tools**, structured JSON out
- Rate-limit policy for free tier (RPM/TPM/RPD from AI Studio + 429 backoff)
- Invoke only on accurate/comprehensive or large packs
- Fallback chain if free quota exhausted

**Exit:** deep runs use Thinker for plan/contradiction steps without blowing free quota on every call.

---

## Phase C3 — Temporal integration (durable execution)

- Temporal.io Python SDK integration
- Wrap LangGraph research graph as Temporal workflow
- Convert LangGraph nodes to Temporal activities
- Configure Temporal server connection and task queues
- Implement crash recovery and workflow resumption
- Add human-in-the-loop pause/approval capabilities
- Set up 24h+ execution timeouts with checkpoints
- Configure retry policies for transient failures

**Exit:** research runs survive crashes, support 24h+ execution, and enable HITL workflows.

---

## Phase D — MCP tool bus + document parsers

- Registry + MCP manager  
- Wikipedia, Firecrawl, Exa (optional)  
- **MinerU** adapter (primary PDF/Office → MD for RAG)  
- Optional **Nougat** for academic-math PDFs (license-aware)  
- Tool-selection component evals  

**Exit:** tools pluggable without graph rewrite; PDF URLs can be ingested cleanly.

---

## Phase E — Bias mitigation (Triangulator agent)

- Implement Triangulator agent for subjective/controversial queries
- Multi-provider setup (OpenAI, Anthropic, Google)
- Pro/Con/Neutral agent system prompts
- Synthesis Arbiter for bias detection and neutral output
- Bias assessment scoring
- Integration with research pipeline for triggered queries
- Citations enforcement for all claims

**Exit:** subjective questions receive balanced, bias-mitigated outputs with explicit bias scores.

---

## Phase F — Factoid extraction pipeline (token optimization)

- Implement Factoid Extractor agent with local inference (vLLM/Ollama)
- Set up Llama 3 8B or Phi-3 for local factoid extraction
- Define factoid schema (entity, relation, event, statistic, definition, citation)
- Implement chunk → factoid JSON conversion
- Store factoids in vector database with metadata
- Implement gap-aware evidence assembly (AdaGATE pattern)
- Update RAG retrieval to operate on factoids instead of raw chunks
- Implement context reconstruction from factoids in Synthesizer
- Token efficiency validation (target 90% reduction)

**Exit:** RAG operates on compressed factoids, achieving 90% token reduction while maintaining quality.

---

## Phase G — Retriever Guard (source verification)

- Implement Retriever Guard agent for source credibility filtering
- Domain reputation analysis (external API or heuristics)
- Content freshness detection
- Citation quality scoring
- Block low-quality sources (SEO spam, content farms)
- Promote high-quality sources (peer-reviewed, official docs)
- Integration with search pipeline before RAG
- Caching for trusted sources

**Exit:** search results are filtered for credibility before RAG, reducing hallucination risk.

---

## Phase H — Vault + self-improve

- Cross-run vault  
- Traces + strategy memory + source quality  
- Vault-first on plan  

**Exit:** second similar topic reuses vault before paid fetch.

---

## Phase I — Critique / fact-check / deep / browser

- Critic quality bar + fact-check sample + patch-only polish  
- Deep mode budgets  
- Optional browser MCP on crawl failure  
- Autonomy **L2** human gates  

---

## Phase J — Evals harden (EvalOps)

- Component suite CI  
- Trajectory + efficiency + research rubric  
- Eval UI tab  
- Prompt store versioning (dev/staging/prod tags)  

---

## Phase K — Web product (primary UX)

- Chat + research streaming
- Provider UI (`+` provider / `+` model)
- Vault browser, run history, cost meter
- Merge ops metrics
- Product API surface (API-first)

---

## Phase L — Mathematical output rendering

- Implement MathJax/KaTeX integration for markdown rendering
- LaTeX syntax detection and validation
- Formula preprocessing and sanitization
- Inline math (`$...$`) and block math (`$$...$$`) support
- Symbol enrichment via constrained decoding
- Multi-modal model integration for equation images
- Export formats: HTML with MathJax, PDF with proper math typesetting
- Accessibility features (MathML output, screen reader support)

**Exit:** research reports render mathematical symbols correctly across all output formats.

---

## Deferred (enterprise scale)

| Item | Why later |
|------|-----------|
| Postgres checkpointing / full HITL productization | Engine first |
| A2A protocol, multi-process agents | Internal contracts first |
| K8s, message queues, OTEL mega-stack | After correctness |
| Zero-trust agent identity catalog, sandbox fleet | Enterprise phase |
| Online production evals + A/B platform | After offline evals |
| Desktop app | Thin shell over web when demanded |
| Weight training | Traces first |
| Distributed Temporal cluster | Single-node Temporal first |
| Multi-tenant factoid pipeline | Single-tenant factoid pipeline first |

---

## Suggested first PR (vertical slice)

**A + B seed + citations stub + install scripts:**

1. `src/providers/` config + Zen free default
2. `rag/` LanceDB + FTS
3. Engine graph with reflect loop (Tavily) + progressive export
4. CLI: `chat`, `research`, `doctor`
5. `scripts/install.sh` + `install.ps1`
6. Component eval scaffold

**Second PR (bias mitigation + durable execution):**

1. Temporal.io integration (Phase C3)
2. Triangulator agent (Phase E)
3. Factoid extraction pipeline (Phase F)
4. Retriever Guard (Phase G)

See [SPEC.md §11](SPEC.md) acceptance criteria.
