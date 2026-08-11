"""Compare benchmark rounds R1 (original), R2 (thin-run fix), R3 (+news) for the 6 re-run topics."""
import json
import glob
import os
import re

NEWS_RE = re.compile(
    r"(reuters|bloomberg|ft\.com|wsj|cnbc|caixin|apnews|bbc|guardian|economist|"
    r"nikkei|scmp|aljazeera|dw\.com|france24|xinhuanet|chinadaily|timesofindia|"
    r"thehindu|livemint|japantimes|straitstimes|channelnewsasia|gulfnews|"
    r"marketwatch|techcrunch|theverge|axios|politico|yahoo\.com)"
)


def load(logdir):
    out = {}
    for p in sorted(glob.glob(os.path.join(logdir, "T*.json"))):
        d = json.load(open(p))
        tid = str(d.get("topic_id"))
        rp = d.get("report_copy") or ""
        report = ""
        if rp and os.path.exists(rp):
            report = open(rp, encoding="utf-8").read()
        doms = d.get("sources_domains") or {}
        news = sum(1 for k in doms if NEWS_RE.search(k))
        out[tid] = {
            "dur": d.get("duration_s", 0),
            "secs": d.get("sections_count", 0),
            "chars": d.get("report_chars", 0),
            "findings": d.get("findings_count", 0),
            "claims": d.get("claims_count", 0),
            "cits": len(d.get("citation_numbers") or []),
            "news": news,
            "err": d.get("error"),
        }
    return out


r1 = load("benchmarks/logs")
r2 = load("benchmarks/logs/round2")
r3 = load("benchmarks/logs/round3")
topics = ("6", "7", "10", "11", "13", "14")

hdr = f"{'T':<4}{'metric':<10}{'R1':>12}{'R2':>12}{'R3':>12}"
print(hdr)
print("-" * len(hdr))
for tid in topics:
    a, b, c = r1.get(tid), r2.get(tid), r3.get(tid)
    if not (a and b and c):
        continue
    print(f"T{tid}  {'duration':<10}{a['dur']:>8.0f}s{b['dur']:>8.0f}s{c['dur']:>8.0f}s")
    print(f"     {'sections':<10}{a['secs']:>12}{b['secs']:>12}{c['secs']:>12}")
    print(f"     {'chars':<10}{a['chars']:>12,}{b['chars']:>12,}{c['chars']:>12,}")
    print(f"     {'findings':<10}{a['findings']:>12}{b['findings']:>12}{c['findings']:>12}")
    print(f"     {'claims':<10}{a['claims']:>12}{b['claims']:>12}{c['claims']:>12}")
    print(f"     {'citations':<10}{a['cits']:>12}{b['cits']:>12}{c['cits']:>12}")
    print(f"     {'newswire':<10}{a['news']:>12}{b['news']:>12}{c['news']:>12}")
    print()


def agg(rows, key):
    return sum(r[key] for r in rows) / len(rows)


t1 = [r1[t] for t in topics]
t2 = [r2[t] for t in topics]
t3 = [r3[t] for t in topics]
print("=== AGGREGATE (6 re-run topics) ===")
for k, label in (("secs", "sections"), ("chars", "chars"), ("findings", "findings"),
                 ("claims", "claims"), ("cits", "citations"), ("news", "newswire")):
    print(f"  {label:<12} R1={agg(t1, k):8.1f}  R2={agg(t2, k):8.1f}  R3={agg(t3, k):8.1f}")

# news counts that made it into final reports at least once
print("\n=== NEWSWIRE COVERAGE (domains in final report Sources) ===")
for tid in topics:
    print(f"  T{tid}: R1={r1[tid]['news']}  R2={r2[tid]['news']}  R3={r3[tid]['news']}")
