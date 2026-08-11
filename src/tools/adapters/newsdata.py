"""
NewsData.io News Adapter — keyed supplement to GDELT with clean JSON.

Free tier: 200 credits/day (~2,000 articles), commercial use permitted.
Useful when the researcher wants structured categories + source metadata
in addition to GDELT's raw global feed.

Env: NEWSDATA_API_KEY (register at https://newsdata.io)
"""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from typing import List, Dict


def newsdata_search(query: str, max_results: int = 6) -> List[Dict]:
    """News search via NewsData.io API (keyed; free tier is commercial-OK)."""
    api_key = os.getenv("NEWSDATA_API_KEY", "")
    if not api_key:
        return []

    try:
        q = urllib.parse.quote(query[:200])
        params = (
            f"apikey={api_key}&q={q}&language=en"
            f"&size={min(max(max_results, 1), 10)}"
        )
        url = f"https://newsdata.io/api/1/news?{params}"
        req = urllib.request.Request(
            url,
            headers={"accept": "application/json", "user-agent": "research-agent/1.0"},
        )
        with urllib.request.urlopen(req, timeout=15.0) as resp:
            body = json.loads(resp.read().decode("utf-8", "replace"))

        results: List[Dict] = []
        for a in body.get("results", [])[:max_results]:
            title = a.get("title", "") or ""
            link = a.get("link", "") or ""
            if not link:
                continue
            pub = a.get("pubDate", "") or ""
            date = pub[:10] if len(pub) >= 10 else ""
            snippet = a.get("description", "") or ""
            content = (f"({date}) {snippet}" if date else snippet)[:1200]
            results.append({
                "title": title,
                "url": link,
                "content": content,
                "raw_content": content,
                "score": 0.9,
                "source": "newsdata",
                "published_date": date,
                "source_name": a.get("source_id", "") or "",
                "language": a.get("language", ""),
            })
        return results
    except Exception as e:
        print(f"  [newsdata] search failed ({e})")
        return []


def newsdata_extract(urls: List[str]) -> List[Dict]:
    """No extract endpoint — fall through to the built-in scraper."""
    return []
