"""
Benchmark runner — executes each topic through the research engine and writes a
structured JSON log per topic (query, mode, timings, stats, report path).

Usage:
    uv run python benchmarks/run_benchmark.py --range 0-4 --mode standard
    uv run python benchmarks/run_benchmark.py --mode quick      # all topics

Logs:    benchmarks/logs/TXX_slug.json
Reports: benchmarks/reports/TXX_slug.md   (copy of the generated report)
"""

import argparse
import json
import os
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmarks.topics import TOPICS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
REPORT_DIR = os.path.join(BASE_DIR, "reports")
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)


def _dirs(round_no: int) -> tuple[str, str]:
    """Round-scoped log/report dirs so re-runs never erase earlier ones.

    round 0 → benchmarks/logs/  (original run)
    round N → benchmarks/logs/round{N}/  (e.g. round2 = fixed-engine re-run)
    """
    if round_no <= 0:
        return LOG_DIR, REPORT_DIR
    ldir = os.path.join(LOG_DIR, f"round{round_no}")
    rdir = os.path.join(REPORT_DIR, f"round{round_no}")
    os.makedirs(ldir, exist_ok=True)
    os.makedirs(rdir, exist_ok=True)
    return ldir, rdir


def slugify(text: str, maxlen: int = 48) -> str:
    keep = "".join(c if c.isalnum() or c in "-_" else " " for c in text)
    return "_".join(keep.split())[:maxlen].strip("_")


def run_topic(topic: dict, mode: str) -> dict:
    from src.graph import run_research

    tid = topic["id"]
    slug = slugify(topic["title"])
    log = {
        "topic_id": tid,
        "topic": topic["title"],
        "domain": topic.get("domain", ""),
        "prompt": topic["prompt"],
        "mode": mode,
        "autonomy": "L1",
        "started_at": time.time(),
        "error": None,
    }
    print(f"\n{'='*70}\n[TOPIC {tid}] {topic['title']} (mode={mode})\n{'='*70}", flush=True)
    try:
        result = run_research(topic["prompt"], mode=mode, autonomy="L1")
        log["finished_at"] = time.time()
        log["duration_s"] = round(log["finished_at"] - log["started_at"], 1)

        report = result.get("report") or ""
        log["report_chars"] = len(report)
        log["sections_count"] = len(result.get("sections") or [])
        log["findings_count"] = len(result.get("findings") or [])
        log["claims_count"] = len(result.get("claims") or [])
        log["evidence_map_sources"] = len(result.get("evidence_map") or {})
        log["evidence_graph_edges"] = len(result.get("evidence_graph") or [])
        log["iteration"] = result.get("iteration", 0)
        log["adjudicated"] = {
            "supported": sum(1 for c in (result.get("adjudicated_claims") or []) if c.get("status") == "supported"),
            "contested": len(result.get("contested_claims") or []),
            "synthetic": len(result.get("synthetic_claims") or []),
        }
        log["atomic_verified"] = result.get("atomic_verified") or []
        log["research_debt"] = (result.get("research_debt") or [])[:6]
        log["ship_gate_ok"] = not any(
            "Evidence graph" in str(i) or "no supported" in str(i).lower()
            for i in (result.get("ship_gate_issues") or [])
        ) if result.get("ship_gate_issues") is not None else None

        # Persist a copy of the report (compiler already wrote the original)
        src_path = result.get("markdown_path") or ""
        md_path = os.path.join(REPORT_DIR, f"T{tid:02d}_{slug}.md")
        if src_path and os.path.exists(src_path):
            shutil.copyfile(src_path, md_path)
        elif report:
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(report)
        log["report_copy"] = os.path.abspath(md_path)
        log["original_report"] = src_path

        # Citation / domain stats from the Sources section
        import re
        citations = sorted({int(m) for m in re.findall(r"\[(\d+)\]", report)})
        log["citation_numbers"] = citations
        urls = re.findall(r"https?://([^/\s)\]]+)", report)
        domains = {}
        for u in urls:
            d = u.split("/")[0].lower()
            domains[d] = domains.get(d, 0) + 1
        log["sources_domains"] = dict(sorted(domains.items(), key=lambda kv: -kv[1])[:25])
        log["excerpt"] = report[:2500]
        print(f"\n✅ [TOPIC {tid}] done in {log['duration_s']}s — {log['report_chars']} chars, "
              f"{log['sections_count']} sections, {len(citations)} citations", flush=True)
    except Exception as e:
        import traceback
        log["error"] = f"{type(e).__name__}: {e}"
        log["traceback"] = traceback.format_exc()[-1500:]
        log["finished_at"] = time.time()
        log["duration_s"] = round(log["finished_at"] - log["started_at"], 1)
        print(f"\n❌ [TOPIC {tid}] FAILED: {log['error']}", flush=True)

    out = os.path.join(LOG_DIR, f"T{tid:02d}_{slug}.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
    log["_log_path"] = out
    return log


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--range", default="0-14", help="topic index range, e.g. 0-4")
    ap.add_argument("--mode", default="standard", help="research mode (quick|standard|deep)")
    ap.add_argument("--round", type=int, default=0, help="round number: 0=original dir, N=logs/roundN/ (default 0)")
    args = ap.parse_args()

    global LOG_DIR, REPORT_DIR
    LOG_DIR, REPORT_DIR = _dirs(args.round)

    lo, hi = (int(x) for x in args.range.split("-"))
    selected = TOPICS[lo:hi + 1]
    print(f"Running {len(selected)} topics [{lo}..{hi}] in mode={args.mode} round={args.round} -> {LOG_DIR}", flush=True)

    ok = fail = 0
    for topic in selected:
        log = run_topic(topic, args.mode)
        if log.get("error"):
            fail += 1
        else:
            ok += 1
    print(f"\nBATCH DONE: {ok} ok, {fail} failed", flush=True)


if __name__ == "__main__":
    main()
