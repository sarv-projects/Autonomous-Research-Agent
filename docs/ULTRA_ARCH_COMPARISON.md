# Ultra Research Architecture vs Ours (A3)

**Purpose:** Compare the aspirational “Ultra Research Agent” blueprint (5-layer cognitive model + later “perfect” merge with triad/math/sandbox) against **what we actually run today** (`A3_scout_gemini3_groq120_exa`).

**Our stack (current = A4):**  
Scout (Exa + 3× Gemini) → Plan → Thinker refine → Research loop ↺ → **Devil’s advocate → Claim adjudicator** (≤1 Socratic hop) → Triangulator → Synth → Compiler (**Bedrock + Research Debt + Sources**).  
Workhorse: Groq `gpt-oss-120b`; search: Exa; RAG: LanceDB+FTS + `run_id` isolation.  
**Measured quality ~87%** vs ChatGPT DR ~90 / Gemini DR ~88 — see [ARCHITECTURE_BENCHMARKS.md](ARCHITECTURE_BENCHMARKS.md).

**Last updated:** 2026-08-10

---

## 1. One-sentence verdict

| Blueprint | Verdict |
|-----------|---------|
| **5-layer “Ultra” (PhD epistemology)** | **Research agenda / grant proposal** — scientifically ambitious; mostly **not built** |
| **“Perfect” merge (triad + math + sandbox + research debt)** | **Next 6–18 months roadmap** — many pieces map cleanly onto our graph |
| **Ours (A3)** | **Production literature Deep Research** — ship today; ~80% product-DR quality; **not** experimental science |

Analogy used in the source comparison still holds: **we are F1 (race now)**; **ultra is a space shuttle (different mission).**

---

## 2. Layer-by-layer: Ultra blueprint vs A3

| Ultra layer | What it demands | Ours today | Coverage | Gap |
|-------------|-----------------|------------|----------|-----|
| **L0 Sensory cortex** | Multi-modal embeddings (DNA, spectra…), temporal half-life, citation GNN | Text (+ PDF/arXiv adapters); flat hybrid RAG; no half-life; no GNN | **~15%** | Domain multi-modal, authority-flow graphs, source decay |
| **L1 Critic-stack swarm** | Generator / Adversary / Empiricist / Synthesizer **in debate**; CoVe per claim | Sequential scout→plan→critic; **triangulator pro/con/neutral once** at end; claim–evidence ship-gate (heuristic) | **~35%** | True adversarial swarm + experiment design agent + strict CoVe |
| **L2 Hippocampus** | Working + episodic + semantic KG (Neo4j) + nightly consolidation | Working: LangGraph state; episodic-lite: **vault** + past reports; semantic: chunks only | **~25%** | Failure memory, uncertainty-weighted KG, consolidation loop |
| **L3 Motor cortex** | Sandbox REPL, unit tests, Wolfram/PubMed/corporate DBs | **Tool bus**: Exa, wiki, Firecrawl, arXiv adapters; **no** code sandbox / SymPy / DFT | **~30%** | Execute & verify, not only retrieve |
| **L4 Metacognitive governor** | Ensemble confidence, info-gain, kill-switch on unresolved contradiction | Critic abort / re-search; budgets; **no** multi-model CI; no entropy/info-gain | **~25%** | Calibrated uncertainty + research-debt kill-switch |
| **Litmus (clarify axioms)** | First response challenges assumptions | Plan/clarify API exists (L2); not default first UX message | **~20%** | Default “3 flawed assumptions?” prelude |

**Rough overall vs Ultra ideal:** **~25–35%** of the full epistemology vision.  
**Rough overall vs product Deep Research (Gemini/ChatGPT):** **~75–80%** (see `ARCHITECTURE_BENCHMARKS.md`).

---

## 3. Pipeline-node mapping (ours → ultra ideas)

