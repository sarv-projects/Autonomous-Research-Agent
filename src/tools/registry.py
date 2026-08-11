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

import threading
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

        1. Primary tool (highest priority, e.g. Firecrawl)
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

        # ── Per-call provider fallback chain (extracurricular web-UI) ──
        # Primary tools are tried ONE AT A TIME in priority order (Exa → Tavily →
        # Firecrawl → …). A tool that raises (rate limit, timeout) or returns
        # nothing falls through to the next. "always" tools (Wikipedia) run
        # CONCURRENTLY on a daemon thread so a slow/timeout primary never delays
        # the always-on fallback source; their results are merged when the chain
        # resolves. A rate-limited paid provider therefore never kills a round.
        all_results: list[dict] = []
        seen_urls: set[str] = set()

        def _merge(rs: list[dict]) -> None:
            for r in rs:
                url = r.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_results.append(r)

        # Start the always-tools (Wikipedia) in parallel with the primary chain.
        always_results: list[dict] = []
        always_done = threading.Event()

        def _run_always() -> None:
            try:
                for tool in always_tools:
                    try:
                        always_results.extend(_parallel_search_with_tool(tool, queries, max_results))
                    except Exception as e:
                        print(f"  [tool:{tool.name}] search failed: {e}")
            finally:
                always_done.set()

        threading.Thread(target=_run_always, daemon=True).start()

        for tool in primary_tools:
            try:
                results = _parallel_search_with_tool(tool, queries, max_results)
            except Exception as e:
                print(f"  [tool:{tool.name}] search failed: {e} — trying next provider")
                continue
            if results:
                _merge(results)
                print(f"  [tool:{tool.name}] primary search OK ({len(results)} raw results)")
                break
            print(f"  [tool:{tool.name}] returned 0 results — trying next provider")

        always_done.wait(timeout=60)
        _merge(always_results)

        all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        return all_results

    def extract(self, urls: list[str]) -> list[dict]:
        """Extract content from URLs using the best available extract tool.

        Tools are tried in priority order (highest first); the first tool that
        returns a non-empty result wins. A tool returning [] (e.g. Wikipedia
        for a non-Wikipedia URL) falls through to the next candidate.
        """
        candidates = sorted(
            (t for t in self.list_all() if t.extract_fn),
            key=lambda t: -t.priority,
        )
        for tool in candidates:
            try:
                out = tool.extract_fn(urls)
                if out:
                    return out
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
