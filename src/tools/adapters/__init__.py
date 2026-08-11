"""
Tool adapters — zero-config by default, optional paid/local tools if available.

Always available (no API key, no Docker, no setup):
  - Wikipedia — search + extract (free, factual)
  - Built-in scraper — extract any URL to clean markdown via trafilatura
  - DuckDuckGo — lightweight web search fallback
  - MinerU — PDF & document parser (PyPDF fallback)
  - Nougat — Academic PDF & LaTeX equation OCR (PyPDF fallback)

Primary Search & Crawling:
  - Exa — ultra-fast neural search (needs EXA_API_KEY, priority 110)
  - Tavily — search + extract (needs TAVILY_API_KEY, priority 105)
  - Firecrawl — self-hosted Docker (localhost:3002) or cloud API (priority 100)
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

# ── MinerU Document Parser (PDF extract + arXiv academic search) ──────
def _register_mineru() -> None:
    from .mineru import mineru_extract, mineru_search
    register_tool(
        name="mineru",
        capabilities={"extract", "pdf", "documents", "free", "academic"},
        search_fn=mineru_search,
        extract_fn=mineru_extract,
        priority=15,
    )

# ── Nougat Academic OCR (PDF/math extract + arXiv search) ────────────
def _register_nougat() -> None:
    from .nougat import nougat_extract, nougat_search
    register_tool(
        name="nougat",
        capabilities={"extract", "pdf", "latex", "math", "academic", "free"},
        search_fn=nougat_search,
        extract_fn=nougat_extract,
        priority=20,
    )

# ── Firecrawl (Primary Web Search & Crawling — Cloud or Self-Hosted Docker) ──
def _register_firecrawl() -> None:
    from .firecrawl import firecrawl_search, firecrawl_extract, _is_self_hosted
    has_key = bool(os.getenv("FIRECRAWL_API_KEY"))
    self_hosted = _is_self_hosted()
    caps = {"web_search", "crawl", "extract", "primary"}
    if has_key:
        caps.add("paid")
    else:
        caps.add("free")

    register_tool(
        name="firecrawl",
        capabilities=caps,
        search_fn=firecrawl_search,
        extract_fn=firecrawl_extract,
        priority=100,
    )

# ── Tavily (optional — needs TAVILY_API_KEY) ──────────────────────────
def _register_tavily() -> None:
    from .tavily import tavily_search, tavily_extract
    if not os.getenv("TAVILY_API_KEY"):
        return
    register_tool(
        name="tavily",
        capabilities={"web_search", "extract", "paid"},
        search_fn=tavily_search,
        extract_fn=tavily_extract,
        priority=105,
    )

# ── Exa (PRIMARY when EXA_API_KEY set — neural search + content) ─────
def _register_exa() -> None:
    from .exa import exa_search, exa_extract
    if not os.getenv("EXA_API_KEY"):
        return
    register_tool(
        name="exa",
        capabilities={"web_search", "neural", "extract", "paid", "primary"},
        search_fn=exa_search,
        extract_fn=exa_extract,
        priority=200,  # above Firecrawl/Tavily — primary research search
    )


# Auto-register tools
_register_wikipedia()
_register_builtin()
_register_mineru()
_register_nougat()
_register_firecrawl()
_register_tavily()
_register_exa()
