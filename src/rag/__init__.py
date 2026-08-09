"""RAG (Retrieval-Augmented Generation) module.

Chunking → Embedding → VectorStore → Pipeline (ingest + retrieve).

Backends: LanceDB (default), SQLite FTS5 (fallback), Qdrant (future).
"""

from .chunk import chunk_text, Chunk
from .embed import Embedder, OpenAIEmbedder
from .store import VectorStore, get_vector_store
from .pipeline import ingest_documents, retrieve_chunks, reset_pipeline
from .factoid import (
    extract_factoids,
    extract_from_pages,
    validate_quote,
    validate_factoids,
    deduplicate_factoids,
    token_reduction_stats,
)
from .guard import (
    assess_source,
    domain_reputation_score,
    freshness_score,
    filter_results,
    retry_pyramid_filter,
    SourceAssessment,
)
from .hybrid import hybrid_retrieve, search_vault
from .vault import Vault
from .chat_memory import ChatMemory, get_chat_memory, reset_chat_memory

__all__ = [
    "chunk_text",
    "Chunk",
    "Embedder",
    "OpenAIEmbedder",
    "VectorStore",
    "get_vector_store",
    "ingest_documents",
    "retrieve_chunks",
    "reset_pipeline",
    "extract_factoids",
    "extract_from_pages",
    "validate_quote",
    "validate_factoids",
    "deduplicate_factoids",
    "token_reduction_stats",
    "assess_source",
    "domain_reputation_score",
    "freshness_score",
    "filter_results",
    "retry_pyramid_filter",
    "SourceAssessment",
    "hybrid_retrieve",
    "search_vault",
    "Vault",
    "ChatMemory",
    "get_chat_memory",
    "reset_chat_memory",
]
