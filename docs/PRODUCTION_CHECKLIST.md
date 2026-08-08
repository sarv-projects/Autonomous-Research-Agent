# Production checklist gap analysis

**Date:** 2026-08-08  
**Sources:** User production rubric · [SPEC.md](SPEC.md) · [ARCHITECTURE.md](ARCHITECTURE.md) · [AUDIT.md](AUDIT.md) · live code  

**Legend**

| Symbol | Meaning |
|--------|---------|
| ✅ | In **target** SPEC / ARCHITECTURE (or built in code) |
| 🔧 | Target design; **not built** yet (roadmap) |
| ⚠️ | Partial / weaker than rubric |
| ❌ | Not in scope yet (deferred or missing) |
| 🟢 | **Built in repo today** |

---

## 1. Core architecture

| Rubric item | Status | Our mapping |
|-------------|--------|-------------|
| Multi-agent (Planner, Researcher, Critic, Synthesizer, Compiler) | 🔧 → **✅ design** | Extended agent roster: **Planner · Researcher · Thinker · Critic · Synthesizer · Compiler** (+ optional Verifier). Not a single super-agent long-term. Today 🟢 is still a **monolithic 9-node** graph. |
| Modular & decoupled (LLM ≠ business logic ≠ tools) | ⚠️ / 🔧 | Gateway separates LLM transport 🟢. Tools/state still mixed in `nodes.py`. Target: `engine/` + `tools/` registry + MCP. |
| MCP | 🔧 | Phase D. |
| A2A (Agent-to-Agent protocol) | ❌ / 🔧 late | Not day-1; internal message contracts first; A2A optional later for multi-process agents. |
| Deterministic harness (Plan-Act-Observe) | 🔧 | Research loop = plan → act (tools) → observe (analyze/reflect). Explicit budgets + ship gates. |
| Staged autonomy L1/L2/L3 | 🔧 **added** | **L1 Report** (default) · **L2 Human gate** · **L3 Unattended** — see SPEC § autonomy. |

---

## 2. Core capabilities

| Rubric item | Status | Our mapping |
|-------------|--------|-------------|
| Advanced planning / DAG of subtasks | 🔧 | Planner emits outline + dependency-aware section DAG (not only linear list). Reflect can replan edges. |
| Adaptive multi-step | 🔧 | Reflect loop + gap-fill; Critic can force replan. |
| Web search | 🟢 / 🔧 | Tavily 🟢; Exa/Firecrawl/wiki 🔧 |
| Internal data / enterprise APIs | 🔧 late | MCP adapters + tool registry; not MVP. |
| Document intelligence (PDF/OCR) | 🔧 | **MinerU** primary · **Nougat** optional (academic math). |
| File systems & apps (e.g. Drive) | ⚠️ / 🔧 late | Local report write 🟢; Drive/MCP filesystem later. |
| Short-term memory | ⚠️ | LangGraph state 🟢; chat session memory 🔧 |
| Long-term memory (vector + structured) | 🔧 | LanceDB/Qdrant + SQLite FTS + vault (not Chroma-only; same role). |
| Self-correction / quality gates | 🔧 | Critic + citations ship-gate + retry; model/tool switch via gateway routes. |
| Automated output + citations | ⚠️ / 🔧 | Markdown export 🟢; progressive write + mandatory cite-check 🔧 |

---

## 3. Enterprise non-functionals

| Rubric item | Status | Our mapping |
|-------------|--------|-------------|
| Zero-trust agent identity | ❌ / 🔧 late | Virtual keys / tenants in gateway 🟢 seed; full ZT later. |
| Data sovereignty / on-prem | ⚠️ | Local install + optional self-host LLM/vector; free cloud APIs leave boundary. |
| Sandboxed execution | ❌ / 🔧 late | Deferred (DeerFlow-style sandbox). |
| Full traceability | ⚠️ / 🔧 | Gateway metrics/events 🟢; full tool/decision traces 🔧 Phase E/G. |
| Audit trails | ⚠️ / 🔧 | Event log 🟢; compliance-grade retention 🔧 |
| Clear ownership / discovery | ❌ | Ops metadata later. |
| Financial budgets | 🟢 / 🔧 | Gateway tenant USD + token budgets 🟢; workflow thresholds 🔧 |
| Token optimization | 🔧 | RAG retrieve-only, progressive write, Thinker only on large-context steps. |
| Retries / backoff / circuits | 🟢 | Gateway. |
| Reproducibility | 🔧 | Run manifests + seed configs + stored traces. |
| Kubernetes | ❌ deferred | Roadmap deferred. |
| Event-driven / queues | ❌ deferred | |
| API-first gateway | ⚠️ / 🔧 | Ops dashboard 🟢; product API Phase H. |

---

## 4. MLOps / LLMOps

| Rubric item | Status | Our mapping |
|-------------|--------|-------------|
| External versioned prompts | 🔧 | `prompts/` versioned YAML/MD — not hardcoded long-term. |
| Offline evals | 🔧 | [EVALS.md](EVALS.md) component suite CI. |
| Online evals | 🔧 late | Post-deploy sampling. |
| A/B experimentation | 🔧 late | Config tags + eval compare. |
| CI/CD | ⚠️ / 🔧 | `test_gateway.py` 🟢; full pipeline later. |

