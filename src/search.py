"""
Primary Search & Extraction Engine — Powered by Firecrawl (self-hosted or cloud)
with zero-config built-in search fallback.

Firecrawl:
  - Self-hosted: http://localhost:3002 (zero API key, free local Docker container)
  - Cloud: https://api.firecrawl.dev (if FIRECRAWL_API_KEY set)

Built-in Fallback:
  - DuckDuckGo HTML + Wikipedia + Trafilatura scraper (always-on, zero setup)
"""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

from src.tools.adapters.firecrawl import (
    firecrawl_search,
    firecrawl_extract,
    _is_self_hosted,
    _get_base_and_key,
)
from src.tools.adapters.builtin_scraper import builtin_search, builtin_extract

load_dotenv()


def search_web(query: str, max_results: int = 5) -> list[dict]:
    """Search the web via Firecrawl (self-hosted or cloud) with built-in search fallback."""
    if not query.strip():
        return []

    base, key = _get_base_and_key()
    has_self_hosted = _is_self_hosted()

    # Try Firecrawl if self-hosted container is active or cloud key is set
    if key or has_self_hosted:
        try:
            results = firecrawl_search(query, max_results=max_results)
            if results:
                return results
        except Exception as e:
            mode = "cloud" if key else "self-hosted"
            print(f"  [search:firecrawl-{mode}] search failed: {e} — using built-in search fallback")

    # Fallback to zero-config DuckDuckGo / Builtin search
    return builtin_search(query, max_results=max_results)


def parallel_search(queries: list[str], max_results: int = 5) -> list[dict]:
    """Run multiple searches in parallel, deduplicate by URL."""
    if not queries:
        return []

    all_results = []
    seen_urls = set()

    with ThreadPoolExecutor(max_workers=min(len(queries), 5)) as executor:
        futures = {executor.submit(search_web, q, max_results): q for q in queries}
        for future in as_completed(futures):
            try:
                results = future.result()
                for r in results:
                    url = r.get("url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        all_results.append(r)
            except Exception as e:
                print(f"  [search] parallel search query failed: {e}")

    all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
    return all_results


def extract_content(urls: list[str]) -> list[dict]:
    """Extract full content from specific URLs via Firecrawl or built-in scraper."""
    if not urls:
        return []

    base, key = _get_base_and_key()
    has_self_hosted = _is_self_hosted()

    if key or has_self_hosted:
        try:
            results = firecrawl_extract(urls)
            if results:
                return results
        except Exception as e:
            print(f"  [extract:firecrawl] extract failed: {e} — using built-in scraper fallback")

    return builtin_extract(urls)
