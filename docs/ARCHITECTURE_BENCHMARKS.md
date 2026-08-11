# Architecture & Research Benchmarks

**Purpose:** Track architecture variants and measured report quality so we can compare runs, baselines, and external systems (Gemini / ChatGPT Deep Research).  
**Topic used for all comparative runs (unless noted):**

> How does retrieval-augmented generation (RAG) reduce hallucination in large language models? Cover mechanisms, limitations, evaluation methods, and production best practices as of 2025–2026.

**Last updated:** 2026-08-10

---

## 1. How to read this file

| Column | Meaning |
|--------|---------|
| **Arch ID** | Named stack / pipeline config |
| **Overall %** | Weighted research-quality score (0–100), same rubric |
| **Baseline** | Reference point for deltas |
| **Delta** | Change vs baseline (pts) |

Higher is better unless marked (e.g. time, cost). Scores are **research deliverable quality**, not chat UX.

---

## 2. Scoring rubric (fixed)

Weights sum to 100. Score each dimension 0–100, then weighted average.

| # | Dimension | Weight | What “100” looks like |
|---|-----------|--------|------------------------|
| D1 | Source integrity | 20% | Real URLs only; 0 cross-run contamination; sources at end |
| D2 | Claim–evidence / faithfulness | 15% | Claims grounded in retrieved text; no empty monographs |
| D3 | Named systems / papers | 12% | Specific systems (Self-RAG, CRAG, RAPTOR, ColBERT, …) with years |
| D4 | Eval matrix (RAG triad + tools) | 12% | Explicit matrix: context relevance, faithfulness, answer relevance |
| D5 | Failure-mode taxonomy | 10% | Structured failure modes + mitigations |
| D6 | Production / ops practices | 8% | Deployable guidance (chunking, cache, monitor) |
| D7 | Report structure | 8% | Exec summary, body, eval, failure, conclusion, sources last |
| D8 | Narrative polish | 8% | Coherent prose; no CoT/planning leaks |
| D9 | Evidence breadth | 7% | Diverse high-quality sources (arXiv + web), not volume alone |

**Overall %** = Σ (score_i × weight_i) / 100.

### Hard metrics (always log)

| Metric | Unit | Notes |
|--------|------|--------|
| Wall time | seconds | End-to-end CLI research |
| Word count | words | Final markdown report |
| Sources (real URLs) | count | End Sources section only |
| arXiv share | count / % | Of listed sources |
| Claim–evidence | supported/total | Compiler ship-gate |
| Euler / off-topic junk | count | Must be 0 |
| Named systems hit | count | From fixed list (see §5) |
| Ship gate | pass/fail | Compiler |
| Mode | string | e.g. deep |
| Primary LLM | string | e.g. groq/openai/gpt-oss-120b |
| Search | string | e.g. Exa |

**Fixed named-system checklist (D3):**  
Self-RAG, CRAG, RAPTOR, ColBERT, DPR, HyDE, GraphRAG, RETRO, Atlas, FiD, REALM, SeaRAG, RAGAS

---

## 3. Architecture variants under test

### 3.0 At a glance — **what was what** (do not confuse)

| Arch | One-line name | What it **was** (stack) | What it was **not** | When / role |
|------|---------------|-------------------------|---------------------|-------------|
| **A0** | Legacy contaminated | Old multi-agent path; **shared RAG store**; weak source gate; often Zen/wiki path | Not Exa-primary integrity stack; not Groq primary; no scout | **Internal baseline (fail)** — Euler sources |
| **A1** | Integrity + Zen free | Critic loop + thinkers + **run_id RAG** + ship-gate + **Exa** + **Zen free** workhorse | Not Groq-first; no Gemini scout | First “fixed integrity” long run (slow free LLMs) |
| **A2** | Integrity + Groq 120b | **Same graph as A1** (no start scout); **Groq `gpt-oss-120b`** primary; Exa; speed caps | Not Zen-primary; **no** `thinker_query_scout` | Fast paid-LLM ship; experiment baseline |
| **A3** | Scout + Gemini×3 + Groq | **A2 + start scout** only (no devil’s advocate yet) | Not ultra-steals (no Bedrock/Debt) | Intermediate |
| **A4** | A3 + Ultra steals | **A3 +** devil’s advocate + claim adjudicator + Bedrock + Research Debt + CoVe | Not math sandbox / GNN | **Current default** |
| **B_gemini** | Gemini Deep Research | Google product DR (external) | Not our repo pipeline | Product baseline |
| **B_chatgpt** | ChatGPT Deep Research | OpenAI product DR (external) | Not our repo pipeline | Product baseline |

