import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


def search_web(query: str, max_results: int = 5) -> list[dict]:
    """Search the web via Tavily. Returns results with full content."""
    response = client.search(
        query=query,
        search_depth="advanced",
        max_results=max_results,
        include_raw_content=True,
    )
    return response["results"]


def parallel_search(queries: list[str], max_results: int = 5) -> list[dict]:
    """Run multiple searches in parallel, deduplicate by URL."""
    all_results = []
    seen_urls = set()

    with ThreadPoolExecutor(max_workers=len(queries)) as executor:
        futures = {executor.submit(search_web, q, max_results): q for q in queries}
        for future in as_completed(futures):
            try:
                results = future.result()
                for r in results:
                    url = r.get("url", "")
                    if url not in seen_urls:
                        seen_urls.add(url)
                        all_results.append(r)
            except Exception as e:
                print(f"  [search] query failed: {e}")

    all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
    return all_results


def extract_content(urls: list[str]) -> list[dict]:
    """Extract full markdown content from specific URLs."""
    if not urls:
        return []
    try:
        response = client.extract(urls=urls, format="markdown")
        return response.get("results", [])
    except Exception as e:
        print(f"  [extract] failed: {e}")
        return []
