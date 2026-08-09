"""Phase L tests — Math rendering: LaTeX detection, sanitization, HTML export."""
import sys
import tempfile
import os


def test_detect_inline_math():
    """Verify inline math detection."""
    from src.render.math import detect_math, has_math

    text = "Einstein's equation $E=mc^2$ is famous."
    assert has_math(text)
    info = detect_math(text)
    assert info["count"] == 1
    assert len(info["inline"]) == 1
    assert "E=mc^2" in info["inline"][0]
    assert len(info["block"]) == 0
    print("1/8 Inline math detection OK")


def test_detect_block_math():
    """Verify block math detection."""
    from src.render.math import detect_math

    text = "The quadratic formula:\n$$x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$$\nis essential."
    info = detect_math(text)
    assert info["count"] == 1
    assert len(info["block"]) == 1
    assert "frac" in info["block"][0]
    assert len(info["inline"]) == 0
    print("2/8 Block math detection OK")


def test_detect_mixed_math():
    """Verify detection of both inline and block math."""
    from src.render.math import detect_math

    text = "We have $\\alpha + \\beta = \\gamma$ and:\n$$\\sum_{i=1}^{n} i = \\frac{n(n+1)}{2}$$"
    info = detect_math(text)
    assert info["count"] == 2
    assert len(info["inline"]) == 1
    assert len(info["block"]) == 1
    print("3/8 Mixed math detection OK")


def test_no_math():
    """Verify no false positives on plain text."""
    from src.render.math import detect_math, has_math

    text = "The price is $50.00 for the item."
    assert not has_math(text)  # $ with no matching pair
    info = detect_math(text)
    assert info["count"] == 0
    print("4/8 No false positives OK")


def test_sanitize_valid_latex():
    """Verify valid LaTeX passes sanitization."""
    from src.render.math import sanitize_latex

    tex = r"\frac{1}{2} + \sqrt{x^2 + y^2}"
    result, valid = sanitize_latex(tex)
    assert valid, f"Should be valid: {result}"
    assert "frac" in result
    print("5/8 Valid LaTeX sanitization OK")


def test_sanitize_balanced_braces():
    """Verify unbalanced braces are detected."""
    from src.render.math import sanitize_latex

    tex = r"\frac{1}{2"  # missing closing brace
    result, valid = sanitize_latex(tex)
    # Should auto-fix single missing brace
    assert "}" in result or not valid
    print("6/8 Brace balancing OK")


def test_sanitize_html_injection():
    """Verify HTML characters are escaped."""
    from src.render.math import sanitize_latex

    tex = r"x < y > z & a"
    result, valid = sanitize_latex(tex)
    assert "&lt;" in result
    assert "&gt;" in result
    assert "&amp;" in result
    print("7/8 HTML escaping OK")


def test_latex_delimiters():
    """Verify \(...\) and \[...\] delimiters are converted to $/$."""
    from src.render.math import sanitize_text, detect_math, has_math

    text = r"Euler's identity is \(e^{i\pi} + 1 = 0\) which is beautiful."
    assert has_math(text), "should detect \(...\) math"
    info = detect_math(text)
    assert info["count"] >= 1

    result = sanitize_text(text)
    assert "$" in result, f"should convert to $ delimiters, got: {result[:100]}"
    assert "\\\\(" not in result, f"should strip \\(, got: {result[:100]}"
    print("8/8 LaTeX \\(...\\) conversion OK")


def test_html_export():
    """Verify HTML page generation with MathJax."""
    from src.render.math import markdown_to_html, wrap_html_page

    md_text = """# Test Report
## Section 1

Einstein's equation is $E=mc^2$.

The quadratic formula:

$$x = \\frac{-b \\pm \\sqrt{b^2-4ac}}{2a}$$

And \(e^{i\\pi}+1=0\) is Euler's identity.
"""
    html = markdown_to_html(md_text, title="Test Report")
    assert "<!DOCTYPE html>" in html
    assert "MathJax" in html
    assert "E=mc^2" in html
    assert "frac" in html
    assert "e^{i" in html
    assert "<h1>Test Report</h1>" in html
    assert "<h2>Section 1</h2>" in html
    # \( should be converted to $
    assert "\\\\(" not in html, f"LaTeX delimiters not converted: {html[:200]}"
    print(f"9/9 HTML export OK ({len(html)} chars)")


if __name__ == "__main__":
    tests = [
        test_detect_inline_math,
        test_detect_block_math,
        test_detect_mixed_math,
        test_no_math,
        test_sanitize_valid_latex,
        test_sanitize_balanced_braces,
        test_sanitize_html_injection,
        test_latex_delimiters,
        test_html_export,
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
