"""
Critic agent — evaluates research quality and decides whether more research is needed.

Checks:
  - Coverage: are all outline sections addressed?
  - Depth: enough findings per section?
  - Credibility: enough sources?
  - Consistency: contradictions?

Triggers retry by setting needs_more_research=True and providing gap queries.
"""

import json

from src.llm import call_llm
from src.state import ResearchState
from .registry import register

CRITIC_SYSTEM = (
    "You are a research quality evaluator. Your job is to critically assess "
    "whether the research is complete enough to write a report. Be strict but fair. "
    "Return valid JSON."
)


@register("critic")
def critic(state: ResearchState) -> ResearchState:
    """Evaluate research completeness and decide next action."""
    max_iter = state.get("max_iterations", 6)
    state["status"] = f"Evaluating research ({state['iteration']}/{max_iter})..."
    print(f"\n🔎 [Critic] Evaluating iteration {state['iteration']}/{max_iter}")

    findings_text = "\n".join(f"- {f}" for f in state.get("findings", []))
    gaps_text = "\n".join(f"- {g}" for g in state.get("gaps", []))
    outline_titles = [s.get("title", "") for s in state.get("outline", [])]

    prompt = f"""Evaluate if the research is complete enough.

Query: "{state['query']}"
Iteration: {state['iteration']}/{max_iter}
Expected sections: {outline_titles}

Findings so far ({len(state.get('findings', []))} total):
{findings_text[:2000]}

Known gaps:
{gaps_text[:500]}

Consider:
1. Coverage: Are all expected sections addressed with at least some findings?
2. Depth: Is there enough substance for a useful report?
3. Sources: Are there {len(state.get('evidence_map', {}))} evidence URLs — is that enough?
4. Confidence: Are claims consistent or contradictory?

Return JSON:
  - "complete": true/false
  - "reason": brief explanation
  - "confidence": "high"/"medium"/"low"
  - "gap_queries": if not complete, 2-3 NEW search queries to fill gaps"""

    result = call_llm(CRITIC_SYSTEM, prompt)
    try:
        evaluation = json.loads(result.strip().removeprefix("```json").removesuffix("```").strip())
    except json.JSONDecodeError:
        evaluation = {"complete": True, "reason": "Evaluation failed", "confidence": "low", "gap_queries": []}

    is_complete = evaluation.get("complete", False)
    reason = evaluation.get("reason", "")

    # Force stop after max iterations
    if state["iteration"] >= max_iter:
        is_complete = True
        reason = f"Reached max iterations ({max_iter})"

    state["needs_more_research"] = not is_complete

    if not is_complete:
        next_queries = evaluation.get("gap_queries", [])
        if next_queries:
            state["search_queries"] = next_queries[:5]
            print(f"  🔄 More needed: {reason}")
            print(f"  Next queries: {next_queries}")
        else:
            state["search_queries"] = [state["query"]]
    else:
        print(f"  ✅ Complete: {reason}")

    state["status"] = f"Evaluation: {'complete' if is_complete else 'needs more'}"
    return state
