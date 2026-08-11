"""
Cross-encoder reranker — optional retrieval precision boost.

Ranks hybrid-retrieved candidates with a cross-encoder (query + document
jointly attended), which typically adds +15–30% top-k precision over
bi-encoder/RRF ordering alone.

Design:
  - Lazy singleton: the model is only loaded on first use, so the research
    engine works unchanged when `sentence-transformers` is not installed.
  - Env controls:
      RERANK_ENABLED=1|0        (default 1 — auto-disabled if lib missing)
      RERANK_MODEL=...          (default BAAI/bge-reranker-v2-m3)
      RERANK_MAX_CANDIDATES=N   (default 50 — candidates fed to the reranker)
      RERANK_MAX_CHARS=N        (default 2000 — per-doc truncation for speed)
  - Any failure (import, load, predict) falls back to the original ordering.
"""

from __future__ import annotations

import os
import threading

# ── Env config (read once at import; malformed values never break imports) ──
_ENABLED = os.getenv("RERANK_ENABLED", "1").lower() not in ("0", "false", "no")
_MODEL_NAME = os.getenv("RERANK_MODEL", "BAAI/bge-reranker-v2-m3")


def _env_int(name: str, default: int) -> int:
    """Parse an int env var; any malformed value falls back to the default so a
    bad .env line can never break the RAG import chain."""
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


_MAX_CANDIDATES = _env_int("RERANK_MAX_CANDIDATES", 50)
_MAX_CHARS = _env_int("RERANK_MAX_CHARS", 2000)

_model = None
_model_lock = threading.Lock()
_attempted = False
_availability = None  # tri-state: None=unknown, True/False=cached


def rerank_available() -> bool:
    """True if the reranker can be used (enabled + library installed).

    Result is cached after the first check — this is called from every
    hybrid_retrieve (up to 6 parallel section writers), so re-importing the
    library on each call would be wasteful.
    """
    global _availability
    if not _ENABLED:
        _availability = False
        return False
    if _availability is not None:
        return _availability
    try:
        import sentence_transformers  # noqa: F401
        _availability = True
    except Exception:
        _availability = False
    return _availability


def _get_model():
    """Load the cross-encoder once (thread-safe). None on any failure."""
    global _model, _attempted
    if _model is not None or _attempted:
        return _model
    with _model_lock:
        if _model is not None or _attempted:
            return _model
        _attempted = True
        try:
            from sentence_transformers import CrossEncoder
            _model = CrossEncoder(_MODEL_NAME, max_length=512)
        except Exception as e:
            print(f"  [rerank] model load failed ({e}) — using hybrid order")
            _model = None
    return _model
def _doc_texts(cands: list[dict]) -> list[str]:
    """Extract the searchable text of each candidate for cross-encoder pairs."""
    out = []
    for r in cands:
        doc = (
            r.get("text")
            or r.get("content")
            or r.get("title")
            or r.get("snippet")
            or ""
        )
        out.append(str(doc)[:_MAX_CHARS])
    return out


def rerank_results(
    query: str,
    results: list[dict],
    k: int = 10,
) -> list[dict]:
    """Rerank retrieved chunks with a cross-encoder and return top-k.

    results: list of dicts with 'text' (or 'title'/'content') keys, as produced
             by hybrid_retrieve. The dicts are mutated with a 'rerank_score'
             key and re-sorted; original 'score'/'rrf_score' are preserved.
    Falls back to the input ordering (sliced to k) on any failure.
    """
    if not results:
        return results
    if not rerank_available():
        return results[:k]

    model = _get_model()
    if model is None:
        return results[:k]

    candidates = results[:_MAX_CANDIDATES]

    # Split out docs with no usable text — predicting on empty strings yields
    # meaningless scores, so they stay unranked (appended after scored ones,
    # preserving their original relative order).
    scored_cands: list[dict] = []
    empty_cands: list[dict] = []
    for r in candidates:
        doc = (
            r.get("text")
            or r.get("content")
            or r.get("title")
            or r.get("snippet")
            or ""
        )
        if doc.strip():
            scored_cands.append(r)
        else:
            empty_cands.append(r)

    if not scored_cands:
        return results[:k]

    pairs = [(query, str(doc)[:_MAX_CHARS]) for doc in _doc_texts(scored_cands)]
    try:
        scores = model.predict(pairs)
    except Exception as e:
        print(f"  [rerank] predict failed ({e}) — using hybrid order")
        return results[:k]

    for r, s in zip(scored_cands, scores):
        r["rerank_score"] = float(s)

    ranked = sorted(scored_cands, key=lambda r: r.get("rerank_score", 0.0), reverse=True)
    return (ranked + empty_cands)[:k]
