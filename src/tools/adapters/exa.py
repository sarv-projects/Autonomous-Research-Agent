"""
Exa Neural Search Adapter — semantic search for research queries.

Uses EXA_API_KEY if configured in environment.
"""

from __future__ import annotations

import os
import json
import urllib.request
from typing import List, Dict


def exa_search(query: str, max_results: int = 5) -> List[Dict]:
    """Execute neural web search via Exa API."""
    api_key = os.getenv("EXA_API_KEY", "")
    if not api_key:
        return []

    try:
        url = "https://api.exa.ai/search"
        payload = {
            "query": query,
            "numResults": max_results,
            "contents": {"text": True}
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "accept": "application/json",
                "content-type": "application/json",
                "x-api-key": api_key
            }
        )
        with urllib.request.urlopen(req, timeout=10.0) as resp:
            body = json.loads(resp.read().decode("utf-8"))

        results = []
        for r in body.get("results", []):
            results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("text", "")[:2000],
                "raw_content": r.get("text", ""),
                "score": r.get("score", 0.8),
                "source": "exa"
            })
        return results
    except Exception as e:
        print(f"  [exa] search failed ({e})")
        return []


def exa_extract(urls: List[str]) -> List[Dict]:
    """Extract content from URLs via Exa contents API."""
    api_key = os.getenv("EXA_API_KEY", "")
    if not api_key or not urls:
        return []

    try:
        url = "https://api.exa.ai/contents"
        payload = {"urls": urls[:5], "text": True}
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "accept": "application/json",
                "content-type": "application/json",
                "x-api-key": api_key
            }
        )
        with urllib.request.urlopen(req, timeout=15.0) as resp:
            body = json.loads(resp.read().decode("utf-8"))

        results = []
        for r in body.get("results", []):
            results.append({
                "url": r.get("url", ""),
                "content": r.get("text", ""),
                "title": r.get("title", "")
            })
        return results
    except Exception as e:
        print(f"  [exa] extract failed ({e})")
        return []
