"""
Factoid Extraction Pipeline — structured JSON extraction, anti-hallucination quote gate,
deduplication, and merging.

Architecture:
  1. Extractor: calls cheap LLM (Zen free / Groq fast) to extract structured factoids
  2. Quote Gate: validates each factoid's source_quote actually appears in the source text
  3. Dedup: removes near-duplicate factoids using text similarity
  4. Merge: combines overlapping factoids from different sources

Token reduction: factoids are ~50-100 tokens each vs 500-800 token raw chunks.
With ~5-10 factoids per chunk, retrieval on factoids cuts context by ~90%.
"""

from __future__ import annotations

import hashlib
import json
import re
from difflib import SequenceMatcher
from typing import Optional

# Lazy import to avoid circular dependency at module level
_llm = None


def _get_llm():
    global _llm
    if _llm is None:
        from src.llm import call_llm
        _llm = call_llm
    return _llm


# ── Factoid schema ──────────────────────────────────────────────────────

FACTOID_TYPES = [
    "entity",       # Named entity (person, org, location, product)
    "relation",     # Relationship between entities
    "event",        # Temporal event with participants
    "statistic",    # Numerical data with context and units
    "definition",   # Concept definition or explanation
    "claim",        # Factual claim with attribution
]

FACTOID_SYSTEM_PROMPT = """You are a precise factoid extraction specialist. Your task is to extract
structured, self-contained factoids from text. Every factoid MUST be verifiable
against the source text.

Rules:
1. Each factoid must have an EXACT source_quote — a substring verbatim from the
   source text that supports the factoid. NEVER fabricate or paraphrase the quote.
2. If you cannot find an exact supporting quote, do NOT create the factoid.
3. Assign confidence based on clarity and specificity:
   - 0.9-1.0: explicit, unambiguous statement
   - 0.7-0.9: clear but could be interpreted differently
   - 0.5-0.7: implied but not directly stated
4. Be concise — each factoid value should be 1-2 sentences max.
5. Include relevant metadata for filtering (entities, topics, numbers).

Output ONLY a JSON array of factoid objects. No other text."""


def factoid_prompt(source_text: str, source_url: str) -> str:
    """Build the extraction prompt for a source text block."""
    return f"""Extract factoids from the following text. For each factoid, include the
EXACT source_quote (verbatim substring from the text) that supports it.

Source URL: {source_url}

Text:
---
{source_text[:8000]}
---

Return a JSON array where each factoid has:
- "type": one of {FACTOID_TYPES}
- "value": concise, self-contained factual statement (1-2 sentences)
- "confidence": number 0.0-1.0
- "source_quote": EXACT substring from the text above that supports this factoid
- "entities": list of entity names mentioned
- "topics": list of topic tags

Only include factoids where you can find an EXACT source_quote in the text above."""


# ── Quote Gate (anti-hallucination) ─────────────────────────────────────

def _normalize_ws(text: str) -> str:
    """Normalize whitespace for fuzzy quote matching."""
    return re.sub(r"\s+", " ", text).strip().lower()