**Memory aid**

| If you remember… | That was… |
|------------------|-----------|
| Euler Wikipedia in Sources | **A0** |
| Long ~15–25 min, free models, real arXiv | **A1** |
| ~4–5 min, Groq 120b, no Gemini scout | **A2** |
| Scout only (3× Gemini), no Bedrock/Debt | **A3** |
| Devil’s advocate + Adjudicator + Bedrock + Research Debt | **A4** (current) |
| Pasted product PDF/UI report | **B_gemini** or **B_chatgpt** |

**Pipeline shape by arch**

| Arch | Pipeline (short) |
|------|------------------|
| **A0** | `Plan → Research loop → Synth → Compile` (weak isolation) |
| **A1 / A2** | `Plan → Thinker → (Gather→Analyze→Thinker→Critic→SearchStrategy)↺ → Triangulate → Synth → Compile` |
| **A3** | **`Scout(Exa+Gemini×3)` →** *(same as A1/A2 from Plan onward)* |
| **A4** | **A3 +** `devil_advocate → adjudicator` [socratic hop?] → tri → synth → **Bedrock+Debt+Sources** |

---

### A0 — `A0_legacy_contaminated` — Baseline (legacy integrity failure)

| Field | Value |
|-------|--------|
| **Arch ID** | `A0_legacy_contaminated` |
| **Human name** | Legacy / contaminated baseline |
| **What it was** | Early multi-agent report path **before** P0 integrity: no reliable per-run RAG filter; vault/shared chunks could leak; sources not ship-gated to this run |
| **Graph** | Planner → Research loop → Synth → Compiler (no scout; weak isolation) |
| **LLM** | Mixed / Zen-heavy (not Groq-primary) |
| **Search** | Weak / vault pollution possible (not Exa-first integrity mode) |
| **RAG** | Shared store; **no reliable run_id isolation** |
| **Report example** | `reports/research_How does retrieval-augmented generation _RAG_ redu_20260810_153607.md` |
| **How to recognize** | Polished prose + **Euler Wikipedia** (or other off-topic) Sources; fake monographs |

---

### A1 — `A1_integrity_zen_exa` — Integrity stack + Zen free

| Field | Value |
|-------|--------|
| **Arch ID** | `A1_integrity_zen_exa` |
| **Human name** | Integrity + OpenCode Zen free + Exa |
| **What it was** | First full **P0 integrity** stack: run_id isolation, critic off-topic, ship-gate, claim–evidence, Exa search, deep templates; **generation on free Zen** (slow) |
| **Graph** | Plan → Thinker → Gather/Analyze → Thinker → Critic → Thinker strategy ↺ → Triangulator → Synth (+ templates) → Compiler |
| **LLM** | OpenCode Zen free first (fast/strong/thinker) — **not** Groq primary |
| **Search** | Exa primary (when key set); arXiv bias |
| **RAG** | `run_id` isolation + hybrid LanceDB+FTS |
| **Integrity** | Off-topic gate, ship-gate, claim–evidence, sources last |
| **Report example** | `reports/research_How does retrieval-augmented generation _RAG_ redu_20260810_174404.md` |
| **How to recognize** | Real RAG sources, long wall time, Zen-era free-model stalls |

---

### A2 — `A2_integrity_groq120_exa` — Integrity + Groq primary (best Groq)

| Field | Value |
|-------|--------|
| **Arch ID** | `A2_integrity_groq120_exa` |
| **Human name** | Integrity + Groq gpt-oss-120b + Exa (no scout) |
| **What it was** | **Same multi-agent graph as A1**, but **LLM primary = Groq `openai/gpt-oss-120b`** on fast/strong/thinker; Exa + speed caps; **no start scout / no parallel Gemini** |
| **Graph** | Same as A1 (**no** `thinker_query_scout`) |
| **LLM** | **Groq `openai/gpt-oss-120b`** primary on fast/strong/thinker |
| **Search** | Exa primary |
| **Speed caps** | ≤4 queries/iter, top ~20 results, 10 pages, 4 iters max, factoids off |
| **Report example** | `reports/research_How does retrieval-augmented generation _RAG_ redu_20260810_180451.md` (Overview CoT cleaned post-hoc) |
| **How to recognize** | ~4–5 min run; gateway shows groq/gpt-oss-120b first; log has **no** “Query scout (web + 3× parallel Gemini)” |
| **Use as** | **Default experiment baseline** (ablate scout vs A3) |

