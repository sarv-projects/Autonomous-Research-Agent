# DeepResearch Bench — Self-Hosted Scoring Protocol (for the Luna session)

> **What this is.** A complete, mechanical protocol for scoring the **Providence** deep-research
> engine against the official **DeepResearch Bench** (DRB) — the industry benchmark that
> published leaderboard numbers exist for (Gemini 2.5 Pro ≈ 48.9 RACE, OpenAI Deep Research ≈
> 47.0, Perplexity ≈ 42.3). We cannot run the official scorer because it requires paid
> LLM/Jina keys. Instead, **you (the model in this session) are the judge**, applying the
> **exact official prompts and formulas** manually, task by task.
>
> **Judge identity:** when you score, you are acting as the official RACE judge model. Set
> `DRB_JUDGE` in your mind as `"GPT-5.6 Luna via Freebuff (manual, protocol identical to official RACE)"`
> — the score report must record this so nobody mistakes it for a GPT-5.5-official number.

---

## 0. Preconditions — check these FIRST, before any scoring

Run from the repo root: `/home/sarvesh/projects/Autonomous-Research-Agent`

```bash
# 1. Generation must be COMPLETE (all 100 tasks):
wc -l research/deep_research_bench/data/test_data/raw_data/providence.jsonl
#    → must print 100. If < 100, do NOT score yet.
#    The generation run is resumable:  bash benchmarks/drb_launch.sh   (skips done ids)

# 2. All input files exist:
ls research/deep_research_bench/data/prompt_data/query.jsonl            # 100 queries (id/prompt/language)
ls research/deep_research_bench/data/criteria_data/criteria.jsonl       # 100 per-task criteria WITH weights
ls research/deep_research_bench/data/test_data/cleaned_data/reference.jsonl  # 100 expert reference reports
ls research/deep_research_bench/data/test_data/raw_data/providence.jsonl     # our 100 reports (3-key format)

# 3. Output dirs:
mkdir -p benchmarks/logs/race benchmarks/logs/fact
```

**Language mapping:** each row of `query.jsonl` has `"language": "en"` or `"zh"`.
Task ids run 1–100. 50 en + 50 zh.

---

## 1. Paste this as your session system prompt

```
You are the judge for the DeepResearch Bench evaluation of the "Providence"
deep-research engine. Follow the protocol in score.md at the repo root
(/home/sarvesh/projects/Autonomous-Research-Agent/score.md) exactly.

Rules you must obey, no exceptions:
1. NEVER invent a score. Every score must be grounded in the actual text of the
   article you read in that task's files. If you cannot read an article (file
   missing/too large to load), record "error": "could not read" and skip the task —
   do not guess.
2. Compare, do not flatter. You are scoring Providence against an expert-written
   reference report. The reference is the bar; scoring it high does not inflate
   Providence. Be as harsh on Providence's gaps as the criteria demand.
3. Use the verbatim official judge prompt (Section 3) for every task. Do not
   improvise a shorter prompt.
4. Echo each criterion's text VERBATIM (exact string, original language) in your
   output — the aggregator matches weights by criterion text.
5. Write one JSON file per task to benchmarks/logs/race/id_XXX.json using the
   exact schema in Section 4. Append nothing else to those files.
6. Log every truncation. If an article exceeds the length cap you apply symmetric
   head+tail truncation to BOTH articles and set "truncated": true.
7. Work in id order, ~10–15 tasks per turn, and report progress in your reply.
   Resumable: never re-write an existing id_XXX.json — skip it.
8. When all 100 are done, run the aggregator (Section 5) and write the final
   report (Section 6) with the leaderboard comparison.
```

---

## 2. What you are comparing (inputs, per task id N)

| Slot | File | Field |
|------|------|-------|
| Task prompt | `research/deep_research_bench/data/prompt_data/query.jsonl` | `prompt` (row with `id` == N) |
| Criteria (WITH weights, for your own aggregation reference) | `research/deep_research_bench/data/criteria_data/criteria.jsonl` | row with `id` == N |
| **article_1 = target = Providence** | `research/deep_research_bench/data/test_data/raw_data/providence.jsonl` | row with `id` == N → `article` |
| **article_2 = reference = expert** | `research/deep_research_bench/data/test_data/cleaned_data/reference.jsonl` | row with `id` == N → `article` |
| Language | `query.jsonl` | `language` |