| Our node | Closest ultra / “perfect” idea | Status |
|----------|--------------------------------|--------|
| `thinker_query_scout` | Deconstruct + light retrieve + multi-LLM fanout | **Shipped** (Exa + Gemini×3) |
| `planner` + `thinker_plan_refine` | Deconstruct / pathway proposal | **Shipped** |
| `researcher_gather` | Sensory retrieval (web/arXiv) | **Shipped** (text-centric) |
| `researcher_analyze` | Working memory claims | **Shipped** |
| `thinker_contradiction_check` | Adversary-lite | **Shipped** (sequential, not swarm) |
| `critic` | Kill-switch-lite + completeness | **Shipped** |
| `thinker_search_strategy` | Dynamic replan of queries | **Shipped** |
| `triangulator` | Generator/adversary/synthesizer **once** | **Partial** (not full Socratic tree) |
| `synthesizer_*` + self-critique | Synthesizer + soft CoVe | **Shipped** |
| `compiler` ship-gate | CoVe / bedrock gate | **Partial** (URL/quote heuristic, not math) |
| Vault + reports | Episodic memory-lite | **Partial** |
| Jobs + SSE progress | Latency UX / leave-return | **Shipped** |
| Plan edit API | Clarifying / editable plan | **Partial** |
| Math straitjacket (SymPy) | Empiricist formalization | **Missing** |
| Repro sandbox | Empiricist experiment | **Missing** (skipped on purpose earlier) |
| Devil’s-advocate crawl | Adversary web | **Missing** as dedicated node |
| Research Debt section | Metacognitive honesty | **Missing** as first-class section |
| Confidence volcano (bedrock/inference) | Metacognitive output layers | **Missing** |
| GNN citation authority | L0 citation graph | **Missing** |
| Source half-life | Temporal indexing | **Missing** |
| Router 7B skip layers | Latency unfair advantage | **Partial** (mode/intensity dials only) |

---

## 4. “Perfect” blueprint upgrades vs priority for *us*

The second half of the comparison proposes upgrades on **top of our pipeline**. Ranked by **impact / cost** for beating product DR without building a lab:

| # | Upgrade | Maps to | Build now? | Why |
|---|---------|---------|------------|-----|
| 1 | **Research Debt** section always | L4 honesty | **Yes** | Cheap; huge expert trust; differentiates vs ChatGPT polish |
| 2 | **Confidence volcano** (Bedrock / Inference / Debt) | L4 + CoVe | **Yes** | Compiler already almost does sources; formalize layers |
| 3 | **Devil’s-advocate / negative-evidence gather** | L1 adversary | **Yes** | One gather pass for retractions, limits, counter-papers |
| 4 | **Socratic tree** (adjudicator → 1–2 targeted re-gathers on contested claims) | L1 swarm-lite | **Yes** | Stretch of our existing loop; don’t need 4 full LLMs |
| 5 | **Claim→chunk CoVe strict** | L1 CoVe | **Yes** | Harden ship-gate beyond keyword overlap |
| 6 | **Clarifying assumptions prelude** (default deep) | Litmus | **Optional** | We have L2 plan; make default for ambiguous queries |
| 7 | **Math straitjacket (SymPy)** | L3 | **Domain mode only** | High value for STEM; noise for pure lit reviews |
| 8 | **Repro sandbox** | L3 | **Later** | Security + infra; only for code-heavy papers |
| 9 | **Neo4j + nightly consolidation** | L2 | **Later** | Real when multi-session research products matter |
| 10 | **GNN citation authority** | L0 | **Research project** | Not needed to win lit-DR leaderboard |
| 11 | Multi-modal DNA/protein embeddings | L0 | **No (unless domain product)** | Out of scope for general DR |

**Do not** treat “DeepSeek-V4-Pro as CEO of every node” as mandatory. Our gateway already multi-providers; routing by **tier** (fast/strong/thinker) is enough. Swap models without rewriting the graph.

---

