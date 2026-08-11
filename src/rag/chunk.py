"""
Token-based text chunking for RAG.

Chunks text into ~500-800 token segments with ~10% overlap.
Uses a simple word-count heuristic (1 token ≈ 0.75 words for English text)
since we want to avoid heavy tokenizer dependencies.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Optional


def _doc_scope(base_meta: dict) -> str:
    """Short stable id-scope derived from base metadata (url when present).

    Chunk ids are per-document counters (chunk_0, chunk_1, …). Two documents
    upserted together would otherwise collide on chunk_0 — INSERT OR REPLACE
    would silently drop one. Scoping ids by the source URL keeps them unique
    across documents while staying stable for idempotent re-ingest.
    """
    url = str(base_meta.get("url") or "")
    if not url:
        return ""
    return hashlib.sha1(url.encode()).hexdigest()[:8]


@dataclass
class Chunk:
    """A chunk of text with metadata for RAG retrieval."""
    id: str                       # unique chunk id
    text: str                     # the chunk text
    embedding: Optional[list[float]] = None  # vector embedding (populated by Embedder)
    metadata: dict = field(default_factory=dict)  # run_id, url, title, source_type, chunk_index, parent_id, parent_text


def _split_parent_sections(text: str) -> list[str]:
    """Split text into parent sections on blank-line / markdown-header boundaries.

    A parent is a logical block (paragraph cluster or a heading-led section).
    A bare heading line attaches to the block that follows it, so
    "## Section\n\n<body>" is ONE parent. Children retrieve small, the parent
    is fed large — the parent-child pattern.
    """
    import re
    if "\n\n" not in text and not re.search(r"\n#{1,6}\s+", text):
        return [text.strip()] if text.strip() else []

    parts = re.split(r"\n\n+", text)
    parents: list[str] = []
    buffer = ""
    for p in parts:
        p = p.strip()
        if not p:
            continue
        is_heading_only = (
            re.match(r"^#{1,6}\s+.+$", p)
            and len(p.splitlines()) <= 2
            and not re.search(r"\n\S{60,}", p)
        )
        if is_heading_only and buffer:
            parents.append(buffer)
            buffer = p
        elif buffer:
            buffer += "\n\n" + p
        else:
            buffer = p
    if buffer:
        parents.append(buffer)
    return parents


def chunk_children_with_parents(
    text: str,
    chunk_size: int = 600,
    chunk_overlap: int = 60,
    metadata: Optional[dict] = None,
) -> list[Chunk]:
    """Parent-child chunking: retrieve small, feed large.

    Splits the document into parent sections (structure-aware), chunks each
    parent into small children, and tags every child with parent_id + a
    truncated parent_text. Downstream retrieval can use the child for scoring
    and the parent for context — the standard production-RAG pattern.

    Returns:
        List of child Chunks, each with metadata.parent_id / parent_text.
    """
    if not text or not text.strip():
        return []
    base_meta = dict(metadata or {})
    scope = _doc_scope(base_meta)
    parents = _split_parent_sections(text)
    out: list[Chunk] = []
    child_index = 0
    for pi, parent in enumerate(parents):
        # Parent ids must also be doc-scoped (P0 in doc A ≠ P0 in doc B)
        parent_id = f"P{scope}{pi}" if scope else f"P{pi}"
        parent_text = parent[:6000]
        kids = chunk_text(parent, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        if not kids:
            # Parent smaller than one chunk — emit it directly as its own child
            kids = [Chunk(
                id=f"child_{scope}_{child_index}" if scope else f"child_{child_index}",
                text=parent,
                metadata={**base_meta, "chunk_index": child_index},
            )]
        for k in kids:
            k.id = f"child_{scope}_{child_index}" if scope else f"child_{child_index}"
            k.metadata = {**base_meta, "chunk_index": child_index,
                          "parent_id": parent_id, "parent_text": parent_text}
            child_index += 1
            out.append(k)
    return out


def _estimate_tokens(text: str) -> int:
    """Estimate token count from text length. ~1.3 tokens per word for English
    (average English word ~4 chars, typical token ~3 chars)."""
    words = text.split()
    return max(1, int(len(words) * 1.3))


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences on period/exclamation/question + space."""
    import re
    # Split on sentence boundaries while preserving the delimiter
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def chunk_text(
    text: str,
    chunk_size: int = 600,
    chunk_overlap: int = 60,
    metadata: Optional[dict] = None,
) -> list[Chunk]:
    """Split text into overlapping chunks of ~chunk_size tokens.

    Args:
        text: The text to chunk.
        chunk_size: Target chunk size in estimated tokens (default 600).
        chunk_overlap: Overlap between chunks in estimated tokens (default 60 ~= 10%).
        metadata: Base metadata to attach to all chunks (url, title, etc.).

    Returns:
        List of Chunk objects (without embeddings — use Embedder to populate).
    """
    if not text.strip():
        return []

    sentences = _split_sentences(text)
    if not sentences:
        return []

    chunks: list[Chunk] = []
    current_chunk: list[str] = []
    current_tokens = 0
    base_meta = dict(metadata or {})
    scope = _doc_scope(base_meta)

    def _kid_id(idx: int) -> str:
        return f"chunk_{scope}_{idx}" if scope else f"chunk_{idx}"

    for sent in sentences:
        sent_tokens = _estimate_tokens(sent)

        if current_tokens + sent_tokens > chunk_size and current_chunk:
            # Finalize current chunk
            chunk_text_val = " ".join(current_chunk)
            chunks.append(Chunk(
                id=_kid_id(len(chunks)),
                text=chunk_text_val,
                metadata={**base_meta, "chunk_index": len(chunks)},
            ))

            # Start new chunk with overlap: keep last ~overlap tokens worth
            overlap_text = " ".join(current_chunk)
            overlap_words = overlap_text.split()
            # Calculate how many words to keep for overlap
            overlap_word_count = max(1, int(chunk_overlap / 0.75))
            if len(overlap_words) > overlap_word_count:
                current_chunk = overlap_words[-overlap_word_count:]
            else:
                current_chunk = []
            current_tokens = _estimate_tokens(" ".join(current_chunk))

        current_chunk.append(sent)
        current_tokens += sent_tokens

    # Final chunk
    if current_chunk:
        chunk_text_val = " ".join(current_chunk)
        chunks.append(Chunk(
            id=_kid_id(len(chunks)),
            text=chunk_text_val,
            metadata={**base_meta, "chunk_index": len(chunks)},
        ))

    return chunks