- **article_1 is ALWAYS Providence, article_2 is ALWAYS the expert reference.** The official
  calculator maps `article_1_score` → target and `article_2_score` → reference. Getting this
  backwards silently inverts every score.
- The criteria list passed to the judge prompt is the `criterions` object from the criteria
  row, **weights stripped** (the judge never sees weights; weights are applied later by the
  aggregator). Keep criteria in their original language (en tasks → English criteria,
  zh tasks → Chinese criteria).

**Context management (important — some reports are 50–270K chars):**
- Read the two articles for the task. If the combined size fits comfortably in your context,
  use full text (official behavior).
- If not, apply **symmetric head+tail truncation**: first 90,000 chars + last 60,000 chars of
  EACH article (150K cap, keeps structure + the Sources section). Apply the SAME policy to
  both articles for that task and set `"truncated": true` in the output JSON.
- Never truncate one side only.

---

## 3. The official judge prompt (verbatim — use for every task)

This is the `generate_merged_score_prompt` from the official harness
(`research/deep_research_bench/prompt/score_prompt_en.py`). Substitute the three placeholders:
`{task_prompt}`, `{article_1}` (Providence), `{article_2}` (reference), `{criteria_list}`
(criteria JSON without weights, from the task's criteria row).

For **zh** tasks, use the equivalent template from `research/deep_research_bench/prompt/score_prompt_zh.py`
(identical structure, Chinese wording) — read that file and use its exact text.

```
<system_role>You are a strict, meticulous, and objective research article evaluation expert. You excel at using specific assessment criteria to deeply compare two articles on the same task, providing precise scores and clear justifications.</system_role>

<user_prompt>
**Task Background**
There is a deep research task, and you need to evaluate two research articles written for this task. We will assess the articles across four dimensions: Comprehensiveness, Insight, Instruction Following, and Readability. The content is as follows:
<task>
"{task_prompt}"
</task>

**Articles to Evaluate**
<article_1>
"{article_1}"
</article_1>

<article_2>
"{article_2}"
</article_2>

**Evaluation Criteria**
Now, you need to evaluate and compare these two articles based on the following **evaluation criteria list**, providing comparative analysis and scoring each on a scale of 0-10. Each criterion includes an explanation, please understand carefully.

<criteria_list>
{criteria_list}
</criteria_list>

<Instruction>
**Your Task**
Please strictly evaluate and compare `<article_1>` and `<article_2>` based on **each criterion** in the `<criteria_list>`. You need to:
1.  **Analyze Each Criterion**: Consider how each article fulfills the requirements of each criterion.
2.  **Comparative Evaluation**: Analyze how the two articles perform on each criterion, referencing the content and criterion explanation.
3.  **Score Separately**: Based on your comparative analysis, score each article on each criterion (0-10 points).

**Scoring Rules**
For each criterion, score both articles on a scale of 0-10 (continuous values). The score should reflect the quality of performance on that criterion:
*   0-2 points: Very poor performance. Almost completely fails to meet the criterion requirements.
*   2-4 points: Poor performance. Minimally meets the criterion requirements with significant deficiencies.
*   4-6 points: Average performance. Basically meets the criterion requirements, neither good nor bad.
*   6-8 points: Good performance. Largely meets the criterion requirements with notable strengths.
*   8-10 points: Excellent/outstanding performance. Fully meets or exceeds the criterion requirements.

**Output Format Requirements**
Please **strictly** follow the `<output_format>` below for each criterion evaluation. **Do not include any other unrelated content, introduction, or summary**. Start with "Standard 1" and proceed sequentially through all criteria:
</Instruction>

<output_format>
{
    "comprehensiveness": [
        {
            "criterion": [Text content of the first comprehensiveness evaluation criterion],
            "analysis": [Comparative analysis],
            "article_1_score": [Continuous score 0-10],
            "article_2_score": [Continuous score 0-10]
        },
        {
            "criterion": [Text content of the second comprehensiveness evaluation criterion],
            "analysis": [Comparative analysis],
            "article_1_score": [Continuous score 0-10],
            "article_2_score": [Continuous score 0-10]
        },
        ...
    ],
    "insight": [
        {
            "criterion": [Text content of the first insight evaluation criterion],
            "analysis": [Comparative analysis],
            "article_1_score": [Continuous score 0-10],
            "article_2_score": [Continuous score 0-10]
        },
        ...
    ],
    ...
}
</output_format>

Now, please evaluate the two articles based on the research task and criteria, providing detailed comparative analysis and scores according to the requirements above. Ensure your output follows the specified `<output_format>` and that the JSON format is parsable, with all characters that might cause JSON parsing errors properly escaped.
</user_prompt>
```

**Scoring bands (memorize):** 0–2 very poor · 2–4 poor · 4–6 average · 6–8 good · 8–10 excellent.

---

## 4. Judge output file (one per task)

Write to `benchmarks/logs/race/id_001.json` … `id_100.json`. Exact schema:

```json
{
  "id": 1,
  "prompt": "<task prompt text>",
  "language": "en",
  "truncated": false,
  "notes": "optional observation (e.g. Providence fabricated a number, missed a sub-question)",
  "scores": {
    "comprehensiveness": [
      {"criterion": "<verbatim criterion text>", "analysis": "<comparative analysis>",
       "article_1_score": 8.0, "article_2_score": 7.5}
    ],
    "insight": [],
    "instruction_following": [],
    "readability": []
  }
}
```

Notes:
- `criterion` text must match the criteria row's text **exactly** (the aggregator falls back
  to fuzzy matching, but exact is better).
