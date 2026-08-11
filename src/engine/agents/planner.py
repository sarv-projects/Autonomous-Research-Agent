"""
Planner agent — decomposes the user query into a structured research plan.

Outputs:
  - Topic identification
  - Subtopics
  - Report outline (section titles + initial search queries)
  - Source type preferences
  - First wave of search queries
"""

import json

from src.llm import call_llm
from src.state import ResearchState
from .registry import register

PLANNER_SYSTEM = (
    "You are an expert research planner. Your job is to decompose a research query "
    "into a structured plan with an outline, subtopics, and search queries. "
    "Always return valid JSON. Be thorough and specific."
)


@register("planner")
def planner(state: ResearchState) -> ResearchState:
    """Analyze the query and generate a research plan with outline and queries.

    If state already has an approved plan (plan_approved / skip_planning), reuse it.
    """
    # Resume from user-edited / approved plan
    if state.get("plan_approved") and state.get("plan"):
        plan = state["plan"]
        state["search_queries"] = list(
            state.get("search_queries") or plan.get("search_queries") or [state["query"]]
        )[:8]
        if not state.get("outline"):
            state["outline"] = [
                {"title": s.get("title", f"Section {i+1}"), "order": i}
                for i, s in enumerate(plan.get("outline", []))
            ]
        state["status"] = f"Using approved plan: {len(state.get('outline') or [])} sections"
        print(f"\n🧠 [Planner] Using approved plan ({len(state['search_queries'])} queries)")
        try:
            from src.engine.progress import get_progress
            get_progress().update(stage="planning", status=state["status"], plan=plan)
            get_progress().think("next", "Approved plan — starting research gather")
        except Exception:
            pass
        return state

    state["status"] = "Planning research..."
    try:
        from src.engine.progress import get_progress
        get_progress().update(stage="planning", status=state["status"])
        get_progress().think("next", "Decomposing query into research plan")
    except Exception:
        pass
    print(f"\n🧠 [Planner] Analyzing query: {state['query'][:80]}")

    flags = state.get("mode_flags") or {}
    structured = bool(flags.get("structured_output")) or state.get("mode") == "compare"
    deep = (state.get("mode") or "") in ("deep", "academic", "ultra-long")
    compare_extra = ""
    if structured:
        compare_extra = """
This is a COMPARE / structured mode query. Outline MUST include:
  - Criteria / Evaluation Framework
  - Option A deep dive
  - Option B deep dive (and C if relevant)
  - Head-to-head Comparison Matrix
  - Recommendation / Trade-offs
  - Sources
Search queries should target each option and direct comparisons (A vs B).
"""
    deep_extra = ""
    if deep:
        deep_extra = """
DEEP mode: outline should name real systems/papers where possible, and include
Evaluation Matrix + Failure-Mode Taxonomy sections before Sources.
"""
    clarif = ""
    if state.get("clarifications"):
        clarif = f"\nUser clarifications: {json.dumps(state.get('clarifications'))}\n"

    scout = state.get("scout") or {}
    scout_extra = ""
    if scout:
        scout_extra = f"""
SCOUT HINTS (from pre-research thinker + web):
  refined_query: {scout.get('refined_query', '')}
  must_cover_systems: {json.dumps(scout.get('must_cover_systems') or [])}
  must_cover_papers: {json.dumps((scout.get('must_cover_papers') or [])[:8])}
  eval_axes: {json.dumps(scout.get('eval_axes') or [])}
  failure_modes: {json.dumps(scout.get('failure_modes') or [])}
  outline_hints: {json.dumps(scout.get('outline_hints') or [])}
  seeded_queries: {json.dumps((state.get('search_queries') or [])[:6])}
REQUIRE: outline/sections should name key systems from must_cover_systems when relevant.
REQUIRE: include Evaluation Matrix and Failure-Mode Taxonomy for deep/academic modes.
"""

    prompt = f"""Analyze this research query and create a structured plan.

Query: "{state['query']}"
{clarif}{scout_extra}{compare_extra}{deep_extra}
Return a JSON object with:
  - "topic": main topic (string)
  - "subtopics": 3-5 key subtopics to investigate (list of strings)
  - "outline": list of section objects with "title" and "queries" (list of search queries for that section)
  - "source_types": recommended source types (e.g. "academic", "news", "documentation")
  - "search_queries": first wave of 3-5 specific search queries
  - "rationale": brief why this plan covers the query

Example outline entry:
  {{"title": "Historical Context", "queries": ["history of X", "origins of X"]}}"""

    result = call_llm(PLANNER_SYSTEM, prompt)
    try:
        plan = json.loads(result.strip().removeprefix("```json").removesuffix("```").strip())
    except json.JSONDecodeError:
        plan = {
            "topic": state["query"],
            "subtopics": [],
            "outline": [{"title": "Overview", "queries": [state["query"]]}],
            "source_types": ["web"],
            "search_queries": [state["query"]],
        }

    state["plan"] = plan
    # Prefer plan queries; keep scout seeds if plan weak
    planned_q = plan.get("search_queries") or []
    if planned_q:
        state["search_queries"] = planned_q[:6]
    elif not state.get("search_queries"):
        state["search_queries"] = [state["query"]]
    else:
        state["search_queries"] = list(state.get("search_queries") or [state["query"]])[:6]
    state["outline"] = [
        {"title": s.get("title", f"Section {i+1}"), "order": i}
        for i, s in enumerate(plan.get("outline", []))
    ]
    state["findings"] = [f"Research topic: {plan.get('topic', state['query'])}"]
    state["status"] = f"Plan: {len(state['outline'])} sections, {len(state['search_queries'])} queries"
    print(f"  Outline: {[s['title'] for s in state['outline']]}")
    print(f"  Initial queries: {state['search_queries']}")
    try:
        from src.engine.progress import get_progress
        get_progress().update(stage="planning", status=state["status"], plan=plan)
        get_progress().think("learned", f"Plan topic: {plan.get('topic', '')[:120]}")
    except Exception:
        pass
    return state
