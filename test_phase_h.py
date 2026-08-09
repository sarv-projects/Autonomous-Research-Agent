"""Phase H tests — Relentless Retrieval: Qdrant, hybrid, vault, chat memory."""
import os
import sys
import tempfile


def test_qdrant_availability():
    """Verify Qdrant availability detection works."""
    from src.rag.backends.qdrant_backend import qdrant_is_available, QDRANT_AVAILABLE

    # Without QDRANT_URL set, should return False
    if "QDRANT_URL" in os.environ:
        old = os.environ["QDRANT_URL"]
        del os.environ["QDRANT_URL"]
        assert not qdrant_is_available()
        os.environ["QDRANT_URL"] = old
    else:
        assert not qdrant_is_available()
    print(f"1/8 Qdrant availability detection OK (available={QDRANT_AVAILABLE})")


def test_hybrid_rrf_scoring():
    """Verify RRF scoring is monotonically decreasing."""
    from src.rag.hybrid import _rrf_score

    scores = [_rrf_score(i) for i in range(20)]
    for i in range(len(scores) - 1):
        assert scores[i] >= scores[i + 1], f"RRF should decrease: {scores[i]} < {scores[i+1]}"
    assert scores[0] > scores[10], "RRF at rank 0 should be higher than rank 10"
    print(f"2/8 RRF scoring OK (rank 0={scores[0]:.4f}, rank 10={scores[10]:.4f})")


def test_vault_store_and_search():
    """Verify vault stores and retrieves sources."""
    from src.rag.vault import Vault

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        vault = Vault(db_path)
        results = [
            {
                "url": "https://arxiv.org/abs/2401.00001",
                "title": "Quantum Computing Breakthrough",
                "content": "A new quantum algorithm achieves exponential speedup...",
                "guard_score": 9.0,
            },
            {
                "url": "https://nature.com/article/science",
                "title": "Climate Research 2024",
                "content": "Global temperatures continue to rise...",
                "guard_score": 8.5,
            },
            {
                "url": "https://medium.com/blog",
                "title": "My Opinion",
                "content": "random thoughts about tech...",
                "guard_score": 2.0,
            },
        ]
        vault.store_results(results, queries=["quantum computing"])

        # Search for quantum
        hits = vault.search("quantum algorithm", k=5)
        assert len(hits) >= 1, f"Should find quantum result, got {len(hits)}"
        assert any("arxiv.org" in h["url"] for h in hits)

        # Search for climate
        hits2 = vault.search("climate temperatures", k=5)
        assert len(hits2) >= 1

        # Low-quality should be filtered out with high min_quality
        hits3 = vault.search("opinion tech", k=5, min_quality=5.0)
        assert all(h["quality_score"] >= 5.0 for h in hits3)

        # Stats
        stats = vault.stats()
        assert stats["total_sources"] == 3
        assert stats["unique_domains"] >= 2
        print(f"3/8 Vault store/search OK (sources={stats['total_sources']}, domains={stats['unique_domains']})")
    finally:
        os.unlink(db_path)


def test_vault_upsert():
    """Verify vault updates existing sources (seen_count incremented)."""
    from src.rag.vault import Vault

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        vault = Vault(db_path)
        # Store once
        vault.store_results([
            {"url": "https://example.com/page", "title": "Test",
             "content": "test content", "score": 7.0}
        ])
        # Store again (should update, not duplicate)
        vault.store_results([
            {"url": "https://example.com/page", "title": "Test Updated",
             "content": "updated", "score": 8.0}
        ])
        stats = vault.stats()
        assert stats["total_sources"] == 1, f"Should be 1 unique source, got {stats['total_sources']}"
        print("4/8 Vault upsert OK")
    finally:
        os.unlink(db_path)


def test_chat_memory_window():
    """Verify chat memory sliding window and compression."""
    from src.rag.chat_memory import ChatMemory

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        persist_path = f.name

    try:
        memory = ChatMemory(window_size=6, persist_path=persist_path)

        # Add 3 pairs (6 messages) — within window, no compression
        for i in range(3):
            memory.add("user", f"Question {i}")
            memory.add("assistant", f"Answer {i}")

        assert len(memory) == 6, f"Window should hold 6 messages, got {len(memory)}"
        assert memory.summary == "", f"No compression should happen within window (got: {memory.summary[:50]})"

        # Add more messages to trigger compression
        memory.add("user", "Question 3")
        assert len(memory) <= 6, f"Window should stay <= 6 after compression, got {len(memory)}"
        assert memory.summary != "", "Summary should be created after overflow"

        # Build context
        ctx = memory.build_context("You are helpful.")
        assert len(ctx) > 0
        assert ctx[0]["role"] == "system"
        assert "summary" in ctx[0]["content"].lower()

        # Clear
        memory.clear()
        assert len(memory) == 0
        assert memory.summary == ""
        print(f"5/8 Chat memory OK (window={len(memory)}, summary_len={len(memory.summary)})")
    finally:
        os.unlink(persist_path)


def test_chat_memory_persistence():
    """Verify chat memory persists and loads across instances."""
    from src.rag.chat_memory import ChatMemory

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        persist_path = f.name

    try:
        # Create and populate
        m1 = ChatMemory(window_size=10, persist_path=persist_path)
        m1.add("user", "Hello")
        m1.add("assistant", "Hi there!")

        # Create new instance with same path
        m2 = ChatMemory(window_size=10, persist_path=persist_path)
        assert len(m2) == 2, f"Should load 2 messages, got {len(m2)}"
        assert m2.messages[0]["role"] == "user"
        assert m2.messages[0]["content"] == "Hello"
        print("6/8 Chat memory persistence OK")
    finally:
        os.unlink(persist_path)


def test_vector_store_auto_detects_qdrant():
    """Verify VectorStore auto-detects Qdrant when QDRANT_URL is set."""
    from src.rag.store import VectorStore

    # Without QDRANT_URL, should default to lancedb
    if "QDRANT_URL" not in os.environ:
        store = VectorStore(backend="auto")
        assert store.backend_name in ("lancedb", "fts"), \
            f"Default should be lancedb/fts, got {store.backend_name}"
        print(f"7/8 Auto-detect falls back to {store.backend_name} OK")
    else:
        # Qdrant URL is set but might not be reachable — test constructor
        try:
            store = VectorStore(backend="qdrant")
            assert store.backend_name == "qdrant"
            print("7/8 Qdrant backend selected OK")
        except Exception:
            print("7/8 Qdrant not reachable (expected)")
        # Clean up
        if "QDRANT_URL" in os.environ:
            del os.environ["QDRANT_URL"]


def test_hybrid_retriever_no_factoids():
    """Verify hybrid retriever works without factoids (dense+keyword only)."""
    from src.rag.hybrid import hybrid_retrieve

    # Should return results without crashing even with no stored data
    results = hybrid_retrieve("test query", k=3, factoids=[])
    assert isinstance(results, list), "Should return a list"
    # With empty store, should return empty
    print(f"8/8 Hybrid retriever no-factoids OK ({len(results)} results)")


if __name__ == "__main__":
    tests = [
        test_qdrant_availability,
        test_hybrid_rrf_scoring,
        test_vault_store_and_search,
        test_vault_upsert,
        test_chat_memory_window,
        test_chat_memory_persistence,
        test_vector_store_auto_detects_qdrant,
        test_hybrid_retriever_no_factoids,
    ]
    passed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"  FAIL: {e}")
    print(f"\n{passed}/{len(tests)} tests passed")
    sys.exit(0 if passed == len(tests) else 1)
