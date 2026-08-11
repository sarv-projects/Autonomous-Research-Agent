# Research Agent Benchmark Report (Round 3)

**Suite:** 15 high-complexity topics · **Mode:** `standard` (default budget) · **Date:** 2026-08-11 (Round 3)
**Stack:** Groq (workhorse) + Exa (search) + Gemini (scout) + OpenCode Zen (free fallback) · LangGraph A4 pipeline

**Method:** Each topic ran through the full pipeline (scout → plan → research loop → adversary → adjudicator → synth → compiler). Outputs scored against a universal 6-checkpoint rubric (per topic) plus topic anchors, with a fact-check matrix comparing **ground-truth numbers from independent web research** against the report text: 🟢 Green = exact/within-tolerance, 🟡 Yellow = partial/near-miss, 🔴 Red = missing/contradicted.

## Aggregate Results

| # | Topic | Time | Sections | Cites | Domains | News | Checkpoints | Fact 🟢/🟡/🔴 | Fact acc. | Grade |
|---|-------|------|----------|-------|---------|------|-------------|---------------|-----------|-------|
| 6 | Japan's Yen Carry Trade Unwind & Global Liqu | 702s | 15 | 35 | 21 | 6 | 0.83 | 5/0/0 | 1.00 | **A** |
| 7 | Open-Source Frontier Models (Llama-4 vs GPT- | 464s | 15 | 33 | 23 | 0 | 0.70 | 6/0/1 | 0.86 | **B** |
| 10 | Anti-Microbial Resistance (AMR) in G7 Hospit | 478s | 12 | 34 | 21 | 0 | 0.83 | 4/1/0 | 0.90 | **A** |
| 11 | Autonomous Trucking Deregulation (US & EU) | 448s | 14 | 34 | 22 | 0 | 0.78 | 3/2/1 | 0.67 | **B** |
| 13 | Colorado River Compact Re-Negotiation (2026) | 592s | 12 | 33 | 17 | 1 | 0.89 | 4/0/2 | 0.67 | **B** |
| 14 | Lunar Permanent Infrastructure (Artemis vs I | 507s | 14 | 36 | 17 | 0 | 0.92 | 3/0/3 | 0.50 | **B** |

**Averages:** 532s per topic · checkpoint coverage 0.83 · fact-check accuracy 0.77 · tier-1 newswire domains 1.2

**Latency vs product Deep Research:** OpenAI/Gemini Deep Research typically 5–30 min per query; this agent averaged **8.9 min** on the same class of query — within/below that band.

## Universal Checkpoint Detail

| # | Topic | Data | Geo | Sources | Contrarian | Temporal | Actionable |
|---|-------|------|-----|---------|------------|----------|------------|
| 6 | Japan's Yen Carry Trade Unwind & Global  | 100% | 75% | 60% | 100% | 60% | 100% |
| 7 | Open-Source Frontier Models (Llama-4 vs  | 70% | 50% | 40% | 100% | 60% | 100% |
| 10 | Anti-Microbial Resistance (AMR) in G7 Ho | 70% | 50% | 80% | 100% | 100% | 100% |
| 11 | Autonomous Trucking Deregulation (US & E | 40% | 75% | 53% | 100% | 100% | 100% |
| 13 | Colorado River Compact Re-Negotiation (2 | 100% | 50% | 87% | 100% | 100% | 100% |
| 14 | Lunar Permanent Infrastructure (Artemis  | 100% | 75% | 80% | 100% | 100% | 100% |

## Citation Depth

- **T6** (Japan's Yen Carry Trade Unwind & Global ): 21 domains · 3 peer-reviewed · 0 gov/regulatory · 6 tier-1 newswire · cites [1–35]
- **T7** (Open-Source Frontier Models (Llama-4 vs ): 23 domains · 4 peer-reviewed · 0 gov/regulatory · 0 tier-1 newswire · cites [1–33]
- **T10** (Anti-Microbial Resistance (AMR) in G7 Ho): 21 domains · 6 peer-reviewed · 7 gov/regulatory · 0 tier-1 newswire · cites [1–34]
- **T11** (Autonomous Trucking Deregulation (US & E): 22 domains · 1 peer-reviewed · 6 gov/regulatory · 0 tier-1 newswire · cites [1–34]
- **T13** (Colorado River Compact Re-Negotiation (2): 17 domains · 3 peer-reviewed · 5 gov/regulatory · 1 tier-1 newswire · cites [1–33]
- **T14** (Lunar Permanent Infrastructure (Artemis ): 17 domains · 3 peer-reviewed · 5 gov/regulatory · 0 tier-1 newswire · cites [1–36]

## Per-Topic Logs & Fact-Check Matrix

### T6 — Japan's Yen Carry Trade Unwind & Global Liquidity

**Prompt:** Model the impact of the Bank of Japan's 2026 interest rate hikes on the global carry trade. Quantify the contagion risk to emerging markets (Turkey, Egypt, Pakistan) and US Tech equities.

**Run:** mode=standard · 702.0s · 15 sections · 196485 chars · 36 findings · 20 claims · evidence graph 20 edges · adjudicated {'supported': 20, 'contested': 0, 'synthetic': 0} · citations [1–35] · ship-gate PASS

**Checkpoints:** data 100% · geo 75% · sources 60% · contrarian 100% · temporal 60% · actionable 100% → **A**

| Fact (ground truth) | Status |
|---------------------|--------|
| BoJ rate | 🟢 GREEN (1.0%, 1.00%, 0.75) |
| JGB taper | 🟢 GREEN (2T) |
| USD/JPY | 🟢 GREEN (158, 162, 163, 165) |
| Aug 2024 unwind | 🟢 GREEN (1 trillion) |
| Correlation | 🟢 GREEN (0.65, 0.78) |

**Ground truth summary:** BoJ policy rate 1.0% (hike from 0.75% June 2026). JGB taper toward ~JPY 2T/month, pause April 2027. USD/JPY 158-162 mid-2026; Goldman: 162 (3m) / 163 (6m) / 165 (12m). Aug 2024 carry unwind ~$1T; mid-2026 event hundreds of billions. Nikkei-NASDAQ 3m correlation +0.65 to +0.78. Goldman: unwind supports Japan structural rebalancing.

**Research debt flags:** Contested claim needs stronger evidence: U.S. stocks opened the month lower, with the Dow falling 500 points, the S&P 50; Contested claim needs stronger evidence: Yen weakness is contributing to inflationary pressures in Japan, prompting the ; Open gap: Counter-evidence gathered — report must address limitations and failed cases; Open gap: The impact of the Bank of Japan's 2026 interest rate hikes on emerging markets (Turkey, Egypt, Pakistan) and U

### T7 — Open-Source Frontier Models (Llama-4 vs GPT-5)

**Prompt:** Benchmark the real-world capabilities of Meta's Llama-4 (open-source) against OpenAI's GPT-5 (closed) in agentic coding, multi-modal reasoning, and adversarial robustness as of August 2026. Assess the regulatory response in the EU AI Act.

**Run:** mode=standard · 463.6s · 15 sections · 231982 chars · 5 findings · 0 claims · evidence graph 0 edges · adjudicated {'supported': 0, 'contested': 0, 'synthetic': 0} · citations [1–33] · ship-gate PASS

**Checkpoints:** data 70% · geo 50% · sources 40% · contrarian 100% · temporal 60% · actionable 100% → **B**

| Fact (ground truth) | Status |
|---------------------|--------|
| GPT-5 SWE-bench | 🟢 GREEN (74.9, 80) |
| Llama-4 SWE-bench | 🟢 GREEN (52.9, 59) |
| GPT-5 MMLU | 🟢 GREEN (93.5) |
| Llama-4 MMLU | 🟢 GREEN (85.5) |
| GPT-5 MATH-500 | 🟢 GREEN (95, 99.4) |
| Training cost | 🔴 RED |
| EU AI Act articles | 🟢 GREEN (51, 55) |

**Ground truth summary:** SWE-bench Verified: GPT-5 74.9-80%, Llama-4 52.9-59%. MMLU: GPT-5 ~93.5%, Llama-4 Maverick ~85.5%. MATH-500: GPT-5 95-99.4%. GPT-5 training ~1e26-1e27 FLOPs, $500M-2.5B; Llama-4 Behemoth ~1e25-1e26 FLOPs, hundreds of millions $. EU AI Act: Art 51 systemic-risk presumption >1e25 FLOPs, Art 52 notification, Art 53 baseline, Art 55 systemic-risk obligations.

**Research debt flags:** Open gap: Counter-evidence gathered — report must address limitations and failed cases

### T10 — Anti-Microbial Resistance (AMR) in G7 Hospitals

**Prompt:** Track the global spread of carbapenem-resistant Enterobacteriaceae (CRE) in 2026. Compare the mortality rates and treatment costs of new beta-lactamase inhibitors (e.g., tebipenem) versus phage therapy alternatives.

**Run:** mode=standard · 477.7s · 12 sections · 121370 chars · 12 findings · 8 claims · evidence graph 8 edges · adjudicated {'supported': 8, 'contested': 0, 'synthetic': 0} · citations [1–34] · ship-gate PASS

**Checkpoints:** data 70% · geo 50% · sources 80% · contrarian 100% · temporal 100% · actionable 100% → **A**

| Fact (ground truth) | Status |
|---------------------|--------|
| CDC CRE rate | 🟢 GREEN (100,000) |
| NDM surge | 🟢 GREEN (1.35) |
| Tebipenem approval | 🟢 GREEN (tebipenem) |
| ICU cost | 🟡 YELLOW (66031) |
| Phage cost | 🟢 GREEN (5,000, 15,000) |

**Ground truth summary:** CDC: CRE incidence rose from <2 to >3 per 100,000 population (2019 vs 2023-25, +69%); NDM-CRE +460% (0.25 → 1.35 per 100,000). Tebipenem (Utebzi) FDA-approved June 17, 2026 — first oral carbapenem. ICU CRE treatment $22,484-$66,031+ per patient; phage therapy $5,000-15,000+. WHO supports delinked pull incentives / subscription models (PASTEUR Act).

**Research debt flags:** Open gap: No specific data or projections on the global spread of CRE in 2026.; Open gap: No comparative mortality rates or treatment cost analyses between new beta-lactamase inhibitors (e.g., tebipen; Open gap: Lack of detailed information on the efficacy and availability of newly approved antimicrobials against CRE.; Open gap: No specific data on the implementation and effectiveness of CRE management plans across EU Member States.

### T11 — Autonomous Trucking Deregulation (US & EU)

**Prompt:** Analyze the 2026 legislative breakthroughs allowing Level-4 autonomous trucks on interstate highways. Contrast the adoption rates, insurance liability frameworks, and job displacement metrics in the US (FHWA) vs EU (UNECE).

**Run:** mode=standard · 448.5s · 14 sections · 169228 chars · 14 findings · 5 claims · evidence graph 5 edges · adjudicated {'supported': 5, 'contested': 0, 'synthetic': 0} · citations [1–34] · ship-gate PASS

**Checkpoints:** data 40% · geo 75% · sources 53% · contrarian 100% · temporal 100% · actionable 100% → **B**

| Fact (ground truth) | Status |
|---------------------|--------|
| FMCSA docket | 🟡 YELLOW (0958) |
| UNECE ADS | 🟢 GREEN (WP.29) |
| Human CPM | 🟡 YELLOW (2.336, 2.34) |
| AV CPM | 🟢 GREEN (1.89) |
| Deadhead | 🟢 GREEN (15%, 20%, 22%) |
| IIHS 68% | 🔴 RED |

**Ground truth summary:** FMCSA docket FMCSA-2026-0958 (91 FR 20252, Apr 15, 2026) — Aurora 5-yr exemption from 49 CFR 392.22(b)/393.25(e)/393.95(f); prior waiver expired July 9, 2026. UNECE WP.29 adopted first global ADS regulation June 24, 2026. ATRI 2026: human CPM $2.336 (ex-fuel $1.854); AV pilot $1.89/mi; parity ~2028. Deadhead 15-22% cut by 15-20%. 1 remote-monitor role per 5-10 driving jobs displaced. IIHS July 2026: AVs 68% fewer crashes; weather remains ODD vulnerability.

**Research debt flags:** Open gap: Counter-evidence gathered — report must address limitations and failed cases

### T13 — Colorado River Compact Re-Negotiation (2026)

**Prompt:** Analyze the 2026 re-negotiation of the Colorado River water usage tiers. Quantify the mandatory cutbacks for California, Arizona, and Nevada, and compare the efficacy of desalination (Mexico) vs agricultural fallowing (Imperial Valley).

**Run:** mode=standard · 591.8s · 12 sections · 196778 chars · 33 findings · 17 claims · evidence graph 17 edges · adjudicated {'supported': 13, 'contested': 4, 'synthetic': 0} · citations [1–33] · ship-gate PASS

**Checkpoints:** data 100% · geo 50% · sources 87% · contrarian 100% · temporal 100% · actionable 100% → **B**

| Fact (ground truth) | Status |
|---------------------|--------|
| Lake Mead elevation | 🟢 GREEN (1040) |
| Lake Powell elevation | 🟢 GREEN (3521) |
| Arizona cut | 🔴 RED |
| California cut | 🔴 RED |
| Nevada cut | 🟢 GREEN (50,000, 50K) |
| Fallowing payout | 🟢 GREEN (840, acre-foot) |

**Ground truth summary:** Lake Mead 1,040.4 ft (Aug 7, 2026); Lake Powell ~3,521.09 ft (Aug 9, 2026); Powell dead pool 3,490 ft. Lower Basin cuts 2027-28 up to 1.5M acre-feet: Arizona 760K, California 440K, Nevada 50K. Imperial Valley fallowing up to $840/acre-foot. Navajo Nation v. US (June 22, 2023, 5-4): no affirmative treaty duty. Tribes challenge prior appropriation via Winters doctrine.

**Research debt flags:** ...; ...

### T14 — Lunar Permanent Infrastructure (Artemis vs ILRS)

**Prompt:** Compare the 2026 architectural design and funding status of NASA's Artemis Base Camp versus China/Russia's International Lunar Research Station (ILRS). Focus on in-situ resource utilization (ISRU) for water ice mining.

**Run:** mode=standard · 506.7s · 14 sections · 129910 chars · 21 findings · 11 claims · evidence graph 11 edges · adjudicated {'supported': 11, 'contested': 0, 'synthetic': 0} · citations [1–36] · ship-gate PASS

**Checkpoints:** data 100% · geo 75% · sources 80% · contrarian 100% · temporal 100% · actionable 100% → **B**

| Fact (ground truth) | Status |
|---------------------|--------|
| LTV teams | 🟢 GREEN (Lunar Outpost, Astrolab) |
| Artemis budget | 🟢 GREEN (93, 102.5, billion) |
| Chang'e 5 | 🔴 RED |
| Chang'e 6 | 🔴 RED |
| ISRU electrolysis | 🟢 GREEN (electrolysis, Sabatier) |
| Blue Moon | 🔴 RED |

**Ground truth summary:** LTV: Lunar Outpost Pegasus + Venturi Astrolab CLV-1 (May 2026 awards), launch late 2020s; Astrolab FLIP late 2026 via Griffin-1. Artemis cumulative ~$93-102.5B; China space budget $19-20B/yr; ILRS crew-ready mid-2030s. Chang'e 5: 8,200 kg, Nov 23, 2020, 1,731 g samples. Chang'e 6: 8,350 kg, May 3, 2024, 1,935.3 g. ISRU: molten regolith electrolysis up to 96% oxygen extraction; Sabatier for methane. Blue Moon Mk2: 21,350 kg, 3,000 kg payload, demo 2027, crewed 2030.

**Research debt flags:** Open gap: Counter-evidence gathered — report must address limitations and failed cases

## Strengths / Weaknesses vs Rubric

- **Best topic:** T6 — fact acc 1.00
- **Weakest topic:** T14 — fact acc 0.50

- **Checkpoint averages:** contrarian_fork 100% · actionable_thesis 100% · temporal_trajectory 87% · data_granularity 80% · source_diversity 67% · geographic_equity 62%

- **Red-flag facts by topic:** T14 (3); T13 (2); T7 (1); T11 (1); T6 (0); T10 (0)

---
*Generated by `benchmarks/score_benchmark.py` from per-topic run logs + ground-truth web research.*