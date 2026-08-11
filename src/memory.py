"""Persistent memory for past searches using a JSON file."""

import json
import os
import time

MEMORY_FILE = os.path.expanduser("~/.providence_memory.json")


def _load() -> list[dict]:
    if not os.path.exists(MEMORY_FILE):
        return []
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def _save(memory: list[dict]) -> None:
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory[-50:], f, indent=2)  # keep last 50


def save_search(query: str, search_queries: list[str], report_path: str, findings: list[str]) -> None:
    """Save a completed search to memory."""
    memory = _load()
    entry = {
        "query": query,
        "search_queries": search_queries,
        "report_path": report_path,
        "findings_count": len(findings),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    memory.append(entry)
    _save(memory)


def get_history(limit: int = 5) -> list[dict]:
    """Get recent search history."""
    memory = _load()
    return memory[-limit:]


def find_similar(query: str) -> list[dict]:
    """Simple keyword match to find past searches on similar topics."""
    memory = _load()
    keywords = set(query.lower().split())
    matches = []
    for entry in memory:
        entry_words = set(entry["query"].lower().split())
        overlap = keywords & entry_words
        if len(overlap) >= 2:
            matches.append(entry)
    return matches[-3:]  # last 3 matches
