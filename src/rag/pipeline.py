"""
RAG pipeline — end-to-end ingest and retrieve flows.

Ingest:
  documents → chunk → embed → upsert(VectorStore)

Retrieve:
  query → embed → hybrid_query(VectorStore) → scored chunks

Module-level singletons for store and embedder to avoid creating new
connections on every call during the research loop.
"""

from __future__ import annotations

import hashlib
import uuid
from typing import Optional

from .chunk import chunk_text, Chunk
from .embed import get_embedder, Embedder
from .store import VectorStore, get_vector_store

# Module-level singletons — reused across research iterations
_store: Optional[VectorStore] = None
_embedder: Optional[Embedder] = None


def _get_or_create_store() -> VectorStore:
    global _store
    if _store is None:
        _store = get_vector_store()
    return _store


def _get_or_create_embedder() -> Embedder:
    global _embedder
    if _embedder is None:
        _embedder = get_embedder()
    return _embedder


def reset_pipeline() -> None:
    """Reset singletons (useful for testing)."""
    global _store, _embedder
    _store = None
    _embedder = None


def ingest_documents(
    pages: list[dict],
    run_id: str = "",
    store: Optional[VectorStore] = None,
    embedder: Optional[Embedder] = None,
) -> int:
    """Ingest extracted pages into the vector store.

    Flow: chunk → embed → upsert. Uses module-level singletons by default
    for efficient reuse across research iterations.

    Args:
        pages: List of dicts with {url, content, title?}.
        run_id: Unique identifier for this research run.
        store: VectorStore instance (uses singleton if None).
        embedder: Embedder instance (uses singleton if None).

    Returns:
        Number of chunks ingested.
    """
    if store is None:
        store = _get_or_create_store()
    if embedder is None:
        embedder = _get_or_create_embedder()

    if not pages:
        return 0

    all_chunks: list[Chunk] = []

    for page in pages:
        url = page.get("url", "")
        title = page.get("title", "")
        content = page.get("content", "") or page.get("raw_content", "")

        if not content:
            continue

        # Chunk
        chunks = chunk_text(
            content,
            chunk_size=600,
            chunk_overlap=60,
            metadata={
                "url": url,
                "title": title[:200] if title else "",
                "source_type": "web",
                "run_id": run_id,
            },
        )

        # Assign unique IDs: url + run_id + chunk_index avoids collisions across runs
        for c in chunks:
            c.id = hashlib.md5(
                f"{url}:{run_id}:{c.metadata.get('chunk_index', 0)}".encode()
            ).hexdigest()[:16]

        all_chunks.extend(chunks)

    if not all_chunks:
        return 0

    # Embed in batches (with short timeout — embeddings are best-effort)
    texts = [c.text for c in all_chunks]
    try:
        embeddings = embedder.embed_batch(texts)
        for c, vec in zip(all_chunks, embeddings):
            c.embedding = vec
    except KeyboardInterrupt:
        raise
    except Exception as e:
        # Embeddings are best-effort — FTS5 keyword search handles fallback
        err_msg = str(e)[:80]
        print(f"  [rag] embedding skipped ({err_msg}) — using keyword fallback")

    # Upsert
    store.upsert(all_chunks)

    return len(all_chunks)


def retrieve_chunks(
    query: str,
    k: int = 10,
    store: Optional[VectorStore] = None,
    embedder: Optional[Embedder] = None,
) -> list[dict]:
    """Retrieve relevant chunks for a query. Uses module-level singletons.

    Vector similarity when embeddings available, falls back to FTS5 keyword.
    """
    if store is None:
        store = _get_or_create_store()
    if embedder is None:
        embedder = _get_or_create_embedder()

    embedding = None
    try:
        embedding = embedder.embed(query)
    except RuntimeError:
        pass  # Will use FTS fallback

    results = store.query(text=query, embedding=embedding, k=k)

    return results
