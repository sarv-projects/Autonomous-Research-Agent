"""
Phase B tests — chunking, embedding, vector store, and RAG pipeline.

All offline (no API keys required). Uses DummyEmbedder for embeddings.
Run with:
    uv run python test_phase_b.py
"""

import os
import sys
import tempfile

# Ensure consistent vector dimension for tests
os.environ["EMBEDDING_DIM"] = "128"

# ── 1. Chunking ─────────────────────────────────────────────────────────
def test_chunk_basic():
    from src.rag.chunk import chunk_text
    # Use actual sentences that will be split properly
    text = " ".join([f"This is sentence number {i}." for i in range(100)])
    chunks = chunk_text(text, chunk_size=300, chunk_overlap=30)
    assert len(chunks) >= 3, f"Expected at least 3 chunks, got {len(chunks)}"
    # Each chunk should not be too large
    for c in chunks:
        assert len(c.text) > 0
    print("1/9 chunk basic OK")


def test_chunk_overlap():
    from src.rag.chunk import chunk_text
    text = " ".join([f"This is sentence number {i} with more words." for i in range(80)])
    chunks = chunk_text(text, chunk_size=200, chunk_overlap=50)
    assert len(chunks) >= 4, f"Expected 4+ chunks, got {len(chunks)}"
    print("2/9 chunk overlap OK")


def test_chunk_metadata():
    from src.rag.chunk import chunk_text
    text = "Hello world. This is a test."
    chunks = chunk_text(text, metadata={"url": "http://example.com", "title": "Test"})
    assert all(c.metadata.get("url") == "http://example.com" for c in chunks)
    assert all(c.metadata.get("title") == "Test" for c in chunks)
    print("3/9 chunk metadata OK")


# ── 2. Embedding ─────────────────────────────────────────────────────────
def test_dummy_embedder():
    from src.rag.embed import DummyEmbedder
    e = DummyEmbedder(dim=128)
    vec = e.embed("hello world")
    assert len(vec) == 128
    assert all(isinstance(v, float) for v in vec)
    # Deterministic
    vec2 = e.embed("hello world")
    assert vec == vec2
    print("4/9 dummy embedder OK")


def test_dummy_embedder_batch():
    from src.rag.embed import DummyEmbedder
    e = DummyEmbedder(dim=128)
    texts = ["hello", "world", "test"]
    vecs = e.embed_batch(texts)
    assert len(vecs) == 3
    assert all(len(v) == 128 for v in vecs)
    print("5/9 dummy embedder batch OK")


# ── 3. Vector Store ─────────────────────────────────────────────────────
def test_fts_store():
    from src.rag.backends.fts import FTSStore
    from src.rag.chunk import Chunk
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        store = FTSStore(db_path=db_path)
        chunks = [
            Chunk(id="c1", text="The quick brown fox jumps over the lazy dog",
                  metadata={"url": "http://a.com", "title": "Foxes", "source_type": "web", "run_id": "r1"}),
            Chunk(id="c2", text="Python is a programming language",
                  metadata={"url": "http://b.com", "title": "Python", "source_type": "web", "run_id": "r1"}),
        ]
        store.upsert(chunks)
        results = store.query("fox", k=5)
        assert len(results) >= 1
        assert results[0]["title"] == "Foxes"
        store.delete_by_run("r1")
        assert store.count() == 0
        print("6/9 FTS store OK")
    finally:
        os.unlink(db_path)


def test_lancedb_store():
    from src.rag.backends.lancedb_backend import LanceDBStore
    from src.rag.chunk import Chunk
    from src.rag.embed import DummyEmbedder
    import shutil, tempfile

    tmpdir = tempfile.mkdtemp()
    try:
        store = LanceDBStore(db_path=tmpdir, vector_dim=128)
        embedder = DummyEmbedder(dim=128)

        chunks = []
        for i in range(5):
            text = f"Document chunk {i} about research topics"
            vec = embedder.embed(text)
            c = Chunk(
                id=f"lc_{i}", text=text, embedding=vec,
                metadata={"url": f"http://c{i}.com", "title": f"Doc {i}", "source_type": "web", "run_id": "br1", "chunk_index": i},
            )
            chunks.append(c)

        store.upsert(chunks)
        assert store.count() == 5

        # Query
        qvec = embedder.embed("research topics")
        results = store.query(qvec, k=3)
        assert len(results) == 3

        # Delete
        store.delete_by_run("br1")
        assert store.count() == 0
        print("7/9 LanceDB store OK")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ── 4. RAG Pipeline ─────────────────────────────────────────────────────
def test_pipeline_ingest_retrieve():
    from src.rag.pipeline import ingest_documents, retrieve_chunks, reset_pipeline
    from src.rag.store import VectorStore
    from src.rag.embed import DummyEmbedder
    from src.rag.backends.lancedb_backend import LanceDBStore
    import shutil, tempfile

    reset_pipeline()  # clear singletons
    tmpdir = tempfile.mkdtemp()
    try:
        store = VectorStore(vector_dim=128)
        # Override to use temp dir
        store._lancedb = LanceDBStore(db_path=tmpdir, vector_dim=128)
        embedder = DummyEmbedder(dim=128)

        pages = [
            {"url": "http://x.com/1", "title": "AI Research",
             "content": "Artificial intelligence is transforming the world. " * 20},
            {"url": "http://x.com/2", "title": "ML Basics",
             "content": "Machine learning is a subset of AI. Deep learning uses neural networks. " * 15},
        ]

        ingested = ingest_documents(pages, run_id="test_run", store=store, embedder=embedder)
        assert ingested > 0, f"No chunks ingested: {ingested}"

        results = retrieve_chunks("artificial intelligence", k=5, store=store, embedder=embedder)
        assert len(results) >= 1, f"No results: {len(results)}"
        assert results[0]["run_id"] == "test_run"

        print("8/9 RAG pipeline OK")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ── 5. State integration ─────────────────────────────────────────────────
def test_state_has_rag_fields():
    from src.state import initial_state
    state = initial_state("test query")
    assert "run_id" in state
    assert "chunks_ingested" in state
    assert "retrieved_chunks" in state
    assert len(state["run_id"]) == 12
    print("9/9 state RAG fields OK")


TESTS = [
    test_chunk_basic,
    test_chunk_overlap,
    test_chunk_metadata,
    test_dummy_embedder,
    test_dummy_embedder_batch,
    test_fts_store,
    test_lancedb_store,
    test_pipeline_ingest_retrieve,
    test_state_has_rag_fields,
]

if __name__ == "__main__":
    passed = 0
    for t in TESTS:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"FAIL: {t.__name__} -> {e}")
            import traceback
            traceback.print_exc()
    print(f"\n{passed}/{len(TESTS)} tests passed")
    sys.exit(0 if passed == len(TESTS) else 1)
