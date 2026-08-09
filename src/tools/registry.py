"""
Tool registry — capability-based tool discovery and selection.

Tools are registered with:
  - name: unique identifier (e.g. "tavily", "wikipedia")
  - capabilities: set of tags (e.g. {"web_search", "factual", "free"})
  - search_fn: callable(query, max_results) -> list[dict]
  - extract_fn: callable(urls) -> list[dict] (optional)
  - priority: int, higher = preferred when multiple tools match
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Optional

SearchFunc = Callable[[str, int], list[dict]]
ExtractFunc = Callable[[list[str]], list[dict]]


class Tool:
    """A registered tool with search and optional extract capability."""
    def __init__(
        self,
        name: str,
        capabilities: set[str],
        search_fn: SearchFunc,
        extract_fn: Optional[ExtractFunc] = None,
        priority: int = 0,
    ) -> None:
        self.name = name
        self.capabilities = capabilities
        self.search_fn = search_fn
        self.extract_fn = extract_fn
        self.priority = priority

    def has_capability(self, cap: str) -> bool:
        return cap in self.capabilities


class ToolRegistry:
    """Registry of all available research tools."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def list_all(self) -> list[Tool]:
        return list(self._tools.values())

    def list_by_capability(self, capability: str) -> list[Tool]:
        """Return tools matching a capability, sorted by priority (desc)."""
        matching = [t for t in self._tools.values() if t.has_capability(capability)]
        matching.sort(key=lambda t: -t.priority)
        return matching

    def search(
        self,
        queries: list[str],
        max_results: int = 5,
        prefer_capability: str = "web_search",
    ) -> list[dict]:
        """Search using the best available tool, always fusing Wikipedia.

        1. Primary tool (highest priority, e.g. Tavily or Firecrawl)
        2. Wikipedia (always queried in parallel as supplementary source)
        Results are merged: primary first (deduped by URL), then Wikipedia novel URLs.
        """
        tools = self.list_by_capability(prefer_capability)
        if not tools:
            tools = self.list_all()

        if not tools:
            return []

        primary_tools = [t for t in tools if not t.has_capability("always")]
        always_tools = [t for t in tools if t.has_capability("always")]

        all_results: list[dict] = []
        seen_urls: set[str] = set()

        # Run primary + always tools in parallel
        search_tools = primary_tools[:1] + always_tools  # best primary + all "always" tools
        if not search_tools:
            search_tools = tools[:1]

        def _search_with(tool: Tool) -> list[dict]:
            return _parallel_search_with_tool(tool, queries, max_results)

        with ThreadPoolExecutor(max_workers=len(search_tools)) as executor:
            future_map = {executor.submit(_search_with, t): t for t in search_tools}
            for future in as_completed(future_map):
                try:
                    results = future.result()
                    for r in results:
                        url = r.get("url", "")
                        if url and url not in seen_urls:
                            seen_urls.add(url)
                            all_results.append(r)
                except Exception as e:
                    tool_name = future_map[future].name
                    print(f"  [tool:{tool_name}] search failed: {e}")

        all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        return all_results

    def extract(self, urls: list[str]) -> list[dict]:
        """Extract content from URLs using the first available tool with extract capability."""
        for tool in self.list_all():
            if tool.extract_fn and urls:
                try:
                    return tool.extract_fn(urls)
                except Exception:
                    continue
        return []


def _parallel_search_with_tool(tool: Tool, queries: list[str], max_results: int) -> list[dict]:
    """Run searches in parallel using a specific tool."""
    all_results: list[dict] = []
    seen_urls: set[str] = set()

    with ThreadPoolExecutor(max_workers=min(len(queries), 8)) as executor:
        futures = {executor.submit(tool.search_fn, q, max_results): q for q in queries}
        for future in as_completed(futures):
            try:
                results = future.result()
                for r in results:
                    url = r.get("url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        all_results.append(r)
            except Exception as e:
                print(f"  [tool:{tool.name}] query failed: {e}")

    all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
    return all_results


# Module-level singleton
_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry


def register_tool(
    name: str,
    capabilities: set[str],
    search_fn: SearchFunc,
    extract_fn: Optional[ExtractFunc] = None,
    priority: int = 0,
) -> Tool:
    """Register a tool in the module-level registry."""
    tool = Tool(name, capabilities, search_fn, extract_fn, priority)
    get_registry().register(tool)
    return tool
