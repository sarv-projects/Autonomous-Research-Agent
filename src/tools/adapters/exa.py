"""
Exa Neural Search Adapter — semantic search for research queries.

Uses EXA_API_KEY if configured in environment.
"""

from __future__ import annotations

import os
import json
import urllib.request
from typing import List, Dict


def exa_search(query: str, max_results: int = 10) -> List[Dict]:
    """Neural web search via Exa API (https://docs.exa.ai).

    Returns results with full text when available (contents.text).
    """
    api_key = os.getenv("EXA_API_KEY", "")
    if not api_key:
        return []

    try:
        url = "https://api.exa.ai/search"
        payload = {
            "query": query,
            "numResults": min(max(max_results, 1), 25),
            "type": "auto",
            "contents": {
                "text": {"maxCharacters": 8000},
            },
            "useAutoprompt": True,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "accept": "application/json",
                "content-type": "application/json",
                "x-api-key": api_key,
            },
        )
        with urllib.request.urlopen(req, timeout=30.0) as resp:
            body = json.loads(resp.read().decode("utf-8"))

        results = []
        for r in body.get("results", []):
            text = r.get("text") or ""
            # Some responses nest text under highlights
            if not text and isinstance(r.get("contents"), dict):
                text = r["contents"].get("text") or ""
            results.append({
                "title": r.get("title", "") or "",
                "url": r.get("url", "") or "",
                "content": text[:2500],
                "raw_content": text,
                "score": float(r.get("score") or 0.9),
                "source": "exa",
                "published_date": r.get("publishedDate") or r.get("published_date") or "",
            })
        return results
    except Exception as e:
        print(f"  [exa] search failed ({e})")
        return []


def exa_extract(urls: List[str]) -> List[Dict]:
    """Extract full page text via Exa /contents API."""
    api_key = os.getenv("EXA_API_KEY", "")
    if not api_key or not urls:
        return []

    try:
        url = "https://api.exa.ai/contents"
        payload = {
            "urls": urls[:20],
            "text": {"maxCharacters": 12000},
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "accept": "application/json",
                "content-type": "application/json",
                "x-api-key": api_key,
            },
        )
        with urllib.request.urlopen(req, timeout=45.0) as resp:
            body = json.loads(resp.read().decode("utf-8"))

        results = []
        for r in body.get("results", []):
            text = r.get("text") or ""
            results.append({
                "url": r.get("url", ""),
                "content": text,
                "title": r.get("title", "") or "",
                "source": "exa",
            })
        return results
    except Exception as e:
        print(f"  [exa] extract failed ({e})")
        return []
