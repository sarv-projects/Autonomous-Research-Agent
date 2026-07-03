import os

OUTPUT_DIR = "reports"


def save_markdown(report: str, filename: str) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, f"{filename}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(report)
    return os.path.abspath(path)
