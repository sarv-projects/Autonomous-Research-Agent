"""Phase E tests — Bias mitigation via Triangulator agent."""
import json
import sys
import os


def test_subjective_detection():
    """Verify heuristic detects subjective queries."""
    from src.engine.agents.triangulator import _is_subjective

    subjective = [
        "What is the best programming language?",
        "Is AI better than humans?",
        "Should we ban social media?",
        "pros and cons of remote work",
        "debate: nuclear energy vs solar",
        "ethical implications of gene editing",
        "compare capitalism and socialism",
        "Python vs Rust for web development",
    ]
    objective = [
        "What is the capital of France?",
        "How does photosynthesis work?",
        "List the planets in order",
        "What is 2 + 2?",
    ]

    subj_count = sum(1 for q in subjective if _is_subjective(q))
    obj_count = sum(1 for q in objective if _is_subjective(q))

    assert subj_count >= 6, f"Expected >=6 subjective detections, got {subj_count}"
    assert obj_count <= 1, f"Expected <=1 false positives, got {obj_count}"
    print(f"1/8 Subjective detection OK ({subj_count}/8 subjectives, {obj_count}/4 objectives)")


def test_should_triangulate_skips_objective():
    """Verify triangulator skips objective queries with few claims."""
    from src.engine.agents.triangulator import _should_triangulate

    state = {"query": "What is 2+2?", "claims": [], "findings": []}
    assert not _should_triangulate(state), "Should skip objective math query"
    print("2/8 Skips objective queries OK")


def test_should_triangulate_triggers_subjective():
    """Verify triangulator triggers on subjective questions."""
    from src.engine.agents.triangulator import _should_triangulate

    state = {"query": "Is AI better than humans at coding?", "claims": [], "findings": []}
    assert _should_triangulate(state), "Should trigger on subjective comparison"
    print("3/8 Triggers on subjective OK")


def test_should_triangulate_triggers_many_claims():
    """Verify triangulator triggers when many claims exist (diverse findings)."""
    from src.engine.agents.triangulator import _should_triangulate, reset_triangulator

    reset_triangulator()
    state = {
        "query": "What is the weather?",
        "claims": [f"claim {i}" for i in range(10)],
        "findings": [],
    }
    assert _should_triangulate(state), "Should trigger with 10 claims"
    reset_triangulator()
    print("4/8 Triggers on many claims OK")


def test_triangulator_skip_when_not_needed():
    """Verify triangulator is a no-op when query is objective."""
    from src.engine.agents.triangulator import triangulator, reset_triangulator

    reset_triangulator()
    state = {
        "query": "What is the speed of light?",
        "claims": [],
        "findings": ["first finding"],
        "status": "idle",
    }
    result = triangulator(state)
    assert result is state, "Should return state unchanged"
    assert result["status"] == "idle", "Status should not change"
    assert result["findings"] == ["first finding"], "Findings should not change"
    print("5/8 No-op on objective query OK")


def test_subjective_pattern_coverage():
    """Verify the subjective pattern list covers common bias triggers."""
    from src.engine.agents.triangulator import SUBJECTIVE_PATTERNS

    assert len(SUBJECTIVE_PATTERNS) >= 8, f"Expected >=8 patterns, got {len(SUBJECTIVE_PATTERNS)}"
    # All should be valid regex
    for pattern in SUBJECTIVE_PATTERNS:
        import re
        re.compile(pattern)  # should not raise
    print(f"6/8 Pattern coverage OK ({len(SUBJECTIVE_PATTERNS)} patterns, all valid)")


def test_reset_triangulator():
    """Verify reset clears rate limit state and atomic slot claiming works."""
    from src.engine.agents.triangulator import (
        reset_triangulator, _should_triangulate,
        _tri_count, _last_triangulation, _tri_lock,
    )
    import time

    # Directly set internal state to simulate exhausted counter
    with _tri_lock:
        _tri_count[0] = 5
        _last_triangulation[0] = time.time()

    assert _tri_count[0] >= 3, "Should be at/above max before reset"

    # Now _should_triangulate should return False (counter exhausted)
    state = {"query": "Is this better than that?", "claims": [], "findings": []}
    assert not _should_triangulate(state), "Should reject when counter exhausted"

    # Reset and verify
    reset_triangulator()
    assert _tri_count[0] == 0, "Tri count should reset to 0"
    assert _last_triangulation[0] == 0.0, "Last triangulation should reset to 0"

    # Now _should_triangulate should return True again (atomically claims slot)
    assert _should_triangulate(state), "Should accept after reset"
    # Slot was claimed — counter should be 1 (even though we didn't call triangulator)
    assert _tri_count[0] == 1, f"Slot should be claimed: got {_tri_count[0]}"
    reset_triangulator()
    print("7/8 Reset + atomic claim OK")


def test_graph_has_triangulator_node():
    """Verify triangulator is registered and in the graph."""
    from src.engine.agents.registry import get_agent
    from src.graph import build_graph

    # Agent registered
    agent = get_agent("triangulator")
    assert agent is not None, "Triangulator should be registered"
    assert callable(agent), "Triangulator should be callable"

    # Graph contains the node
    graph = build_graph()
    nodes = graph.get_graph().nodes
    assert "triangulator" in nodes, "Graph should contain triangulator node"
    print(f"8/8 Graph integration OK (agent registered, graph nodes: {sorted(nodes)[:5]}...)")


if __name__ == "__main__":
    tests = [
        test_subjective_detection,
        test_should_triangulate_skips_objective,
        test_should_triangulate_triggers_subjective,
        test_should_triangulate_triggers_many_claims,
        test_triangulator_skip_when_not_needed,
        test_subjective_pattern_coverage,
        test_reset_triangulator,
        test_graph_has_triangulator_node,
    ]
    passed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  FAIL: {e}")
    print(f"\n{passed}/{len(tests)} tests passed")
    sys.exit(0 if passed == len(tests) else 1)
