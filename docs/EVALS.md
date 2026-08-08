# Evaluation system (final)

Aligns with [SPEC.md](SPEC.md) R13.

---

## 1. Layers

### A. Component & lower-level

| Suite | Measures | Offline? |
|-------|----------|----------|
| `tool_selection` | Correct tool + valid args | Yes (fixtures) |
| `plan_coherence` | Goal decomposition validity | Yes + LLM judge |
| `memory_recall` | Multi-turn fact recall | Yes |
| `intent_resolution` | Mode / chat vs research | Yes |
| `rag_ir` | recall@k, MRR, nDCG | Yes |
| `citation_grounding` | Claim supported by evidence | Yes + entailment/judge |

### B. System & macro

| Suite | Measures |
|-------|----------|
| `task_completion` | Multi-step goals finished |
| `trajectory` | Cascading failures; first-fail step |
| `efficiency` | Loops, tokens, latency, $ vs budget |
| `research_quality` | Coverage, citations, actionability rubric |
| `macro` | Aggregated blockers across runs |

### C. Industry / optional

- DeepResearch-style task subsets  
- BrowseComp / GAIA samples (optional, not day-1 CI)  
- Internal static task bank for regression  

### D. Always-on ops metrics

From gateway + engine:

- Latency p50/p95 (chat turn, research run)  
- Cost USD / task  
- Error rate by provider/tool  
- RAG query p95  
- Circuit open rate, rate-limit denials  
- Tokens per accepted claim  

---

## 2. Layout

```
evals/
  datasets/
    tool_selection.jsonl
    intent_modes.jsonl
    memory_multiturn.jsonl
    research_tasks.jsonl
    rag_qrels.jsonl
  scorers/
    tool_accuracy.py
    plan_coherence.py
    memory_recall.py
    task_completion.py
    trajectory.py
    efficiency.py
    research_rubric.py
    rag_ir.py
    citations.py
  runners/
    component_runner.py
    e2e_runner.py
    macro_aggregator.py
```

CLI:

```bash
uv run python main.py eval run --suite component
uv run python main.py eval run --suite research_smoke
uv run python main.py eval compare --baseline main --candidate HEAD
```

---

## 3. CI policy

| Suite | When |
|-------|------|
| `component` | Every PR (must pass) |
| `research_smoke` | Nightly / optional PR with secrets |
| Efficiency budgets | Fail if token/latency regresses > configured % |

---

## 4. Self-improve link

Failed trajectories → new fixtures + strategy memory updates.  
Eval set grows from production failures.