def validate_quote(source_quote: str, source_text: str, threshold: float = 0.85) -> bool:
    """Check that source_quote actually appears in source_text.

    Uses exact substring match first, then fuzzy SequenceMatcher fallback
    for minor whitespace/normalization differences.

    Returns True if the quote is verifiable in the source.
    """
    if not source_quote or not source_text:
        return False

    quote_norm = _normalize_ws(source_quote)
    text_norm = _normalize_ws(source_text)

    # Exact match (case-insensitive, whitespace-normalized)
    if quote_norm in text_norm:
        return True

    # For very short quotes (< 20 chars), require exact match — skip fuzzy
    if len(quote_norm) < 20:
        return False

    # Sliding window fuzzy match for longer quotes
    window = len(quote_norm)
    if window > len(text_norm):
        return False
    for i in range(0, len(text_norm) - window + 1, max(1, window // 4)):
        snippet = text_norm[i : i + window]
        ratio = SequenceMatcher(None, quote_norm, snippet).ratio()
        if ratio >= threshold:
            return True

    return False


def validate_factoids(factoids: list[dict], source_text: str) -> list[dict]:
    """Filter factoids that fail the quote gate.

    Every factoid must have a source_quote verifiable in the source text.
    Factoids without quotes are dropped regardless of confidence — the
    quote gate is strict to prevent hallucinated facts from entering the vault.
    """
    valid = []
    for f in factoids:
        quote = f.get("source_quote", "")
        if not quote:
            continue  # No quote = not verifiable, drop it
        if validate_quote(quote, source_text):
            valid.append(f)
    return valid


# ── Deduplication & Merging ──────────────────────────────────────────────

def _factoid_key(factoid: dict) -> str:
    """Generate a stable key for a factoid (for dedup)."""
    value = _normalize_ws(factoid.get("value", ""))
    return hashlib.md5(value.encode()).hexdigest()[:12]


def _similarity(a: str, b: str) -> float:
    """Text similarity between two factoid values (0-1)."""
    return SequenceMatcher(None, _normalize_ws(a), _normalize_ws(b)).ratio()


def deduplicate_factoids(factoids: list[dict], similarity_threshold: float = 0.85) -> list[dict]:
    """Remove near-duplicate factoids, keeping the highest-confidence version.

    Two factoids are considered duplicates if their values are >= similarity_threshold similar.
    When merging, we keep the higher-confidence one and merge their source_urls.
    """
    if not factoids:
        return []

    # Sort by confidence descending so we keep the best version
    sorted_facts = sorted(factoids, key=lambda f: f.get("confidence", 0), reverse=True)
    kept: list[dict] = []

    for fact in sorted_facts:
        is_dup = False
        for existing in kept:
            sim = _similarity(fact.get("value", ""), existing.get("value", ""))
            if sim >= similarity_threshold:
                # Merge source_urls
                existing_urls = existing.get("source_urls", [existing.get("source_url", "")])
                new_url = fact.get("source_url", "")
                if new_url and new_url not in existing_urls:
                    existing_urls.append(new_url)
                    existing["source_urls"] = existing_urls
                is_dup = True
                break

        if not is_dup:
            # Ensure source_urls list exists
            url = fact.get("source_url", "")
            fact["source_urls"] = [url] if url else []
            kept.append(fact)

    return kept


# ── Main extraction pipeline ─────────────────────────────────────────────

def extract_factoids(source_text: str, source_url: str = "") -> list[dict]:
    """Extract structured factoids from source text.

    Flow: LLM extract → validate quotes → deduplicate.

    Args:
        source_text: Raw text to extract factoids from.
        source_url: URL the text came from (for attribution).

    Returns:
        List of validated, deduplicated factoid dicts.
    """
    if not source_text or len(source_text.strip()) < 50:
        return []

    call_llm = _get_llm()
    prompt = factoid_prompt(source_text, source_url)

    try:
        raw = call_llm(FACTOID_SYSTEM_PROMPT, prompt, model="fast")
    except Exception as e:
        print(f"  [factoid] LLM extraction failed: {e}")
        return []

    # Parse JSON
    try:
        cleaned = raw.strip()
        for prefix in ("```json", "```"):
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
        for suffix in ("```",):
            if cleaned.endswith(suffix):
                cleaned = cleaned[:-len(suffix)].strip()
        factoids = json.loads(cleaned)
        if not isinstance(factoids, list):
            factoids = []
    except json.JSONDecodeError:
        # Fallback: find the first JSON array with regex
        match = re.search(r"\[.*?\]", raw, re.DOTALL)
        if match:
            try:
                factoids = json.loads(match.group())
            except json.JSONDecodeError:
                return []
        else:
            return []

    # Validate quotes against source
    valid_factoids = validate_factoids(factoids, source_text)

    # Attach source URL in both forms for backward compatibility
    for f in valid_factoids:
        f.setdefault("source_url", source_url)
        f.setdefault("source_urls", [source_url] if source_url else [])
        f.setdefault("id", _factoid_key(f))

    # Deduplicate
    unique_factoids = deduplicate_factoids(valid_factoids)

    return unique_factoids


def extract_from_pages(
    pages: list[dict],
    max_pages: int = 5,
    max_llm_calls: int = 3,
) -> list[dict]:
    """Extract factoids from a list of {url, content} page dicts.

    Batches pages into limited LLM calls to avoid excessive latency.
    Limits to max_pages and max_llm_calls for performance.

    Args:
        pages: List of page dicts with {url, content}.
        max_pages: Max pages to process (sorted by content length).
        max_llm_calls: Max LLM calls to make (pages batched together).

    Returns:
        List of validated, deduplicated factoid dicts.
    """
    if not pages:
        return []

    # Sort by content length descending — process the richest pages first
    scored_pages = []
    for p in pages:
        content = (p.get("content", "") or p.get("raw_content", "")).strip()
        if len(content) >= 50:
            scored_pages.append((len(content), p))
    scored_pages.sort(key=lambda x: x[0], reverse=True)

    # Limit to top pages
    top_pages = [p for _, p in scored_pages[:max_pages]]
    if not top_pages:
        return []

    # Batch pages into max_llm_calls groups
    batch_size = max(1, len(top_pages) // max_llm_calls)
    all_factoids: list[dict] = []

    for batch_start in range(0, len(top_pages), batch_size):
        batch = top_pages[batch_start : batch_start + batch_size]
        print(f"  [factoid] processing batch {batch_start//batch_size + 1}: {len(batch)} pages")

        # Combine pages into one prompt
        combined = ""
        for p in batch:
            url = p.get("url", "")
            content = (p.get("content", "") or p.get("raw_content", ""))[:4000]
            if content:
                combined += f"\n--- Source: {url} ---\n{content}\n"

        if not combined.strip():
            continue

        factoids = extract_factoids(combined, "batch")
        all_factoids.extend(factoids)

    # Cross-page deduplication
    all_factoids = deduplicate_factoids(all_factoids)

    return all_factoids


def token_reduction_stats(raw_pages: list[dict], factoids: list[dict]) -> dict:
    """Calculate token reduction statistics."""
    raw_tokens = sum(
        len((p.get("content", "") or p.get("raw_content", "")).split()) * 1.3
        for p in raw_pages
    )
    factoid_tokens = sum(len(f.get("value", "").split()) * 1.3 for f in factoids)
    reduction_pct = (1 - factoid_tokens / max(raw_tokens, 1)) * 100
    return {
        "raw_tokens": int(raw_tokens),
        "factoid_tokens": int(factoid_tokens),
        "num_factoids": len(factoids),
        "reduction_pct": round(reduction_pct, 1),
        "types": _type_distribution(factoids),
    }


def _type_distribution(factoids: list[dict]) -> dict[str, int]:
    """Count factoids by type."""
    dist: dict[str, int] = {}
    for f in factoids:
        t = f.get("type", "unknown")
        dist[t] = dist.get(t, 0) + 1
    return dist