---

### A3 — `A3_scout_gemini3_groq120_exa` — Current (scout + Gemini×3 + Groq)

| Field | Value |
|-------|--------|
| **Arch ID** | `A3_scout_gemini3_groq120_exa` |
| **Human name** | Start scout (Exa + 3× Gemini) + Groq workhorse + Exa research |
| **What it was** | **A2 plus** entry node **`thinker_query_scout`**: light Exa web peek + **3 parallel Gemini Flash-Lite** calls, then full A2 research loop on **Groq** — **before** devil’s advocate / Bedrock / Debt |
| **Graph** | **scout** → plan → refine → loop ↺ → triangulate → synth → compile |
| **Scout** | Exa ~5 hits + **3× parallel Gemini Flash-Lite** |
| **LLM workhorse** | Groq `openai/gpt-oss-120b` |
| **Report example** | `reports/research_How does retrieval-augmented generation _RAG_ redu_20260810_183051.md` |
| **How to recognize** | Scout log present; **no** “Devil's Advocate” / no Evidence Bedrock section |

---

### A4 — `A4_ultra_steals` — Current (A3 + Ultra steals)

| Field | Value |
|-------|--------|
| **Arch ID** | `A4_ultra_steals` **← current default** |
| **Human name** | Scout + Groq + devil’s advocate + adjudicator + confidence volcano |
| **What it was** | **A3 plus** Ultra steals: counter-evidence gather, claim CoVe adjudication (1 Socratic hop), compiler layers Bedrock + Research Debt + Sources |
| **Graph** | scout → plan → refine → loop ↺ → **devil_advocate → adjudicator** → [socratic gather?] → tri → synth → compile |
| **LLM workhorse** | Groq `openai/gpt-oss-120b`; Gemini×3 scout |
| **Report example** | `reports/research_How does retrieval-augmented generation _RAG_ redu_20260810_192307.md` |
| **How to recognize** | Logs: `Devil's Advocate`, `Adjudicator`; report has **Evidence Bedrock** + **Research Debt** |

### Graph diagram (A4 — current)

```
User query
    │
    ▼
thinker_query_scout     Exa scout + 3× Gemini (parallel, RPM-safe)
    │
    ▼
planner                 outline + queries (uses scout)
    │
    ▼
thinker_plan_refine
    │
    ▼
┌── researcher_gather ──► researcher_analyze ──► thinker_contradiction
│         │                                              │
│         │                                              ▼
│         │                                           critic
│         │                                              │
│         │                                              ▼
│         │                                    thinker_search_strategy
│         │                                              │
│         ◄──────── needs_more_research ─────────────────┤
│                                                        │
│         abort ──► abort_passthrough ──► compiler       │
│                                                        ▼
└── complete ──► triangulator ──► synth_outline ──► synth_write
                                                          │
                                                          ▼
                                                      compiler
                                                   (ship-gate, sources)
```

---

## 4. External baselines (product Deep Research)

Not run inside this repo; scores are **judgment baselines** from side-by-side review of pasted Gemini/ChatGPT reports on the **same topic**.

| Baseline ID | System | Overall % | Notes |
|-------------|--------|-----------|--------|
| **B_gemini_dr** | Google Gemini Deep Research | **86–90** | Strong production ops flavor; real URLs; eval matrix sometimes lighter |
| **B_chatgpt_dr** | ChatGPT Deep Research | **88–92** | Strong taxonomy + eval matrix; high polish; real URLs |
| **B_human_survey** | Ideal survey paper | **95+** | Not automated; upper bound |

Use **B_chatgpt_dr = 90** and **B_gemini_dr = 88** as single-point baselines for tables.

---

## 5. Measured results (same topic)

### 5.1 Hard metrics

