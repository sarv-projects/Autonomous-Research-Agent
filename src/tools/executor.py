"""
Tool executor — high-level interface for research agents.

Uses the tool registry to execute searches and extractions across
all available tools with graceful degradation.
"""

from .registry import get_registry


def execute_searches(queries: list[str], max_results: int = 5) -> list[dict]:
    """Run searches across available tools. Uses best available, falls back gracefully.

    Args:
        queries: List of search query strings.
        max_results: Maximum results per query.

    Returns:
        List of unique search results with {title, url, content, raw_content, score}.
    """
    registry = get_registry()
    return registry.search(queries, max_results=max_results)


def extract_pages(urls: list[str]) -> list[dict]:
    """Extract content from URLs using available tools.

    Tries each registered tool's extract capability until one succeeds.
    """
    registry = get_registry()
    return registry.extract(urls)
