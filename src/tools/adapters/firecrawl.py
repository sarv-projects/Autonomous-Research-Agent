"""
Firecrawl adapter — search + scrape, cloud OR self-hosted.

Cloud:   POST https://api.firecrawl.dev/v2  — needs FIRECRAWL_API_KEY
Self:    POST http://localhost:3002/v2        — no key, runs via Docker

Self-hosted setup (one command):
    docker run -d -p 3002:3002 --name firecrawl ghcr.io/firecrawl/firecrawl:latest

With USE_DB_AUTHENTICATION=false (default in self-hosted), no auth is required.
Set FIRECRAWL_BASE_URL to override the default http://localhost:3002.

Priority:
  1. FIRECRAWL_API_KEY → cloud API
  2. Self-hosted reachable at FIRECRAWL_BASE_URL or localhost:3002 → free, no key
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

FIRE_CLOUD = "https://api.firecrawl.dev"
FIRE_SELF_DEFAULT = "http://localhost:3002"
FIRE_TIMEOUT = 30.0


def _get_base_and_key() -> tuple[str, str]:
    """Return (base_url, api_key). Cloud if key set, else self-hosted."""
    key = os.getenv("FIRECRAWL_API_KEY", "")
    if key:
        return FIRE_CLOUD, key
    base = os.getenv("FIRECRAWL_BASE_URL", FIRE_SELF_DEFAULT)
    return base.rstrip("/"), ""


def _is_self_hosted() -> bool:
    """Check if a self-hosted Firecrawl instance is reachable."""
    base, key = _get_base_and_key()
    if key:
        return False  # cloud mode
    try:
        req = urllib.request.Request(
            f"{base}/v2/health",
            headers={"User-Agent": "AutonomousResearchAgent/1.0"},
        )
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            return resp.status == 200
    except Exception:
        return False


def _request(base: str, key: str, endpoint: str, payload: dict) -> dict:
    """Make a Firecrawl API request (works for both cloud and self-hosted)."""
    body = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "AutonomousResearchAgent/1.0",
    }
    if key:
        headers["Authorization"] = f"Bearer {key}"

    req = urllib.request.Request(
        f"{base}{endpoint}", data=body, method="POST", headers=headers,
    )
    with urllib.request.urlopen(req, timeout=FIRE_TIMEOUT) as resp:
        return json.loads(resp.read().decode())


def firecrawl_search(query: str, max_results: int = 5) -> list[dict]:
    """Search the web via Firecrawl (cloud or self-hosted)."""
    if not query.strip():
        return []

    base, key = _get_base_and_key()
    try:
        data = _request(base, key, "/v2/search", {
            "query": query,
            "limit": min(max_results, 10),
            "sources": ["web"],
        })
    except Exception as e:
        mode = "cloud" if key else "self-hosted"
        print(f"  [firecrawl:{mode}] search failed: {e}")
        return []

    results = []
    web_results = data.get("data", {}).get("web", [])
    source_tag = "firecrawl" if key else "firecrawl-self"
    for item in web_results:
        markdown = item.get("markdown", "") or item.get("description", "")
        results.append({
            "title": item.get("title", "") or item.get("metadata", {}).get("title", ""),
            "url": item.get("url", ""),
            "content": item.get("description", "")[:500],
            "raw_content": markdown,
            "score": 0.85,
            "source": source_tag,
        })

    return results[:max_results]


def firecrawl_scrape(url: str) -> dict:
    """Scrape a single URL via Firecrawl."""
    base, key = _get_base_and_key()
    try:
        data = _request(base, key, "/v2/scrape", {
            "url": url,
            "formats": ["markdown"],
            "onlyMainContent": True,
        })
        content = data.get("data", {}).get("markdown", "")
        title = data.get("data", {}).get("metadata", {}).get("title", "")
        return {"url": url, "content": content, "title": title}
    except Exception as e:
        print(f"  [firecrawl] scrape failed for {url}: {e}")
        return {}


def firecrawl_extract(urls: list[str]) -> list[dict]:
    """Extract content from multiple URLs via Firecrawl."""
    if not urls:
        return []
    results = []
    for url in urls[:5]:
        r = firecrawl_scrape(url)
        if r:
            results.append(r)
    return results
