"""Quick end-to-end test of the research agent."""

import sys

from src.llm import call_llm
from src.search import search_web, parallel_search
from src.export import save_markdown
from src.memory import save_search, get_history


def test_llm():
    print("1. Testing LLM...", end=" ")
    r = call_llm("You are helpful.", "Say 'OK' in one word.")
    assert "OK" in r or "ok" in r, f"Unexpected: {r}"
    print("PASS")


def test_search():
    print("2. Testing search...", end=" ")
    r = search_web("test", max_results=2)
    assert len(r) >= 1, "No results"
    print(f"PASS ({len(r)} results)")


def test_parallel_search():
    print("3. Testing parallel search...", end=" ")
    r = parallel_search(["test one", "test two"], max_results=2)
    assert len(r) >= 1, "No results"
    print(f"PASS ({len(r)} results)")


def test_export():
    print("4. Testing Markdown export...", end=" ")
    report = "# Test\n\nHello world.\n\n## Section\n- Point 1\n- Point 2"
    md = save_markdown(report, "test_unit")
    assert md.endswith(".md")
    print("PASS")


def test_memory():
    print("5. Testing memory...", end=" ")
    save_search("test query", ["test"], "/tmp/test.md", ["finding 1"])
    h = get_history()
    assert any("test query" in e["query"] for e in h)
    print("PASS")


if __name__ == "__main__":
    tests = [test_llm, test_search, test_parallel_search, test_export, test_memory]
    passed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"FAIL ({e})")
    print(f"\n{passed}/{len(tests)} tests passed")
    sys.exit(0 if passed == len(tests) else 1)
