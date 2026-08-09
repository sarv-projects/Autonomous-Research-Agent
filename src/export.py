import os

OUTPUT_DIR = "reports"


def save_markdown(report: str, filename: str) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, f"{filename}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(report)
    return os.path.abspath(path)


def save_html(report: str, filename: str, title: str = "Research Report") -> str:
    """Save report as HTML with MathJax rendering."""
    from src.render.math import markdown_to_html
    html_content = markdown_to_html(report, title=title)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, f"{filename}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html_content)
    return os.path.abspath(path)