- Use `write_file` to create each `id_XXX.json`. Do not append — one file per task, clean JSON.
- If a task cannot be scored, write `{"id": N, "error": "reason"}` and continue.

---

## 5. Aggregation (do NOT hand-compute — run the script)

```bash
cd /home/sarvesh/projects/Autonomous-Research-Agent
DRB_JUDGE="GPT-5.6 Luna via Freebuff (manual, official RACE protocol)" \
  uv run python benchmarks/drb_score_local.py \
    --dir benchmarks/logs/race \
    --criteria research/deep_research_bench/data/criteria_data/criteria.jsonl \
    --out benchmarks/DRB_RACE_RESULTS.md
```

The script implements the official math exactly:

```
dim_avg    = Σ(score_i × w_i) / Σ(w_i)                        # per dimension, per article
total      = Σ(dim_avg × dim_weight)                          # dimension_weight from criteria row
overall    = target_total / (target_total + reference_total)  # per task (0..1)
RACE score = mean(overall across tasks) × 100                 # ← the leaderboard number
dim score  = target_dim / (target_dim + reference_dim) × 100  # per dimension
```

Sanity checks after running:
- Output should say `RACE score: XX.XX (100 tasks)`.
- If a task is missing from the table, find its `id_XXX.json` and re-score it.
- Reference-point calibration: a perfect copy of the reference would score ~50.0. If you
  routinely score Providence above ~65 on tasks where you can see obvious factual gaps,
  you are inflating — recalibrate toward the bands in Section 3.

---

## 6. Final report — write `benchmarks/DRB_SCORE.md`

Append (or create) this file with:

```markdown
# Providence on DeepResearch Bench — Self-judged Score

**Judge:** GPT-5.6 Luna via Freebuff (manual execution, official RACE prompt & formula)
**Method caveat:** Same protocol as the published leaderboard, but judged by Luna rather
than GPT-5.5 and with symmetric truncation on oversized articles (logged per task).
Not byte-identical to the official harness; treat as indicative, directionally comparable.

## RACE (report quality)
- **Score:** {RACE score} (mean overall × 100, 100 tasks)
- Per dimension: {dim scores from DRB_RACE_RESULTS.md}

## Leaderboard comparison (published ≈)
| System | RACE | Notes |
|--------|------|-------|
| Gemini 2.5 Pro Deep Research | ~48.9 | best published report quality |
| OpenAI Deep Research | ~47.0 | best instruction-following |
| Perplexity Deep Research | ~42.3 | highest citation accuracy (90.24%) |
| **Providence (self-judged)** | **{ours}** | Luna judge, official protocol |

## FACT (citation integrity) — only if Section 7 was completed
- Citation accuracy: {x}% over {n} verified statements · effective citations: {n}
- Coverage: {n}/{total} URLs verified, rest marked unknown

## Weakest / strongest tasks
- Strongest: {ids} · Weakest: {ids} · recurring failure modes: {list, from notes}
```