## 5. Head-to-head scorecard (honest)

| Criterion | Ultra ideal | “Perfect” merge | **Ours A3** | Winner for *shippable DR* |
|-----------|-------------|-----------------|-------------|---------------------------|
| Usable today | No | Partial | **Yes** | **Ours** |
| Literature survey quality | High (if built) | High | **Good (~80%)** | Products still ahead |
| Hallucination control | Max (if built) | Max | **Strong integrity** | Ours > A0; products ≈ |
| Experimental science | Yes | Yes | No | Ultra |
| Latency (deep lit report) | Slow | Medium (async) | **~4 min (Groq)** | **Ours** |
| Cost / control | High | High | **Low–mid** | **Ours** |
| Open / reproducible | Depends | Depends | **Yes** | **Ours** |
| Epistemic honesty (debt, CI) | Explicit | Explicit | Implicit gaps only | Ultra / Perfect |
| Multi-agent debate depth | 4-way swarm | Triad + adjudicator | Sequential + triangulate | Ultra |
| Code/math grounding | Full REPL | SymPy + sandbox | Search tools only | Ultra |

---

## 6. What we should claim publicly

**Accurate:**  
“We run a **Deep Research multi-agent pipeline** with scout, critique loop, hybrid RAG isolation, claim–evidence ship-gate, and multi-provider failover—comparable structure to product DR, open and fast on Groq+Exa.”

**Not accurate:**  
“We implement full scientific epistemology / DFT experiments / GNN citation authority / nightly KG consolidation.”

**Crush angles vs GPT/Gemini (products):**  
integrity automation, open stack, forced eval/failure templates, cost, research-debt honesty (once added)—**not** “we run better physics simulations.”

---

## 7. Target architecture if we evolve A3 → “Ultra-lite”

Keep A3 spine; add only high-ROI nodes:

```
scout → plan → refine
  → gather/analyze loop (+ optional devil_advocate_gather)
  → contradiction + critic + search_strategy
  → [optional] claim_adjudicator → targeted re-gather (Socratic tree, max 1–2 hops)
  → triangulator
  → synth
  → [optional] math_validate (STEM modes)
  → compiler: Bedrock | Inference | Research Debt | Sources
```

**Still out of scope for v1 “ultra-lite”:** GNN, Neo4j nightly merge, multi-modal spectra, ensemble 5-model CI every claim.

---

## 8. Coverage summary

| Target | Ours vs target |
|--------|----------------|
| Ultra 5-layer PhD agent | **~30%** coverage (conceptual overlap; implementation thin) |
| “Perfect” triad/math/sandbox blueprint | **~40%** (spine exists; validation layers missing) |
| Product Deep Research (Gemini/ChatGPT) | **~80%** (see ARCHITECTURE_BENCHMARKS) |
| Best next jump | Research Debt + devil’s-advocate + stricter CoVe → estimate **~80 → ~84–86%** product-relative |

---

## 9. Stolen into the live graph (2026-08-10)

Implemented ultra-lite steals (no sandbox/GNN yet):

| Steal | Node / behavior |
|-------|-----------------|
| Devil’s-advocate crawl | `devil_advocate_gather` after research loop complete |
| Socratic tree (1 hop) | `claim_adjudicator` → optional one re-gather on contested/synthetic claims |
| CoVe-lite | Phrase/word + adjudicated claim status in ship-gate |
| Confidence volcano | Compiler appends **Evidence Bedrock** + **Research Debt** + **Sources** |
| Research Debt | Always compiled; LLM polish on deep modes |

**Graph path:**  
`… → search_strategy → [loop|adversary] → devil_advocate → adjudicator → [socratic gather|triangulator] → synth → compiler`

---

## Related docs

- `docs/ARCHITECTURE_BENCHMARKS.md` — A0–A3 scores and baselines  
- `docs/ARCHITECTURE.md` — engine modules  
- `src/graph.py` — live graph edges  
