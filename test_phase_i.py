"""Phase I tests — Progressive output: progress tracker, streaming LLM, dashboard."""
import json
import sys
import time


def test_progress_tracker_start():
    """Verify progress tracker initializes correctly."""
    from src.engine.progress import get_progress

    p = get_progress()
    p.start("test query", run_id="test123", max_iterations=4)

    snap = p.snapshot()
    assert snap["query"] == "test query"
    assert snap["run_id"] == "test123"
    assert snap["stage"] == "starting"
    assert snap["max_iterations"] == 4
    assert snap["iteration"] == 0
    assert snap["finished"] is False
    assert snap["elapsed_s"] >= 0
    print("1/8 Progress tracker start OK")


def test_progress_tracker_update():
    """Verify progress tracker updates fields correctly."""
    from src.engine.progress import get_progress

    p = get_progress()
    p.start("q", run_id="r", max_iterations=3)

    p.update(stage="planning", iteration=1, findings_count=5,
             status="Planning research...")
    snap = p.snapshot()
    assert snap["stage"] == "planning"
    assert snap["iteration"] == 1
    assert snap["findings_count"] == 5
    assert snap["status"] == "Planning research..."
    print("2/8 Progress tracker update OK")


def test_progress_tracker_sections():
    """Verify section tracking in progress."""
    from src.engine.progress import get_progress

    p = get_progress()
    p.start("q", run_id="r")

    sections = [
        {"title": "Intro", "content": "Hello world"},
        {"title": "Body", "content": "Some content here"},
    ]
    p.update(stage="writing_section", sections=sections,
             current_section="Body", section_index=2, total_sections=3)

    snap = p.snapshot()
    assert len(snap["sections"]) == 2
    assert snap["sections"][0]["chars"] == 11  # len("Hello world")
    assert snap["sections"][1]["chars"] == 17  # len("Some content here")
    assert snap["current_section"] == "Body"
    assert snap["section_progress"] == "2/3"
    print("3/8 Progress sections OK")


def test_progress_tracker_finish():
    """Verify progress tracker marks finished."""
    from src.engine.progress import get_progress

    p = get_progress()
    p.start("q", run_id="r")
    p.update(stage="complete", finished=True, findings_count=10)

    snap = p.snapshot()
    assert snap["finished"] is True
    assert snap["stage"] == "complete"
    assert snap["findings_count"] == 10
    print("4/8 Progress tracker finish OK")


def test_call_llm_stream_signature():
    """Verify call_llm_stream exists and has correct signature."""
    from src.llm import call_llm_stream
    import inspect

    sig = inspect.signature(call_llm_stream)
    params = list(sig.parameters.keys())
    assert "system_prompt" in params
    assert "user_prompt" in params
    assert "model" in params
    print("5/8 call_llm_stream signature OK")


def test_provider_stream_method():
    """Verify provider has complete_stream method."""
    from src.gateway.providers import OpenAICompatibleProvider

    p = OpenAICompatibleProvider("test", "https://example.com")
    assert hasattr(p, "complete_stream")
    assert callable(p.complete_stream)
    print("6/8 Provider complete_stream exists OK")


def test_gateway_stream_method():
    """Verify gateway has complete_stream method."""
    from src.gateway.router import Gateway

    gw = Gateway()
    assert hasattr(gw, "complete_stream")
    assert callable(gw.complete_stream)
    print("7/8 Gateway complete_stream exists OK")


def test_progress_snapshot_json_serializable():
    """Verify snapshot output is JSON-serializable."""
    from src.engine.progress import get_progress

    p = get_progress()
    p.start("test query", run_id="abc123")
    p.update(stage="researching", iteration=1, findings_count=3)

    snap = p.snapshot()
    # Should not raise
    encoded = json.dumps(snap)
    decoded = json.loads(encoded)
    assert decoded["run_id"] == "abc123"
    assert decoded["stage"] == "researching"
    print("8/8 Snapshot JSON-serializable OK")


if __name__ == "__main__":
    tests = [
        test_progress_tracker_start,
        test_progress_tracker_update,
        test_progress_tracker_sections,
        test_progress_tracker_finish,
        test_call_llm_stream_signature,
        test_provider_stream_method,
        test_gateway_stream_method,
        test_progress_snapshot_json_serializable,
    ]
    passed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"  FAIL: {e}")
    print(f"\n{passed}/{len(tests)} tests passed")
    sys.exit(0 if passed == len(tests) else 1)
