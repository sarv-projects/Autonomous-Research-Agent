"""
Token-based text chunking for RAG.

Chunks text into ~500-800 token segments with ~10% overlap.
Uses a simple word-count heuristic (1 token ≈ 0.75 words for English text)
since we want to avoid heavy tokenizer dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Chunk:
    """A chunk of text with metadata for RAG retrieval."""
    id: str                       # unique chunk id
    text: str                     # the chunk text
    embedding: Optional[list[float]] = None  # vector embedding (populated by Embedder)
    metadata: dict = field(default_factory=dict)  # run_id, url, title, source_type, chunk_index


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

    for sent in sentences:
        sent_tokens = _estimate_tokens(sent)

        if current_tokens + sent_tokens > chunk_size and current_chunk:
            # Finalize current chunk
            chunk_text_val = " ".join(current_chunk)
            chunks.append(Chunk(
                id=f"chunk_{len(chunks)}",
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
            id=f"chunk_{len(chunks)}",
            text=chunk_text_val,
            metadata={**base_meta, "chunk_index": len(chunks)},
        ))

    return chunks
