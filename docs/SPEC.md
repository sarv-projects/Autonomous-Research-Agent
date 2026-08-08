# Product specification (final)

**Version:** 2.0  
**Date:** 2026-08-08  
**Status:** Final **target** for implementation  

> **Reality check:** What the repository runs *today* is a subset (LangGraph + Tavily + gateway with API keys).  
> See **[AUDIT.md](AUDIT.md)** for the built-vs-target matrix. This SPEC remains the goal.

> **Major Update (v2.0):** Integration of LangGraph + Temporal plugin for durable execution, adversarial triangulation for bias mitigation, factoid extraction pipeline for 90% token reduction, dynamic task graph with live injection, and mathematical output rendering system.

---

## 1. Product statement

A **self-improving research and chat agent** that:

- Answers like a strong general assistant (**chat**)
- Produces **cited, progressive, high-signal research reports** (**research**)
- Uses **RAG + iterative tool loops** (not token stuffing)
- Plugs **any LLM endpoint** (empty URL = OpenCode free; `+` adds more)
- Installs easily on **Linux/macOS (Bash)** and **Windows (PowerShell)**
- **NEW: Crushes current SOTA through harness-first architecture with dynamic task graphs, relentless retrieval, bias mitigation, and token optimization**
- **NEW: Renders mathematical formulas and symbols properly via LaTeX/Unicode**

**Not the goal:** maximize tokens or emit one giant uncited blob.

---

## 2. Non-negotiable requirements

|| # | Requirement | Definition of done |
||---|-------------|-------------------|
|| R1 | **Powerful chat** | Multi-turn chat with optional tools + vault RAG; escalate to research |
|| R2 | **Powerful research** | Multi-iteration plan → gather → RAG → analyze → reflect → progressive write |
|| R3 | **Self-improving** | Vault reuse, run traces, strategy memory, source quality scores on every completed research run |
|| R4 | **Token reduction** | Full page bodies never enter main LLM context; only retrieved chunks |
|| R5 | **Progressive output** | Report written section-by-section (streamed), not one-shot generation |
|| R6 | **Mandatory citations** | Inline claim→source + end **Sources**; ship-gate fails without evidence for key claims |
|| R7 | **Quality dials** | ultra-fast · balanced · accurate · comprehensive (budgets, not separate codebases) |
|| R8 | **Universal providers** | Empty URL → OpenCode free; empty key → no auth; `+` provider/model; official-docs bases only |
|| R9 | **Modular tools** | MCP + local adapters (Tavily, wiki, Firecrawl, Exa, **MinerU/Nougat PDF parse**, …); graceful degrade |
|| R10 | **Dual install** | Documented + scripted Bash and PowerShell paths |
|| R11 | **Surfaces** | Primary **web app**; secondary **CLI**; desktop later as thin shell |
|| R12 | **Gateway** | All LLM calls through existing resilient gateway (failover, circuits, cost, metrics) |
|| R13 | **Evals** | Component suite in CI; research/efficiency/trajectory evals; ops metrics |
|| R14 | **Multi-agent roles** | Planner · Researcher · **Thinker** · Critic · Synthesizer · Compiler (not one super-agent) |
|| R15 | **Staged autonomy** | L1 Report (default) · L2 Human gate · L3 Unattended — explicit config |
|| R16 | **Fact-check** | Key claims verified / multi-source where possible before ship |
|| R17 | **Dynamic task graph** | User can inject new tasks mid-research; DAG auto-replans without restart |
|| R18 | **Relentless retrieval** | 3-tier retry pyramid (backoff → provider failover → semantic rephrase) |
|| R19 | **Adversarial triangulation** | Pro/Con/Neutral agents for subjective questions to cancel bias |
|| R20 | **Model-agnostic harness** | Constrained decoding forces identical output across models |
|| R21 | **Factoid extraction pipeline** | 90% token reduction via structured JSON extraction before synthesis |
|| R22 | **Durable execution** | LangGraph + Temporal plugin for 24h ultra-long research with checkpoint recovery |
|| R23 | **Mathematical output** | LaTeX/Unicode rendering for equations, formulas, and scientific notation |

Production rubric mapping: [PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md).

---

## 2b. Multi-agent roster (normative)

