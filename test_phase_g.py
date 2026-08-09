"""Phase G tests — Retriever Guard: domain reputation, freshness, quality, retry pyramid."""
import sys


def test_domain_reputation_high():
    """Verify high-reputation domains score well."""
    from src.rag.guard import domain_reputation_score

    assert domain_reputation_score("nature.com") >= 9.0
    assert domain_reputation_score("arxiv.org") >= 9.0
    assert domain_reputation_score("en.wikipedia.org") >= 9.0
    assert domain_reputation_score("cdc.gov") >= 7.0  # high-trust TLD
    assert domain_reputation_score("mit.edu") >= 9.0
    print("1/8 High-reputation domains OK")


def test_domain_reputation_low():
    """Verify low-reputation domains score poorly."""
    from src.rag.guard import domain_reputation_score

    assert domain_reputation_score("medium.com") <= 2.0
    assert domain_reputation_score("ezinearticles.com") <= 2.0
    assert domain_reputation_score("best-reviews-guide.net") <= 3.0  # content farm pattern
    print("2/8 Low-reputation domains OK")


def test_domain_reputation_neutral():
    """Verify unknown domains get neutral score."""
    from src.rag.guard import domain_reputation_score

    score = domain_reputation_score("some-rando-site.com")
    assert 3.5 <= score <= 5.5, f"Neutral domain should score ~4.5, got {score}"
    print("3/8 Neutral domain scoring OK")


def test_freshness_recent():
    """Verify recent content scores high on freshness."""
    from src.rag.guard import freshness_score

    import datetime
    this_year = datetime.datetime.now().year
    assert freshness_score(this_year) >= 9.5
    assert freshness_score(this_year - 1) >= 8.0
    assert freshness_score(this_year - 5) <= 1.0
    assert freshness_score(None) == 5.0  # unknown year = neutral
    print("4/8 Freshness scoring OK")


def test_assess_source_high_quality():
    """Verify assess_source correctly flags high-quality sources."""
    from src.rag.guard import assess_source

    assessment = assess_source(
        url="https://www.nature.com/articles/s41586-024-00001-0",
        title="A groundbreaking study on quantum computing",
        snippet="Published 2024-03-15. This paper demonstrates..."
    )
    assert assessment.is_high_quality, f"nature.com should be high quality, got {assessment.composite_score}"
    assert assessment.composite_score >= 6.0
    assert assessment.reputation >= 9.0
    print(f"5/8 High-quality assessment OK (composite: {assessment.composite_score:.1f})")


def test_assess_source_blocked():
    """Verify assess_source blocks known spam domains."""
    from src.rag.guard import assess_source

    assessment = assess_source(
        url="https://medium.com/@random-user/some-blog-post",
        title="My thoughts on AI",
    )
    assert assessment.is_blocked, "medium.com should be blocked"
    assert "medium.com" in assessment.block_reason.lower()
    print(f"6/8 Blocked source OK: {assessment.block_reason}")


def test_filter_results():
    """Verify filter_results drops blocked and low-score sources."""
    from src.rag.guard import filter_results

    results = [
        {"url": "https://nature.com/article", "title": "Great study", "content": "2024 research"},
        {"url": "https://medium.com/post", "title": "Blog post", "content": "opinion"},
        {"url": "https://arxiv.org/abs/2401", "title": "Preprint", "content": "2024 paper"},
        {"url": "https://ezinearticles.com/spam", "title": "SEO spam", "content": "buy now"},
        {"url": "https://example.com/page", "title": "Unknown", "content": "some content"},
    ]
    filtered, stats = filter_results(results, min_score=3.0)

    urls = [r["url"] for r in filtered]
    assert "https://nature.com/article" in urls
    assert "https://arxiv.org/abs/2401" in urls
    assert "https://medium.com/post" not in urls  # blocked
    assert "https://ezinearticles.com/spam" not in urls  # blocked
    assert stats["total"] == 5
    assert stats["blocked"] >= 2
    assert 3 <= stats["passed"] <= 4
    print(f"7/8 Filter results OK ({stats['passed']}/{stats['total']} passed, {stats['blocked']} blocked)")


def test_retry_pyramid():
    """Verify retry pyramid progressively lowers threshold."""
    from src.rag.guard import retry_pyramid_filter

    # All low-quality: pyramid should fall through to lenient tier
    results = [
        {"url": "https://medium.com/a", "title": "A", "content": "2024"},
        {"url": "https://medium.com/b", "title": "B", "content": "2024"},
        {"url": "https://example.com/c", "title": "C", "content": "2024"},
    ]
    filtered = retry_pyramid_filter(results, threshold=3)
    # Lenient tier (1.0) should pass example.com but still block medium.com
    assert len(filtered) >= 0  # at minimum, doesn't crash
    # example.com (neutral ~4.5) should pass lenient tier
    example_urls = [r["url"] for r in filtered if "example.com" in r["url"]]
    assert len(example_urls) >= 1, "Neutral domain should pass lenient tier"
    print(f"8/8 Retry pyramid OK ({len(filtered)} passed at lenient tier)")


if __name__ == "__main__":
    tests = [
        test_domain_reputation_high,
        test_domain_reputation_low,
        test_domain_reputation_neutral,
        test_freshness_recent,
        test_assess_source_high_quality,
        test_assess_source_blocked,
        test_filter_results,
        test_retry_pyramid,
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
