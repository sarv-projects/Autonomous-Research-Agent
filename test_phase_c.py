"""
Phase C tests — multi-agent graph, agents, state, compiler, citation ship gate.

All offline (no API keys). Tests agent registration and graph structure.
Run with:
    uv run python test_phase_c.py
"""

import sys

# ── 1. Agent Registration ───────────────────────────────────────────────
def test_agent_registry():
    import src.engine.agents  # triggers registration
    from src.engine.agents.registry import get_all, get_agent
    agents = get_all()
    expected = {"planner", "researcher_gather", "researcher_analyze",
                "critic", "synthesizer_outline", "synthesizer_write", "compiler"}
    assert expected.issubset(set(agents.keys())), f"Missing agents: {expected - set(agents.keys())}"
    assert callable(get_agent("planner"))
    print("1/8 agent registration OK")


def test_state_has_new_fields():
    from src.state import initial_state
    state = initial_state("test", max_iterations=4)
    assert state["max_iterations"] == 4
    assert "plan" in state
    assert "claims" in state
    assert "gaps" in state
    assert "outline" in state
    assert "sections" in state
    assert "evidence_map" in state
    assert state["evidence_map"] == {}
    assert state["sections"] == []
    print("2/8 state multi-agent fields OK")


# ── 2. Compiler Ship Gate ──────────────────────────────────────────────
def test_ship_gate_empty():
    from src.engine.agents.compiler import _validate_ship_gate
    state = {
        "sections": [],
        "claims": [],
        "evidence_map": {},
        "retrieved_chunks": [],
    }
    passed, issues = _validate_ship_gate(state)
    assert not passed
    assert len(issues) >= 2  # at least "No sections" + "no sources/body"
    print("3/8 ship gate catches empty report OK")


def test_ship_gate_valid():
    from src.engine.agents.compiler import _validate_ship_gate
    state = {
        "sections": [
            {"title": "Introduction", "content": "This is a comprehensive introduction. " * 15, "sources": ["http://a.com"]},
            {"title": "Sources", "content": "[1] http://a.com", "sources": ["http://a.com"]},
        ],
        "claims": [{"text": "Test claim", "evidence_ids": ["http://a.com"]}],
        "evidence_map": {"http://a.com": ["Test claim"]},
        "retrieved_chunks": [],
    }
    passed, issues = _validate_ship_gate(state)
    assert passed, f"Expected pass, got: {issues}"
    print("4/8 ship gate validates good report OK")


def test_compiler_adds_sources_if_missing():
    from src.engine.agents.compiler import compiler as _compiler_func
    state = {
        "query": "test",
        "sections": [
            {"title": "Intro", "content": "Body " * 20, "sources": ["http://a.com"]},
        ],
        "claims": [{"text": "test", "evidence_ids": ["http://a.com"]}],
        "evidence_map": {"http://a.com": ["test"]},
        "retrieved_chunks": [
            {"url": "http://a.com", "title": "Source A", "text": "content", "id": "1", "score": 0.9},
        ],
        "run_id": "test123",
        "iteration": 1,
    }
    result = _compiler_func(state)
    # Should have added a Sources section
    has_sources = any(s["title"] == "Sources" for s in result.get("sections", []))
    assert has_sources, "Compiler should auto-add Sources section"
    assert len(result.get("report", "")) > 50
    print("5/8 compiler adds missing Sources OK")


# ── 3. Graph Structure ──────────────────────────────────────────────────
def test_graph_builds():
    from src.graph import build_graph
    graph = build_graph()
    assert graph is not None
    print("6/8 multi-agent graph builds OK")


def test_graph_nodes_are_registered():
    from src.graph import build_graph
    graph = build_graph()
    # The graph should have all 7 agent nodes
    nodes = graph.get_graph().nodes
    assert "planner" in nodes
    assert "researcher_gather" in nodes
    assert "researcher_analyze" in nodes
    assert "critic" in nodes
    assert "synthesizer_outline" in nodes
    assert "synthesizer_write" in nodes
    assert "compiler" in nodes
    print("7/8 graph agent nodes registered OK")


# ── 4. Backward compat ──────────────────────────────────────────────────
def test_old_nodes_still_work():
    # Verify the legacy nodes.py functions are still importable
    from src.nodes import parse_query, plan_searches, execute_searches
    from src.nodes import extract_pages, ingest_chunks, retrieve_for_analysis
    from src.nodes import analyze_findings, evaluate_research, synthesize_report, export_report
    assert callable(parse_query)
    assert callable(synthesize_report)
    print("8/8 legacy nodes backward compatible OK")


TESTS = [
    test_agent_registry,
    test_state_has_new_fields,
    test_ship_gate_empty,
    test_ship_gate_valid,
    test_compiler_adds_sources_if_missing,
    test_graph_builds,
    test_graph_nodes_are_registered,
    test_old_nodes_still_work,
]

if __name__ == "__main__":
    passed = 0
    for t in TESTS:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"FAIL: {t.__name__} -> {e}")
            import traceback
            traceback.print_exc()
    print(f"\n{passed}/{len(TESTS)} tests passed")
    sys.exit(0 if passed == len(TESTS) else 1)
