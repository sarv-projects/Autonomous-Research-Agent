"""
Autonomous Research Agent
=========================
Built with: LangGraph (orchestration), Groq (LLM), Tavily (web search)

Usage:
    uv run python main.py "your research topic"
    uv run python main.py --history          # show past searches
"""

import sys
import time

from src.graph import run_research
from src.memory import get_history, save_search, find_similar


def print_header(text: str) -> None:
    print()
    print("=" * 60)
    print(f"  {text}")
    print("=" * 60)


def main() -> None:
    args = sys.argv[1:]

    # Show search history
    if "--history" in args or "-h" in args:
        print_header("PAST RESEARCHES")
        history = get_history(10)
        if not history:
            print("  No past searches found.")
        for entry in history:
            print(f"  \u2022 {entry['timestamp']} \u2014 {entry['query']}")
            print(f"    Report: {entry.get('report_path', 'N/A')}")
        return

    # Get query from args
    if not args:
        print("Usage: uv run python main.py <research topic>")
        print("       uv run python main.py --history")
        sys.exit(1)

    query = " ".join(args)

    # Check for similar past searches
    similar = find_similar(query)
    if similar:
        print_header("PAST SIMILAR RESEARCH FOUND")
        for s in similar:
            print(f"  \u2022 {s['timestamp']} \u2014 {s['query']}")
            print(f"    Report: {s.get('report_path', 'N/A')}")
        print()

    # Run research
    print_header(f"RESEARCH: {query}")
    start = time.time()

    try:
        result = run_research(query)
        elapsed = time.time() - start

        print_header("RESEARCH COMPLETE")
        print(f"  Time: {elapsed:.1f}s")
        print(f"  Iterations: {result['iteration']}")
        print(f"  Findings: {len(result['findings'])}")
        print(f"  Sources: {len(result['search_results'])}")
        print(f"  Report: {result.get('markdown_path', 'N/A')}")
        print()

        # Show report preview
        print("\u2500" * 60)
        preview = result.get("report", "")[:500]
        print(preview)
        print("...")
        print("\u2500" * 60)

        # Save to memory
        save_search(
            query=query,
            search_queries=result.get("search_queries", []),
            report_path=result.get("markdown_path", ""),
            findings=result.get("findings", []),
        )

    except Exception as e:
        print(f"\n\u274c Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