---

## 5. Autonomous research specifics

| Rubric item | Status | Our mapping |
|-------------|--------|-------------|
| Automated fact-checking | 🔧 | Verifier / Critic: multi-source agreement + contradiction graph. |
| Full citation tracking | 🔧 (R6) | Evidence ids + end Sources; ship-gate. |
| Multi-format input | 🔧 | PDF/Office/images via MinerU; web real-time via search tools. |

---

## 6. Thinker agent (new — required)

| Item | Spec |
|------|------|
| **Role** | Large-context **reasoning only** — not tool calls, not final user-facing prose by default |
| **When** | Plan refinement, multi-doc synthesis brief, contradiction resolution, section outline under “accurate/comprehensive” dials |
| **Default model** | Gemini **free tier** via OpenAI-compat endpoint (see [PROVIDERS.md](PROVIDERS.md) + below) |
| **Why Gemini** | Long context (up to ~1M class on current Flash/Pro families per Google docs), free input/output on Free tier for eligible models |
| **Rate limits** | **Not hard-coded in product** — official docs say limits are **per project, per model, per tier** and must be read live in [AI Studio rate limits](https://aistudio.google.com/rate-limit). Dimensions: **RPM · TPM (input) · RPD** (RPD resets midnight Pacific). Free tier has **no spend-based** 10-min limit (N/A). Free tier content **may be used to improve Google products** ([pricing](https://ai.google.dev/gemini-api/docs/pricing)). |
| **Engineering controls** | Gateway rate limit for `gemini/*`; queue/thinker jobs; backoff on 429; never spam Thinker every micro-step — **invoke sparingly** |
| **Fallback** | OpenCode free strong / Groq / DeepSeek if Gemini free exhausted |

### Gemini free tier (official, not third-party tables)

From [Rate limits](https://ai.google.dev/gemini-api/docs/rate-limits) + [Pricing](https://ai.google.dev/gemini-api/docs/pricing):

- Free tier: free input & output on **eligible** models; limited access.  
- Exact RPM/TPM/RPD: **view in AI Studio** for your project (Google does not publish a single static free-tier number for all models on the rate-limits page).  
- Community reports historically cite ~5–15 RPM free depending on model — **treat as informal**; always bind product to AI Studio + 429 handling.  
- Prefer **Flash** family for free Thinker (e.g. docs examples `gemini-3.6-flash` / `gemini-2.5-flash`) for speed + context; Pro free is tighter and may be unavailable on free for some previews.

---

## 7. Target multi-agent map (production pattern)

```
                 ┌─────────────┐
                 │   Planner   │  DAG / outline / budgets / autonomy level
                 └──────┬──────┘
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
   ┌────────────┐ ┌──────────┐ ┌────────────┐
   │ Researcher │ │ Thinker  │ │  Critic    │
   │ tools+RAG  │ │ Gemini   │ │ eval/retry │
   └─────┬──────┘ │ free/LC  │ └─────┬──────┘
         │        └────┬─────┘       │
         └─────────────┼─────────────┘
                       ▼
                ┌────────────┐
                │Synthesizer │  progressive sections
                └─────┬──────┘
                      ▼
                ┌────────────┐
                │  Compiler  │  citations + export + ship-gate
                └────────────┘
```

| Agent | Tools? | Default model tier | Trust boundary |
|-------|--------|--------------------|----------------|
| **Planner** | vault read only | fast | No web write |
| **Researcher** | search, crawl, parse, vault | fast | Untrusted web fenced |
| **Thinker** | none (context in, structure out) | **Gemini free / large context** | No tools = smaller blast radius |
| **Critic** | vault read + sampled sources | strong / thinker | Can block ship |
| **Synthesizer** | RAG retrieve only | strong | No raw crawl dump |
| **Compiler** | export, cite-check | fast/deterministic where possible | Ship-gate owner |

Deterministic **harness** owns: budgets, autonomy level, tool allowlists, ship-gate — not the LLM.

---

## 8. Staged autonomy (controlled)

| Level | Name | Behavior |
|-------|------|----------|
| **L1** | Report | Full research → report; user always reviews (default) |
| **L2** | Human gate | Pause after plan and/or before deep spend / export for approval |
| **L3** | Unattended | Auto-run within hard budgets; still logs full audit trail |

Default product: **L1**. L2/L3 require explicit config.

---

## 9. Scorecard summary

| Pillar | Target coverage | Built today |
|--------|-----------------|-------------|
| 1 Architecture | High (with multi-agent + Thinker + L1–L3) | Low–medium (monolith + gateway) |
| 2 Capabilities | High | Medium (search + report) |
| 3 Enterprise NFRs | Medium (gateway strong; K8s/sandbox deferred) | Medium on resilience/cost; low on ZT/sandbox/K8s |
| 4 LLMOps | Medium (evals designed; online A/B later) | Low |
| 5 Research specifics | High (cites, fact-check, multi-format) | Low–medium |

---

## 10. Doc updates linked

- SPEC — multi-agent roster, Thinker, autonomy L1–L3, R14  
- ARCHITECTURE — agent diagram + Thinker path  
- ROADMAP — multi-agent + Thinker phase  
- PROVIDERS — Gemini free Thinker notes  
