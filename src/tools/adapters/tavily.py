"""
Tavily Search Adapter — search + extract via Tavily API.

Uses TAVILY_API_KEY if configured in environment.
"""

from __future__ import annotations

import os
import json
import urllib.request
from typing import List, Dict


def tavily_search(query: str, max_results: int = 5) -> List[Dict]:
    """Execute search via Tavily API with raw content included."""
    api_key = os.getenv("TAVILY_API_KEY", "")
    if not api_key:
        return []

    try:
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": api_key,
            "query": query,
            "max_results": min(max_results, 10),
            "include_raw_content": True,
            "search_depth": "basic",
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "accept": "application/json",
                "content-type": "application/json",
            }
        )
        with urllib.request.urlopen(req, timeout=10.0) as resp:
            body = json.loads(resp.read().decode("utf-8"))

        results = []
        for r in body.get("results", []):
            markdown = r.get("raw_content", "") or r.get("content", "")
            results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("content", "")[:1000],
                "raw_content": markdown,
                "score": r.get("score", 0.85),
                "source": "tavily"
            })
        return results
    except Exception as e:
        print(f"  [tavily] search failed ({e})")
        return []


def tavily_extract(urls: List[str]) -> List[Dict]:
    """Extract content from URLs via Tavily extract API."""
    api_key = os.getenv("TAVILY_API_KEY", "")
    if not api_key or not urls:
        return []

    try:
        url = "https://api.tavily.com/extract"
        payload = {"api_key": api_key, "urls": urls[:5]}
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "accept": "application/json",
                "content-type": "application/json",
            }
        )
        with urllib.request.urlopen(req, timeout=15.0) as resp:
            body = json.loads(resp.read().decode("utf-8"))

        results = []
        for r in body.get("results", []):
            results.append({
                "url": r.get("url", ""),
                "content": r.get("raw_content", ""),
                "title": r.get("url", "")
            })
        return results
    except Exception as e:
        print(f"  [tavily] extract failed ({e})")
        return []
