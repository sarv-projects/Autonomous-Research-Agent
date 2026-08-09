"""
Tool adapters — zero-config by default, optional paid/local tools if available.

Always available (no API key, no Docker, no setup):
  - Wikipedia — search + extract (free, factual)
  - Built-in scraper — extract any URL to clean markdown via trafilatura
  - DuckDuckGo — lightweight web search fallback
  - MinerU — PDF & document parser (PyPDF fallback)
  - Nougat — Academic PDF & LaTeX equation OCR (PyPDF fallback)

Optional (register when API keys are set):
  - Tavily — comprehensive web search + extract (needs TAVILY_API_KEY)
  - Firecrawl — cloud (needs FIRECRAWL_API_KEY) or self-hosted (Docker, localhost:3002)
  - Exa — neural search (needs EXA_API_KEY)
"""

import os
from ..registry import register_tool

# ── Wikipedia (ALWAYS — free, factual, no key) ───────────────────────
def _register_wikipedia() -> None:
    from .wikipedia import wiki_search, wiki_extract
    register_tool(
        name="wikipedia",
        capabilities={"web_search", "factual", "free", "always"},
        search_fn=wiki_search,
        extract_fn=wiki_extract,
        priority=10,
    )

# ── Built-in scraper (ALWAYS — extract any URL, no key, no Docker) ────
def _register_builtin() -> None:
    from .builtin_scraper import builtin_extract, builtin_search
    register_tool(
        name="builtin",
        capabilities={"extract", "free", "always"},
        search_fn=builtin_search,
        extract_fn=builtin_extract,
        priority=5,
    )

# ── MinerU Document Parser (ALWAYS — PDF/Office parser) ───────────────
def _register_mineru() -> None:
    from .mineru import mineru_extract
    register_tool(
        name="mineru",
        capabilities={"extract", "pdf", "documents", "free", "always"},
        search_fn=lambda q, n: [],
        extract_fn=mineru_extract,
        priority=15,
    )

# ── Nougat Academic OCR (ALWAYS — Math PDF parser) ───────────────────
def _register_nougat() -> None:
    from .nougat import nougat_extract
    register_tool(
        name="nougat",
        capabilities={"extract", "pdf", "latex", "math", "academic", "free", "always"},
        search_fn=lambda q, n: [],
        extract_fn=nougat_extract,
        priority=20,
    )

# ── Tavily (optional — needs TAVILY_API_KEY) ──────────────────────────
def _register_tavily() -> None:
    try:
        from src.search import search_web, extract_content
        register_tool(
            name="tavily",
            capabilities={"web_search", "extract", "paid", "primary"},
            search_fn=search_web,
            extract_fn=extract_content,
            priority=100,
        )
    except Exception:
        pass

def _register_firecrawl() -> None:
    from .firecrawl import firecrawl_search, firecrawl_extract, _is_self_hosted
    has_key = bool(os.getenv("FIRECRAWL_API_KEY"))
    self_hosted = _is_self_hosted()
    if not has_key and not self_hosted:
        return
    caps = {"web_search", "crawl", "extract"}
    if has_key:
        caps.add("paid")
    if self_hosted and not has_key:
        caps.add("free")
    register_tool(
        name="firecrawl",
        capabilities=caps,
        search_fn=firecrawl_search,
        extract_fn=firecrawl_extract,
        priority=80,
    )

def _register_exa() -> None:
    from .exa import exa_search, exa_extract
    if not os.getenv("EXA_API_KEY"):
        return
    register_tool(
        name="exa",
        capabilities={"web_search", "neural", "extract", "paid"},
        search_fn=exa_search,
        extract_fn=exa_extract,
        priority=40,
    )


# Auto-register: always-available first, then optional
_register_wikipedia()
_register_builtin()
_register_mineru()
_register_nougat()
_register_tavily()
_register_firecrawl()
_register_exa()
