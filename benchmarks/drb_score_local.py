#!/usr/bin/env python3
"""
Aggregate per-task RACE judge scores into DeepResearch Bench-comparable metrics.

Faithful mirror of the official harness math:
  - research/deep_research_bench/utils/score_calculator.py  (calculate_weighted_scores)
  - research/deep_research_bench/deepresearch_bench_race.py (overall + normalized dims)

Formulas
--------
  dim_avg    = Σ(score_i × w_i) / Σ(w_i)                       # per dimension
  total      = Σ(dim_avg × dim_weight)                         # per article (target / reference)
  overall    = target_total / (target_total + reference_total) # per task (0..1)
  RACE score = mean(overall) × 100                             # leaderboard headline
  dim score  = target_dim / (target_dim + reference_dim) × 100 # per-dimension, per task

Judge output format (one file per task in --dir, named id_001.json …):
  {
    "id": 1,
    "prompt": "<task prompt>",
    "language": "en" | "zh",
    "truncated": false,
    "notes": "<optional>",
    "scores": {
      "comprehensiveness": [ {"criterion": "<verbatim criterion text>",
                              "analysis": "...",
                              "article_1_score": 8.0, "article_2_score": 7.5}, ... ],
      "insight": [...],
      "instruction_following": [...],
      "readability": [...]
    }
  }

article_1 = target (Providence report), article_2 = expert reference.

Usage
-----
  uv run python benchmarks/drb_score_local.py \
      --dir benchmarks/logs/race \
      --criteria research/deep_research_bench/data/criteria_data/criteria.jsonl \
      --out benchmarks/DRB_RACE_RESULTS.md
"""
import argparse
import glob
import json
import os
import statistics
import sys

# Harness lives inside the repo (gitignored): research/deep_research_bench
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRB_DIR = os.path.expanduser(
    os.getenv("DRB_DIR", os.path.join(BASE_DIR, "research", "deep_research_bench"))
)


def load_criteria(path):
    """id -> {"dimension_weight": {...}, "criterions": {dim: [{criterion, weight}]}}"""
    criteria = {}
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            criteria[int(row["id"])] = row
    return criteria


def criterion_weight(dim_map, text):
    """Mirror official matching: exact -> case-insensitive -> substring -> avg weight."""
    if text is None:
        return None
    text = str(text).strip()
    if text in dim_map:
        return dim_map[text]
    low = text.lower()
    for key, val in dim_map.items():
        if key.lower() == low:
            return val
    for key, val in dim_map.items():
        if low in key.lower() or key.lower() in low:
            return val
    return sum(dim_map.values()) / len(dim_map)  # official fallback


def weighted_scores(llm_scores, criteria_row):
    """Returns (target_total, reference_total, target_dims, reference_dims)."""
    dim_weights = criteria_row.get("dimension_weight", {})
    target_total = reference_total = 0.0
    target_dims, reference_dims = {}, {}
    for dim, dim_list in llm_scores.items():
        if dim not in dim_weights or not isinstance(dim_list, list):
            continue
        dim_map = {c["criterion"]: c["weight"] for c in criteria_row["criterions"].get(dim, [])}
        if not dim_map:
            continue
        t_sum = r_sum = w_sum = 0.0
        for item in dim_list:
            if not isinstance(item, dict):
                continue
            w = criterion_weight(dim_map, item.get("criterion"))
            if w is None:
                continue
            t_raw = item.get("article_1_score")
            r_raw = item.get("article_2_score")
            try:
                t = float(t_raw) if t_raw is not None else None
                r = float(r_raw) if r_raw is not None else None
            except (TypeError, ValueError):
                continue
            if t is None:
                continue
            t_sum += t * w
            r_sum += (r * w) if r is not None else 0.0
            w_sum += w
        if w_sum <= 0:
            continue
        t_avg = t_sum / w_sum
        r_avg = r_sum / w_sum if r_raw is not None else 0.0
        target_dims[dim] = t_avg
        reference_dims[dim] = r_avg
        target_total += t_avg * dim_weights[dim]
        reference_total += r_avg * dim_weights[dim]
    return target_total, reference_total, target_dims, reference_dims