| Arch | What it was (short) | Time (s) | Words | Sources | arXiv | Claim–ev | Euler | Named (of 13) | Bedrock/Debt | Ship |
|------|---------------------|----------|-------|---------|-------|----------|-------|---------------|--------------|------|
| **A0** | Legacy contamination | ~284 | ~5.5k | 12 junk | 0 | n/a | **22** | n/a* | n/n | soft |
| **A1** | Integrity + Zen free + Exa | ~950 | ~19k | 28 | 12 | 24/24 | **0** | 6 | n/n | pass |
| **A2** | Groq 120b + Exa, no scout | ~265 | ~8.0k | 22 | 15 | 21/21 | **0** | 6 | n/n | pass |
| **A3** | Scout Gemini×3 + Groq | ~243 | ~7.3k | 30 | 20 | 27/27 | **0** | 4 | n/n | pass |
| **A4** | **A3 + ultra steals** | **~284** | **~11.7k** | **41** | **24** | **34/36** | **0** | **7** | **Y/Y** | pass |

\*A0 may name systems in body while Sources are Euler — integrity fail.  
A4 report: `…_20260810_192307.md` (devil’s advocate + adjudicator + Bedrock + Debt).

### 5.2 Dimension scores (0–100) and overall %

| Dimension (weight) | A0 | A1 | A2 | A3 | **A4** | B_gemini | B_chatgpt |
|--------------------|----|----|----|-----|--------|----------|-----------|
| D1 Integrity (20) | 25 | 90 | 90 | 90 | **93** | 92 | 90 |
| D2 Claim–evidence (15) | 30 | 95 | 95 | 95 | **94** | 85 | 88 |
| D3 Named systems (12) | 40 | 70 | 70 | 60 | **75** | 88 | 90 |
| D4 Eval matrix (12) | 45 | 88 | 88 | 88 | **88** | 70 | 92 |
| D5 Failure taxonomy (10) | 45 | 88 | 88 | 88 | **88** | 72 | 90 |
| D6 Production (8) | 40 | 80 | 80 | 80 | **80** | 90 | 78 |
| D7 Structure (8) | 50 | 88 | 88 | 88 | **96** | 80 | 92 |
| D8 Polish (8) | 72 | 62 | 58 | 62 | **70** | 90 | 92 |
| D9 Breadth (7) | 25 | 79 | 73 | 86 | **92** | 95 | 90 |
| **Overall %** | **~38** | **~84** | **~83** | **~83** | **~87** | **~88** | **~90** |

*A4 ≈ **87%** from hard metrics on `…_192307.md`. A1–A3 re-scored on the same measured reports. ±2 pts noise.*

### 5.3 Delta vs baselines

| Arch | What it was | vs A0 | vs A2 | vs A3 | vs B_chatgpt (90) | vs B_gemini (88) |
|------|-------------|-------|-------|-------|-------------------|------------------|
| A0 | Legacy | 0 | — | — | −52 | −50 |
| A1 | Zen + integrity | +46 | +1 | +1 | −6 | −4 |
| A2 | Groq, no scout | +45 | 0 | 0 | −7 | −5 |
| A3 | Scout only | +45 | 0 | 0 | −7 | −5 |
| **A4** | **Ultra steals (current)** | **+49** | **+4** | **+4** | **−3** | **−1** |

---

## 6. Comparison leaderboard (latest)

| Rank | System / Arch | What it was | Overall % | Integrity | Speed | Open/repro |
|------|---------------|-------------|-----------|-----------|-------|------------|
| 1 | **B_chatgpt** ChatGPT Deep Research | OpenAI product DR | ~90 | high | medium | closed |
| 2 | **B_gemini** Gemini Deep Research | Google product DR | ~88 | high | medium–fast | closed |
| 3 | **A4** Ultra steals | **Current** scout+DA+CoVe+Debt | **~87** | **high** | **~4.7 min** | **open** |
| 4 | A1 / A2 / A3 | Integrity variants | ~83–84 | high | varies | open |
| 5 | **A0** legacy | Contaminated / Euler | ~38 | **fail** | medium | open |

**Where we win vs products:** integrity automation, CoVe + Research Debt honesty, forced eval/failure structure, open stack, cost.  
**Where we lose:** narrative polish, perfect citation hygiene, full web-index breadth.  
**A4 vs A3:** +11 sources, Bedrock/Debt layers, counter-evidence pass, CoVe **94%** (34/36).

---

