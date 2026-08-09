"""Phase F tests — Factoid extraction pipeline, quote gate, dedup, integration."""
import json
import sys


def test_factoid_prompt():
    """Verify the prompt builder includes source URL and text."""
    from src.rag.factoid import factoid_prompt, FACTOID_TYPES

    prompt = factoid_prompt("Hello world. AI is advancing.", "https://example.com")
    assert "https://example.com" in prompt
    assert "Hello world" in prompt
    assert "FACTOID_TYPES" not in prompt  # should have expanded types
    for t in FACTOID_TYPES:
        assert t in prompt, f"Type {t} should appear in prompt"
    assert "source_quote" in prompt
    assert "EXACT" in prompt.upper()
    print(f"1/8 Factoid prompt OK ({len(FACTOID_TYPES)} types in prompt)")


def test_validate_quote_exact_match():
    """Verify exact quote matching works."""
    from src.rag.factoid import validate_quote

    source = "The quick brown fox jumps over the lazy dog."
    assert validate_quote("quick brown fox", source)
    assert validate_quote("lazy dog", source)
    assert not validate_quote("purple elephant", source)
    print("2/8 Exact quote matching OK")


def test_validate_quote_fuzzy():
    """Verify fuzzy quote matching with whitespace differences."""
    from src.rag.factoid import validate_quote

    source = "The   sky  is blue and   the  grass is green."
    # Normalized: "The sky is blue and the grass is green."
    assert validate_quote("sky is blue", source)  # exact match after normalization
    assert validate_quote("the grass is green", source)
    print("3/8 Fuzzy quote matching OK")


def test_validate_factoids_filters():
    """Verify factoids with bad quotes are filtered out."""
    from src.rag.factoid import validate_factoids

    source = "Python was created by Guido van Rossum in 1991."
    factoids = [
        {"type": "entity", "value": "Python was created by Guido van Rossum",
         "source_quote": "created by Guido van Rossum", "confidence": 0.95},
        {"type": "claim", "value": "Python is the best language",
         "source_quote": "Python is the best language", "confidence": 0.8},  # NOT in source
        {"type": "statistic", "value": "Python created in 1991",
         "source_quote": "1991", "confidence": 0.9},
    ]
    valid = validate_factoids(factoids, source)
    assert len(valid) == 2, f"Expected 2 valid, got {len(valid)}"
    values = [f["value"] for f in valid]
    assert "Python was created by Guido van Rossum" in values
    assert "Python created in 1991" in values
    assert "Python is the best language" not in values  # fabricated quote
    print(f"4/8 Factoid validation filters OK ({len(valid)}/3 kept)")


def test_deduplicate_factoids():
    """Verify near-duplicate factoids are deduped."""
    from src.rag.factoid import deduplicate_factoids

    factoids = [
        {"value": "Einstein developed relativity theory in 1905",
         "confidence": 0.92, "source_url": "url1", "type": "event", "source_quote": "x"},
        {"value": "Einstein developed the theory of relativity in 1905",
         "confidence": 0.85, "source_url": "url2", "type": "event", "source_quote": "x"},
        {"value": "Quantum mechanics emerged in the 1920s",
         "confidence": 0.88, "source_url": "url3", "type": "event", "source_quote": "x"},
    ]
    result = deduplicate_factoids(factoids, similarity_threshold=0.75)
    assert len(result) == 2, f"Expected 2 after dedup, got {len(result)}"
    # Higher confidence version kept, with merged source_urls
    kept = [f for f in result if "Einstein" in f["value"]]
    assert len(kept) == 1
    assert kept[0]["confidence"] == 0.92
    assert len(kept[0].get("source_urls", [])) == 2  # merged both URLs
    print("5/8 Dedup OK")


def test_deduplicate_keeps_best():
    """Verify higher-confidence version survives with merged urls."""
    from src.rag.factoid import deduplicate_factoids

    factoids = [
        {"value": "AI will transform healthcare",
         "confidence": 0.65, "source_url": "low", "type": "claim", "source_quote": "q"},
        {"value": "AI will transform healthcare",
         "confidence": 0.95, "source_url": "high", "type": "claim", "source_quote": "q"},
    ]
    result = deduplicate_factoids(factoids)
    assert len(result) == 1
    assert result[0]["confidence"] == 0.95
    print("6/8 Keeps best confidence OK")


def test_token_reduction_stats():
    """Verify token reduction calculation."""
    from src.rag.factoid import token_reduction_stats

    pages = [
        {"content": "The quick brown fox " * 50, "url": "u1"},  # ~200 words → ~260 tokens
        {"content": "jumps over the lazy dog " * 50, "url": "u2"},  # ~250 words → ~325 tokens
    ]
    factoids = [
        {"value": "Foxes are quick and brown."},   # 5 words → ~6.5 tokens
        {"value": "The dog is lazy."},              # 5 words → ~6.5 tokens
    ]
    stats = token_reduction_stats(pages, factoids)
    assert stats["num_factoids"] == 2
    assert stats["raw_tokens"] > 500, f"Raw tokens too low: {stats['raw_tokens']}"
    assert stats["factoid_tokens"] < 30, f"Factoid tokens too high: {stats['factoid_tokens']}"
    assert stats["reduction_pct"] > 90, f"Expected >90% reduction, got {stats['reduction_pct']}%"
    print(f"7/8 Token stats OK ({stats['reduction_pct']}% reduction)")


def test_extract_factoids_empty():
    """Verify empty/short text returns no factoids."""
    from src.rag.factoid import extract_factoids

    assert extract_factoids("") == []
    assert extract_factoids("   ") == []
    assert extract_factoids("Hi.") == []  # too short
    print("8/8 Empty text returns [] OK")


if __name__ == "__main__":
    tests = [
        test_factoid_prompt,
        test_validate_quote_exact_match,
        test_validate_quote_fuzzy,
        test_validate_factoids_filters,
        test_deduplicate_factoids,
        test_deduplicate_keeps_best,
        test_token_reduction_stats,
        test_extract_factoids_empty,
    ]
    passed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  FAIL: {e}")
    print(f"\n{passed}/{len(tests)} tests passed")
    sys.exit(0 if passed == len(tests) else 1)
