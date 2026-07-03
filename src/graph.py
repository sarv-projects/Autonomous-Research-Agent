"""Build the LangGraph research agent graph."""

from langgraph.graph import StateGraph

from src.state import ResearchState, initial_state
from src.nodes import (
    parse_query,
    plan_searches,
    execute_searches,
    extract_pages,
    deduplicate_content,
    analyze_findings,
    evaluate_research,
    synthesize_report,
    export_report,
)


def should_continue(state: ResearchState) -> str:
    """Conditional edge: decide whether to do more research or synthesize."""
    if state["needs_more_research"]:
        return "research_more"
    return "synthesize"


def build_graph() -> StateGraph:
    """Build and return the compiled research agent graph."""

    builder = StateGraph(ResearchState)

    # Add all nodes
    builder.add_node("parse_query", parse_query)
    builder.add_node("plan_searches", plan_searches)
    builder.add_node("execute_searches", execute_searches)
    builder.add_node("extract_pages", extract_pages)
    builder.add_node("deduplicate", deduplicate_content)
    builder.add_node("analyze_findings", analyze_findings)
    builder.add_node("evaluate", evaluate_research)
    builder.add_node("synthesize_report", synthesize_report)
    builder.add_node("export_report", export_report)

    # Start
    builder.set_entry_point("parse_query")

    # Flow
    builder.add_edge("parse_query", "plan_searches")
    builder.add_edge("plan_searches", "execute_searches")
    builder.add_edge("execute_searches", "extract_pages")
    builder.add_edge("extract_pages", "deduplicate")
    builder.add_edge("deduplicate", "analyze_findings")
    builder.add_edge("analyze_findings", "evaluate")

    # Conditional: research more or synthesize
    builder.add_conditional_edges(
        "evaluate",
        should_continue,
        {
            "research_more": "plan_searches",  # loop back
            "synthesize": "synthesize_report",  # done researching
        },
    )

    builder.add_edge("synthesize_report", "export_report")
    builder.set_finish_point("export_report")

    return builder.compile()


def run_research(query: str) -> ResearchState:
    """Run the full research workflow and return the final state."""
    graph = build_graph()
    state = initial_state(query)
    result = graph.invoke(state)
    return result
