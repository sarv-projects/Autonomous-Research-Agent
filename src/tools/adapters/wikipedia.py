"""
Wikipedia adapter — free search and page content extraction.

Uses the Wikipedia REST API (no API key required):
  - Search: GET /w/api.php?action=query&list=search
  - Extract: GET /w/api.php?action=query&prop=extracts&exintro

Priority: 10 (lower than paid tools, higher than stubs).
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

WIKI_API = "https://en.wikipedia.org/w/api.php"
WIKI_SEARCH_LIMIT = 5
WIKI_TIMEOUT = 15.0


def _wiki_request(params: dict) -> dict:
    """Make a Wikipedia API request and return parsed JSON."""
    params["format"] = "json"
    url = f"{WIKI_API}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        url, headers={"User-Agent": "AutonomousResearchAgent/1.0"}
    )
    with urllib.request.urlopen(req, timeout=WIKI_TIMEOUT) as resp:
        return json.loads(resp.read().decode())


def wiki_search(query: str, max_results: int = 5) -> list[dict]:
    """Search Wikipedia for articles matching the query.

    Returns list of dicts compatible with the tool result format:
    {title, url, content (snippet), raw_content, score}
    """
    if not query.strip():
        return []

    try:
        data = _wiki_request({
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": min(max_results, WIKI_SEARCH_LIMIT),
            "srprop": "snippet",
        })
    except Exception as e:
        print(f"  [wikipedia] search failed: {e}")
        return []

    results = []
    for item in data.get("query", {}).get("search", []):
        title = item.get("title", "")
        page_id = item.get("pageid", 0)
        snippet = item.get("snippet", "")
        # Clean HTML tags from snippet
        snippet = snippet.replace("<span class=\"searchmatch\">", "").replace("</span>", "")
        results.append({
            "title": title,
            "url": f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}",
            "content": snippet,
            "raw_content": snippet,
            "score": 0.7,  # Wikipedia scores high for factual content
            "source": "wikipedia",
        })

    return results[:max_results]


def wiki_extract(urls: list[str]) -> list[dict]:
    """Extract the introductory content from Wikipedia pages.

    Only processes URLs matching wikipedia.org.
    Returns list of {url, content}.
    """
    wiki_urls = [u for u in urls if "wikipedia.org" in u]
    if not wiki_urls:
        return []

    results = []
    for url in wiki_urls[:5]:
        try:
            # Extract page title from URL
            title = url.rstrip("/").split("/")[-1]
            title = urllib.parse.unquote(title).replace("_", " ")

            data = _wiki_request({
                "action": "query",
                "prop": "extracts",
                "exintro": "1",
                "explaintext": "1",
                "titles": title,
            })
            pages = data.get("query", {}).get("pages", {})
            for page in pages.values():
                extract = page.get("extract", "")
                if extract:
                    results.append({
                        "url": url,
                        "content": extract,
                        "title": title,
                    })
        except Exception as e:
            print(f"  [wikipedia] extract failed for {url}: {e}")

    return results