---

## 7. FACT (optional but strongly recommended — citation integrity)

The official FACT pipeline = extract claims → dedupe → scrape each URL → validate
supported/unsupported/unknown. The prompts below are the official English ones
(from `research/deep_research_bench/utils/`). Do this on a **stratified sample** (e.g. 20 reports:
10 en + 10 zh, spread across ids), because live-verifying ~3,000 URLs is not feasible in one
session. **Report coverage honestly** — a sample is a sample.

**7a. Extract** — for each sampled report, run the official extract prompt
(`research/deep_research_bench/utils/extract.py`, `prompt_template_en`) to get
`(fact, ref_idx, url)` triplets for every citation point. Save to
`benchmarks/logs/fact/id_XXX_extract.json`.

**7b. Dedupe** — deduplicate each report's extracted statements with the official dedup prompt
(`utils/deduplicate.py`, `prompt_template_en`): duplicates only if they express *exactly the
same thing*. Save `id_XXX_dedup.json`.

**7c. Verify** — for each unique URL, fetch the page (use `read_url`, or `curl -m 15 -sL`
via a spawned basher for speed). If the page cannot be fetched or is an error page, mark the
statement **unknown**. Then apply the official validate prompt (`utils/validate.py`,
`prompt_template_en`): with respect to the fetched reference, each statement is
**supported** (facts/data found entirely or partially, rounding accepted) /
**unsupported** (nothing in the statement found in the page) / **unknown** (page invalid).
Save `id_XXX_validate.json`.

**7d. Aggregate** (hand roll into the final report):
```
Citation accuracy = supported / (supported + unsupported)     # unknown excluded, reported separately
Effective citations = total supported statements across the sample
```

---

## 8. Integrity rules (non-negotiable)

1. **No fabricated scores.** Ground every score in text you actually read. Unreadable → error entry, skip.
2. **No inflating.** The reference is the bar; 50 ≈ parity. Be skeptical, especially on
   comprehensiveness (Providence's known weak axis is retrieval breadth, not verification).
3. **No retroactive editing.** Once `id_XXX.json` is written, do not re-score that task to
   "fix" the aggregate. If you believe a score was a mistake, append a note in the final
   report instead of silently rewriting history.
4. **Transparency beats polish.** Where the protocol is approximated (truncation, FACT
   sampling, Luna judge), say so in `DRB_SCORE.md`. A documented approximation is credible;
   an undocumented one is a lie.
5. **Symmetric truncation only** — never truncate one side of a comparison.

---

## 9. Quick reference — file map

| Path | Purpose |
|------|---------|
| `research/deep_research_bench/data/prompt_data/query.jsonl` | 100 task prompts + language |
| `research/deep_research_bench/data/criteria_data/criteria.jsonl` | per-task criteria + weights |
| `research/deep_research_bench/data/test_data/cleaned_data/reference.jsonl` | expert references (article_2) |
| `research/deep_research_bench/data/test_data/raw_data/providence.jsonl` | our reports (article_1) |
| `research/deep_research_bench/prompt/score_prompt_en.py` / `_zh.py` | official judge prompts |
| `research/deep_research_bench/utils/score_calculator.py` | official aggregation (we mirror it) |
| `research/deep_research_bench/utils/{extract,deduplicate,validate}.py` | official FACT prompts |
| `benchmarks/logs/race/id_*.json` | per-task judge output (you write these) |
| `benchmarks/drb_score_local.py` | aggregator (run it, don't hand-compute) |
| `benchmarks/DRB_RACE_RESULTS.md` | machine-generated per-task table |
| `benchmarks/DRB_SCORE.md` | final human-readable report + leaderboard |
