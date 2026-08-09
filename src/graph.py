"""
Build the multi-agent LangGraph research agent graph.

Agent roles:
  Planner → [Thinker: plan refine] → Researcher (gather + analyze)
    → [Thinker: contradiction check] → Critic
    ↺ (back to Researcher if gaps)
    → [Triangulator: bias mitigation if subjective] → Synthesizer → Compiler

Thinker + Triangulator are integrated inline — they skip themselves when
not needed, making them safe defaults for all modes.
"""

from langgraph.graph import StateGraph

from src.state import ResearchState, initial_state

# Import agents to trigger registration
import src.engine.agents  # noqa: F401
from src.engine.agents.registry import get_agent


def should_continue_research(state: ResearchState) -> str:
    """Conditional: more research or proceed to synthesis?"""
    if state.get("needs_more_research", False):
        return "research_again"
    return "synthesize"


def build_graph() -> StateGraph:
    """Build the multi-agent research graph with Thinker integration."""

    builder = StateGraph(ResearchState)

    # ── Agent nodes ──
    builder.add_node("planner",                   get_agent("planner"))
    builder.add_node("thinker_plan_refine",       get_agent("thinker_plan_refine"))
    builder.add_node("researcher_gather",         get_agent("researcher_gather"))
    builder.add_node("researcher_analyze",        get_agent("researcher_analyze"))
    builder.add_node("thinker_contradiction_check", get_agent("thinker_contradiction_check"))
    builder.add_node("critic",                    get_agent("critic"))
    builder.add_node("triangulator",              get_agent("triangulator"))
    builder.add_node("synthesizer_outline",       get_agent("synthesizer_outline"))
    builder.add_node("synthesizer_write",         get_agent("synthesizer_write"))
    builder.add_node("compiler",                  get_agent("compiler"))

    # ── Flow ──
    builder.set_entry_point("planner")

    # Plan → Thinker refine → Research loop
    builder.add_edge("planner", "thinker_plan_refine")
    builder.add_edge("thinker_plan_refine", "researcher_gather")
    builder.add_edge("researcher_gather", "researcher_analyze")
    builder.add_edge("researcher_analyze", "thinker_contradiction_check")
    builder.add_edge("thinker_contradiction_check", "critic")

    # Critic: research more or proceed to triangulation then synthesis
    builder.add_conditional_edges(
        "critic",
        should_continue_research,
        {
            "research_again": "researcher_gather",   # loop back
            "synthesize": "triangulator",             # proceed → bias check → synthesis
        },
    )

    # Triangulator → Synthesis outline
    builder.add_edge("triangulator", "synthesizer_outline")

    # Synthesis outline → write each section
    builder.add_edge("synthesizer_outline", "synthesizer_write")

    # Synthesis → Compile final report
    builder.add_edge("synthesizer_write", "compiler")
    builder.set_finish_point("compiler")

    return builder.compile()


def run_research(query: str, mode: str = "standard") -> ResearchState:
    """Run the full multi-agent research workflow with progress tracking.

    Args:
        query: Research topic/question
        mode: Research mode name — thinker only fires on accurate/comprehensive dials
    """
    from src.engine.modes import load_modes, get_mode
    from src.engine.progress import get_progress

    registry = load_modes()
    mode_config = get_mode(registry, mode)

    # Start progress tracking for dashboard SSE
    progress = get_progress()
    max_iters = mode_config.budgets.max_iterations
    progress.start(query, max_iterations=max_iters)

    # Disable Thinker/Triangulator per quality dial before building graph
    from src.engine.agents.thinker import disable_thinker as _disable_thinker
    from src.engine.agents.triangulator import disable_triangulator as _disable_triangulator
    dial = mode_config.quality
    if not dial.thinker_enabled:
        _disable_thinker()
    if not dial.triangulation_enabled:
        _disable_triangulator()

    graph = build_graph()
    state = initial_state(query, max_iterations=max_iters)
    state["mode"] = mode  # for factoid extraction gating

    try:
        result = graph.invoke(state)
        progress.update(stage="complete", finished=True, status="Research complete",
                        findings_count=len(result.get("findings", [])),
                        factoids_count=len(result.get("factoids", [])))
        return result
    except Exception as e:
        progress.update(stage="error", finished=True, error=str(e))
        raise
