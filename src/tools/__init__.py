"""
Modular tool bus for the research agent.

Tools are registered with capability tags and executed through a unified
interface. The Researcher agent queries the registry to find available tools
and falls back gracefully when tools are unavailable.

Built-in: Tavily (web search), Wikipedia (free background facts).
Optional: Firecrawl (crawl), Exa (neural search).
"""

from .registry import ToolRegistry, register_tool, get_registry
from .executor import execute_searches, extract_pages

# Auto-register adapters on import
from . import adapters  # noqa: F401

__all__ = [
    "ToolRegistry",
    "register_tool",
    "get_registry",
    "execute_searches",
    "extract_pages",
]