def main():
    ap = argparse.ArgumentParser(description="Aggregate DRB RACE judge scores")
    ap.add_argument("--dir", default="benchmarks/logs/race",
                    help="dir with id_*.json judge outputs")
    ap.add_argument("--criteria",
                    default=os.path.join(DRB_DIR, "data", "criteria_data", "criteria.jsonl"),
                    help="official per-task criteria file")
    ap.add_argument("--out", default="benchmarks/DRB_RACE_RESULTS.md",
                    help="markdown summary output path")
    args = ap.parse_args()

    criteria = load_criteria(args.criteria)
    files = sorted(glob.glob(os.path.join(args.dir, "id_*.json")))
    if not files:
        print(f"No judge outputs found in {args.dir} (expected id_001.json ...)")
        sys.exit(1)

    tasks, missing_criteria = [], []
    for fp in files:
        with open(fp) as fh:
            row = json.load(fh)
        tid = int(row["id"])
        crit = criteria.get(tid)
        if not crit:
            missing_criteria.append(tid)
            continue
        t_total, r_total, t_dims, r_dims = weighted_scores(row["scores"], crit)
        overall = t_total / (t_total + r_total) if (t_total + r_total) > 0 else 0.0
        dims = {d: (t_dims[d] / (t_dims[d] + r_dims[d]) if (t_dims.get(d, 0) + r_dims.get(d, 0)) > 0 else 0.0)
                for d in ("comprehensiveness", "insight", "instruction_following", "readability")}
        tasks.append({"id": tid, "lang": row.get("language", "en"), "overall": overall,
                      "target_total": t_total, "ref_total": r_total, "dims": dims,
                      "truncated": row.get("truncated", False)})

    tasks.sort(key=lambda t: t["id"])
    n = len(tasks)
    if n == 0:
        print("No tasks scored.")
        sys.exit(1)

    race = statistics.mean(t["overall"] for t in tasks) * 100
    en = [t for t in tasks if t["lang"] == "en"]
    zh = [t for t in tasks if t["lang"] == "zh"]
    dim_names = ("comprehensiveness", "insight", "instruction_following", "readability")
    dim_means = {d: statistics.mean(t["dims"][d] for t in tasks) * 100 for d in dim_names}
    truncated = sum(1 for t in tasks if t["truncated"])
    weakest = sorted(tasks, key=lambda t: t["overall"])[:3]
    strongest = sorted(tasks, key=lambda t: t["overall"], reverse=True)[:3]

    lines = []
    lines.append("# DRB RACE Results — Providence (self-judged)")
    lines.append("")
    lines.append(f"- **Judge:** {os.environ.get('DRB_JUDGE', 'manual LLM judge')}")
    lines.append(f"- **Tasks scored:** {n}/100 ({len(en)} en / {len(zh)} zh)"
                 f"{'  ⚠ truncated articles: ' + str(truncated) if truncated else ''}")
    lines.append(f"- **RACE score (mean overall × 100):** {race:.2f}")
    lines.append("")
    lines.append("## Per-dimension (mean target/(target+ref) × 100)")
    lines.append("")
    lines.append("| Dimension | Score |")
    lines.append("|-----------|-------|")
    for d in dim_names:
        lines.append(f"| {d} | {dim_means[d]:.2f} |")
    lines.append("")
    lines.append("## Per-task")
    lines.append("")
    lines.append("| id | lang | overall | comp | insight | instr | read | trunc |")
    lines.append("|----|------|---------|------|---------|-------|------|-------|")
    for t in tasks:
        lines.append(
            f"| {t['id']} | {t['lang']} | {t['overall']*100:.2f} | "
            f"{t['dims']['comprehensiveness']*100:.2f} | {t['dims']['insight']*100:.2f} | "
            f"{t['dims']['instruction_following']*100:.2f} | {t['dims']['readability']*100:.2f} | "
            f"{'Y' if t['truncated'] else ''} |")
    lines.append("")
    lines.append("## Best 3 / Weakest 3")
    lines.append("")
    lines.append("| Rank | id | overall |")
    lines.append("|------|----|---------|")
    for i, t in enumerate(strongest, 1):
        lines.append(f"| {i} | {t['id']} | {t['overall']*100:.2f} |")
    lines.append("")
    lines.append("| Rank | id | overall |")
    lines.append("|------|----|---------|")
    for i, t in enumerate(weakest, 1):
        lines.append(f"| {i} | {t['id']} | {t['overall']*100:.2f} |")
    if missing_criteria:
        lines.append("")
        lines.append(f"⚠ skipped (no criteria): {sorted(missing_criteria)}")

    with open(args.out, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"RACE score: {race:.2f}  ({n} tasks)  ->  {args.out}")
    for d in dim_names:
        print(f"  {d}: {dim_means[d]:.2f}")
    print(f"  en: {statistics.mean(t['overall'] for t in en)*100:.2f}" if en else "  en: n/a",
          f"| zh: {statistics.mean(t['overall'] for t in zh)*100:.2f}" if zh else "| zh: n/a")


if __name__ == "__main__":
    main()
