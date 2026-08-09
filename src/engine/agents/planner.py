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
    """Analyze the query and generate a research plan with outline and queries."""
    state["status"] = "Planning research..."
    print(f"\n🧠 [Planner] Analyzing query: {state['query'][:80]}")

    prompt = f"""Analyze this research query and create a structured plan.

Query: "{state['query']}"

Return a JSON object with:
  - "topic": main topic (string)
  - "subtopics": 3-5 key subtopics to investigate (list of strings)
  - "outline": list of section objects with "title" and "queries" (list of search queries for that section)
  - "source_types": recommended source types (e.g. "academic", "news", "documentation")
  - "search_queries": first wave of 3-5 specific search queries

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
    state["search_queries"] = plan.get("search_queries", [state["query"]])[:5]
    state["outline"] = [
        {"title": s.get("title", f"Section {i+1}"), "order": i}
        for i, s in enumerate(plan.get("outline", []))
    ]
    state["findings"] = [f"Research topic: {plan.get('topic', state['query'])}"]
    state["status"] = f"Plan: {len(state['outline'])} sections, {len(state['search_queries'])} queries"
    print(f"  Outline: {[s['title'] for s in state['outline']]}")
    print(f"  Initial queries: {state['search_queries']}")
    return state