|| Agent | Responsibility | Default model / tier |
||-------|----------------|----------------------|
|| **Planner** | Decompose query → DAG of sections/subtasks, budgets, tool plan | `fast` |
|| **Researcher** | Execute tools (search, crawl, parse), ingest RAG | `fast` |
|| **Thinker** | Large-context reasoning only (no tools): replan, contradictions, deep structure | **Gemini free tier** (Flash preferred); fallback Zen/Groq |
|| **Critic** | Quality score, citation sampling, trigger retry/replan | `strong` or Thinker |
|| **Synthesizer** | Progressive section drafts from retrieved claims | `strong` |
|| **Compiler** | Assemble report, citation ship-gate, export | `fast` + deterministic checks |
|| **Triangulator** (NEW) | Adversarial pro/con/neutral agents for bias mitigation | Fast/Strong |
|| **Factoid Extractor** (NEW) | Structured JSON extraction from documents (cheap model) | Fast local |
|| **Retriever Guard** (NEW) | 3-tier retry pyramid with fallback routing | Fast |

**Thinker rules**

- Invoked for **large context** steps only (many sources, long outline, contradiction sets) — not every node.  
- **No tool calls** (smaller trust boundary).  
- Input: structured packs (claims, outlines, chunk summaries) — not raw page dumps when avoidable.  
- Output: structured JSON (plan deltas, scores, section briefs).  
- Rate-limit aware: respect Gemini free **RPM/TPM/RPD** from [AI Studio](https://aistudio.google.com/rate-limit); gateway backoff on 429.  
- Privacy: Free tier may use content to improve Google products per [Gemini pricing/terms](https://ai.google.dev/gemini-api/docs/pricing) — document for users; paid Gemini for zero training use.

---

## 2c. Staged autonomy (normative)

|| Level | Name | Behavior |
||-------|------|----------|
|| **L1** | Report | Run research → produce report; human always in the loop for trust (default) |
|| **L2** | Human gate | Interrupt after plan and/or before expensive waves / export |
|| **L3** | Unattended | Auto within hard $ / token / tool budgets; full audit log required |

---

## 3. Modes

|| Mode | Purpose | Default budget (tunable) |
||------|---------|---------------------------|
|| `chat` | Conversational Q&A | 0–2 tool calls; vault RAG |
|| `quick` | Fast brief | 1–2 gather waves |
|| `standard` | Default research | 3–6 waves |
|| `deep` | Heavy analysis | 8–15 waves + critique/patch |
|| `recency` | Last-N-days style | Parallel multi-source, recency bias |
|| `academic` | Papers-first | arXiv / scholar bias |
|| `compare` | A vs B | Structured matrix output |
|| `ultra-long` (NEW) | 24h deep dive | Durable execution with checkpoint recovery |

Quality dial overlays mode budgets:

|| Dial | Priority |
||------|----------|
|| **ultra-fast** | Minimize latency and tool calls |
|| **balanced** | Default |
|| **accurate** | More retrieval, critique, cite-check |
|| **comprehensive** | Higher coverage, more sections, deeper gaps |

---

## 4. Research loop (normative)

Plan–Act–Observe harness with specialized agents:

```
Planner (DAG/outline/budgets)
  → [optional Thinker: refine plan if large/complex]
  → Researcher: tool_select → gather → ingest → retrieve → analyze
  → [optional Thinker: contradiction / multi-source reason]
  → Critic/reflect (gaps|stop|retry) ↺
  → Synthesizer: outline → FOR EACH section: retrieve → draft(stream)
  → Critic: citations_pass / fact-check sample
  → Compiler: polish(patch-only) → export (ship-gate)
```

**NEW - Ultra-Long Horizon (24h mode):**

```
Temporal Workflow: LangGraph graph wrapped in TemporalGraph
  → Durable state checkpoints (every N steps)
  → Automatic recovery from process crashes
  → Heartbeating for long-running activities
  → Human-in-the-loop via Temporal signals (approval queue)
  → Cost and token budget enforcement at workflow level
```

**Stop when (any):**

- Mode budget exhausted (iters / tools / USD)
- Marginal new high-quality claims below threshold
- Outline coverage confidence ≥ target

**Ship gate:**

- [ ] End **Sources** section present
- [ ] ≥ N% of key claims have evidence ids
- [ ] No empty report body
- [ ] Progressive write completed (not single full regenerate)

---

## 5. Chat loop (normative)

```
message → intent(chat | tools | research)
  → if chat: LLM + optional vault hybrid RAG
  → if tools: short ReAct (budgeted)
  → if research: hand off same thread_id / vault / vector namespace
```

---

## 6. Providers (normative summary)

Full detail: [PROVIDERS.md](PROVIDERS.md).

|| Rule | Behavior |
||------|----------|
|| Empty `base_url` | Resolve to `https://opencode.ai/zen/v1` (OpenCode free) |
|| Empty `api_key` | Send **no** `Authorization` header |
|| Non-empty URL | Use as OpenAI-compatible (or protocol-specific) base |
|| `+` provider / `+` model | User-extensible list; optional `GET {base}/models` |
|| Model IDs | Official docs or live catalog only — **no invented/outdated defaults** |

**First-wave presets:** OpenCode free, NVIDIA NIM, OpenRouter, North Mini Code (Zen/OR), Cohere Platform (Command), OpenAI, Claude, Gemini, Groq, DeepSeek (`deepseek-v4-flash` / `deepseek-v4-pro`), MiMo (Zen/OR), custom.

---

## 7. RAG / vector DB (normative)

|| Backend | Role |
||---------|------|
|| **LanceDB** | Default embedded (ultra-fast local, zero Docker) |
|| **Qdrant** | Production multi-user |
|| **SQLite FTS5** | Always-on keyword fallback |

Hybrid dense + FTS. Collections: run corpus, vault, chat memory.

**NEW - Factoid Extraction Pipeline:**

```
Document → Normalization (trafilatura/MarkItDown) → Structural chunking
  → Cheap model extraction (Llama 3 8B) → Structured JSON factoids
  → Anti-hallucination gate (quote verification) → Deduplication/merging
  → PostgreSQL/pgvector storage → Hybrid retrieval for synthesis
```

Token reduction: ~90% vs raw document dumping.

---

## 8. Surfaces

|| Surface | Priority |
||---------|----------|
|| Web app (chat, research, vault, runs, eval, provider UI with `+`) | **Primary** |
|| CLI (`chat`, `research`, `doctor`, `eval`, `history`) | **Secondary** |
|| Gateway ops dashboard (`/metrics`, circuits) | Built |
|| Desktop shell | Deferred (wrap web) |

---

## 9. Self-improvement (normative)

On every completed research run:

1. Persist sources as vault notes (markdown + FTS/vectors)
2. Append structured run trace (JSONL)
3. Write strategy memory entry (what worked / failed / preferred sources)
4. Update source-quality scores when cite-check fails or user rates

Next similar query: **search vault before paid fetch**.

---

## 10. MCP tools (priority)

|| Tool | Role | Required for MVP |
||------|------|------------------|
|| Tavily (local) | Web search | Yes (or equivalent) |
|| Wikipedia | Background facts | Prefer free default |
|| Firecrawl | Clean crawl | Optional |
|| Exa | Neural search | Optional |
|| arXiv | Papers | Prefer free |
|| **MinerU** | PDF/Office → Markdown (primary parser) | Optional Phase D+ (recommended for academic/deep) |
|| **Nougat** | Academic PDF math specialist | Optional (non-commercial weight license) |
|| Vault tools | Prior research | Yes (local) |
|| Browser escalation | Hard pages | Optional |

---

## 11. Acceptance criteria (MVP vertical slice)

- [ ] Install works on Bash and PowerShell with docs scripts
- [ ] Empty provider URL uses OpenCode free models without API key
- [ ] `+` can add a custom OpenAI-compatible base URL + model
- [ ] Chat mode responds multi-turn
- [ ] Research mode runs ≥2 iterations when gaps exist (budget allowing)
- [ ] RAG ingest + retrieve used; synthesis path does not dump full pages
- [ ] Report has progressive sections + end Sources with URLs
- [ ] Traces written under `data/traces/`
- [ ] `doctor` shows provider/tool readiness
- [ ] Offline component evals pass in CI
- [ ] **NEW**: Dynamic task injection mid-research without restart
- [ ] **NEW**: Factoid extraction reduces tokens by ≥80%
- [ ] **NEW**: Mathematical symbols render properly in reports
- [ ] **NEW**: Adversarial triangulation reduces bias in subjective queries

---

## 12. Out of scope (deferred)

- Full STORM multi-agent fleet
- Postgres LangGraph checkpointing / HITL production polish
- K8s, OTEL mega-stack, HTTP sidecar gateway
- Native Electron desktop rewrite
- Weight fine-tuning (traces only first)

---

## 13. Related docs

- Architecture → [ARCHITECTURE.md](ARCHITECTURE.md)
- Providers → [PROVIDERS.md](PROVIDERS.md)
- Evals → [EVALS.md](EVALS.md)
- Install → [INSTALL.md](INSTALL.md)
- Roadmap → [ROADMAP.md](ROADMAP.md)
- Gateway (built) → [GATEWAY.md](GATEWAY.md)
- Factoid Pipeline → [FACTOID_PIPELINE.md](FACTOID_PIPELINE.md) (NEW)