## 7. Architecture → expected effect (cheat sheet)

| Change | Helps | Hurts / risk |
|--------|-------|----------------|
| Per-run RAG isolation | D1 | — |
| Critic off-topic + abort | D1, D2 | False positives if URL-only (fixed: titles+text) |
| Exa primary | D9, latency of search | Cost; over-fetch if uncapped |
| Speed caps (top-N pages) | Time | D9 if too aggressive |
| Groq 120b primary | Time, D8 vs Zen free | CoT leak in body (oss models) |
| Start scout + 3× Gemini | D3 planning, D4/D5 seeds, D7 | RPM if abused; body may ignore seeds |
| Forced report templates | D4, D5, D7 | Generic sections if evidence thin |
| Ship-gate / claim–evidence | D2 | Soft heuristic ≠ full NLI |

---

## 8. How to add a new row (protocol)

1. Record **Arch ID** + config (providers.yaml tiers, modes.yaml, graph nodes).  
2. Run same query:  
   `uv run python main.py research "<topic>" --mode deep --autonomy L1`  
3. Fill hard metrics from log + report path.  
4. Score D1–D9 with rubric above.  
5. Append row to §5 tables; update leaderboard §6.  
6. Note date and git commit if available.

### Template

```markdown
| Arch | YYYY-MM-DD | Time | Words | Sources | Claim–ev | Named | Overall % | Report path | Notes |
|------|------------|------|-------|---------|----------|-------|-----------|-------------|-------|
| A?   |            |      |       |         |          |       |           |             |       |
```

---

## 9. Baseline definition (for experiments)

| Name | Definition | Use when |
|------|------------|----------|
| **Internal baseline** | **A0** (Euler / contamination era) | Show integrity work |
| **Prior ship** | **A2** (Groq+Exa, no scout) | Ablate scout / Gemini |
| **Product baseline** | **B_chatgpt_dr = 90** | Head-to-head product claim |
| **Secondary product** | **B_gemini_dr = 88** | Structure/ops comparison |

**Default experiment baseline for new features:** **A2** (same search+integrity+Groq; only pipeline nodes change).  
**Default product baseline:** **B_chatgpt_dr**.

---

## 10. Current recommended stack (A4)

**What “current” means:** `A4_ultra_steals` — A3 scout + devil’s advocate + adjudicator + Bedrock/Debt.

```
Scout:     Exa + Gemini Flash-Lite ×3 parallel (≤15 RPM free class)
Workhorse: Groq openai/gpt-oss-120b (fast/strong/thinker)
Search:    Exa (priority 200) + arXiv bias + devil’s-advocate pass
Store:     LanceDB + FTS, run_id isolation
Loop:      Critic → search strategy → gather (max 4 deep)
Adversary: devil_advocate → claim_adjudicator (≤1 Socratic hop)
Report:    Inference + Evidence Bedrock + Research Debt + Sources
Gates:     off-topic, ship-gate, CoVe claim–evidence
```

**Report (A4):**  
`reports/research_How does retrieval-augmented generation _RAG_ redu_20260810_192307.md`

| Report filename time | Arch it belongs to |
|----------------------|--------------------|
| `…_20260810_153607` | **A0** legacy contaminated |
| `…_20260810_165258` | A1-era integrity (long Exa firehose; see also 174404) |
| `…_20260810_174404` | **A1** Zen + integrity + Exa |
| `…_20260810_175306` | False abort / off-topic bug (transitional) — not a baseline |
| `…_20260810_175903` / `180451` | **A2** Groq 120b, no scout |
| `…_20260810_183051` | **A3** Scout + Gemini×3 + Groq (pre-steals) |
| `…_20260810_192307` | **A4** Ultra steals (DA + adjudicator + Bedrock + Debt) |

---

## 11. Changelog

| Date | Change |
|------|--------|
| 2026-08-10 | Initial comparison doc: A0–A3, product baselines, rubric, leaderboard |
| 2026-08-10 | A3: thinker_query_scout + parallel Gemini; integrity + Groq/Exa |
| 2026-08-10 | A0 documented as contamination baseline (Euler sources) |
| 2026-08-10 | Added “what was what” glance table, memory aid, report→arch map, labels on all score tables |
| 2026-08-10 | **A4** eval vs A0–A3 and product baselines; overall ~87% |
