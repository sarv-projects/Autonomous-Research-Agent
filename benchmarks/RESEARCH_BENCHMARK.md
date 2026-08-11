# Research Agent Benchmark Report

**Suite:** 15 high-complexity topics · **Mode:** `standard` (default budget) · **Date:** 2026-08-11
**Stack:** Groq (workhorse) + Exa (search) + Gemini (scout) + OpenCode Zen (free fallback) · LangGraph A4 pipeline

**Method:** Each topic ran through the full pipeline (scout → plan → research loop → adversary → adjudicator → synth → compiler). Outputs scored against a universal 6-checkpoint rubric (per topic) plus topic anchors, with a fact-check matrix comparing **ground-truth numbers from independent web research** against the report text: 🟢 Green = exact/within-tolerance, 🟡 Yellow = partial/near-miss, 🔴 Red = missing/contradicted.

## Aggregate Results

| # | Topic | Time | Sections | Cites | Domains | Checkpoints | Fact 🟢/🟡/🔴 | Fact acc. | Grade |
|---|-------|------|----------|-------|---------|-------------|---------------|-----------|-------|
| 1 | BRICS+ New Development Bank vs IMF/World Ban | 425s | 14 | 35 | 15 | 0.94 | 7/0/0 | 1.00 | **A** |
| 2 | AMOC Collapse Probability | 423s | 13 | 35 | 19 | 0.79 | 7/0/0 | 1.00 | **A** |
| 3 | Global Uranium Enrichment & SMR Viability | 418s | 13 | 36 | 24 | 0.94 | 6/0/0 | 1.00 | **A** |
| 4 | ASAT Capabilities & Orbital Debris Cascade | 484s | 13 | 41 | 25 | 0.97 | 5/0/1 | 0.83 | **A** |
| 5 | Avian Influenza (H5N1) Human Transmission Ri | 443s | 15 | 34 | 17 | 0.76 | 6/1/0 | 0.93 | **A** |
| 6 | Japan's Yen Carry Trade Unwind & Global Liqu | 731s | 14 | 32 | 17 | 0.76 | 4/0/1 | 0.80 | **B** |
| 7 | Open-Source Frontier Models (Llama-4 vs GPT- | 588s | 13 | 34 | 20 | 0.65 | 6/0/1 | 0.86 | **B** |
| 8 | Deep-Sea Mining in the Clarion-Clipperton Zo | 683s | 13 | 34 | 15 | 0.90 | 5/1/0 | 0.92 | **A** |
| 9 | Global Housing Affordability Crisis (2026 In | 998s | 14 | 27 | 17 | 0.62 | 6/0/0 | 1.00 | **A** |
| 10 | Anti-Microbial Resistance (AMR) in G7 Hospit | 258s | 5 | 34 | 13 | 0.62 | 4/1/0 | 0.90 | **B** |
| 11 | Autonomous Trucking Deregulation (US & EU) | 230s | 6 | 34 | 26 | 0.66 | 3/2/1 | 0.67 | **B** |
| 12 | 6G Standardization Wars (ITU vs 3GPP) | 380s | 13 | 33 | 17 | 0.90 | 6/0/0 | 1.00 | **A** |
| 13 | Colorado River Compact Re-Negotiation (2026) | 345s | 13 | 37 | 24 | 0.83 | 4/0/2 | 0.67 | **B** |
| 14 | Lunar Permanent Infrastructure (Artemis vs I | 370s | 6 | 33 | 12 | 0.72 | 3/0/3 | 0.50 | **C** |
| 15 | Global AI-Tutoring Experiment | 549s | 15 | 31 | 19 | 0.80 | 4/0/1 | 0.80 | **B** |

**Averages:** 488s per topic · checkpoint coverage 0.79 · fact-check accuracy 0.86

**Latency vs product Deep Research:** OpenAI/Gemini Deep Research typically 5–30 min per query; this agent averaged **8.1 min** on the same class of query — within/below that band.

## Universal Checkpoint Detail

| # | Topic | Data | Geo | Sources | Contrarian | Temporal | Actionable |
|---|-------|------|-----|---------|------------|----------|------------|
| 1 | BRICS+ New Development Bank vs IMF/World | 100% | 100% | 67% | 100% | 100% | 100% |
| 2 | AMOC Collapse Probability | 40% | 75% | 60% | 100% | 100% | 100% |
| 3 | Global Uranium Enrichment & SMR Viabilit | 100% | 75% | 87% | 100% | 100% | 100% |
| 4 | ASAT Capabilities & Orbital Debris Casca | 100% | 100% | 80% | 100% | 100% | 100% |
| 5 | Avian Influenza (H5N1) Human Transmissio | 40% | 75% | 80% | 100% | 60% | 100% |
| 6 | Japan's Yen Carry Trade Unwind & Global  | 70% | 50% | 73% | 100% | 60% | 100% |
| 7 | Open-Source Frontier Models (Llama-4 vs  | 40% | 50% | 40% | 100% | 60% | 100% |
| 8 | Deep-Sea Mining in the Clarion-Clipperto | 100% | 100% | 40% | 100% | 100% | 100% |
| 9 | Global Housing Affordability Crisis (202 | 10% | 100% | 53% | 50% | 60% | 100% |
| 10 | Anti-Microbial Resistance (AMR) in G7 Ho | 10% | 75% | 80% | 50% | 60% | 100% |
| 11 | Autonomous Trucking Deregulation (US & E | 10% | 75% | 53% | 100% | 60% | 100% |
| 12 | 6G Standardization Wars (ITU vs 3GPP) | 100% | 75% | 67% | 100% | 100% | 100% |
| 13 | Colorado River Compact Re-Negotiation (2 | 100% | 25% | 73% | 100% | 100% | 100% |
| 14 | Lunar Permanent Infrastructure (Artemis  | 40% | 75% | 67% | 50% | 100% | 100% |
| 15 | Global AI-Tutoring Experiment | 100% | 75% | 93% | 50% | 60% | 100% |

## Citation Depth

- **T1** (BRICS+ New Development Bank vs IMF/World): 15 domains · 2 peer-reviewed · 2 gov/regulatory · 0 news · cites [1–35]
- **T2** (AMOC Collapse Probability): 19 domains · 6 peer-reviewed · 1 gov/regulatory · 0 news · cites [1–35]
- **T3** (Global Uranium Enrichment & SMR Viabilit): 24 domains · 5 peer-reviewed · 6 gov/regulatory · 1 news · cites [1–36]
- **T4** (ASAT Capabilities & Orbital Debris Casca): 25 domains · 4 peer-reviewed · 8 gov/regulatory · 0 news · cites [1–41]
- **T5** (Avian Influenza (H5N1) Human Transmissio): 17 domains · 8 peer-reviewed · 6 gov/regulatory · 0 news · cites [1–34]
- **T6** (Japan's Yen Carry Trade Unwind & Global ): 17 domains · 2 peer-reviewed · 3 gov/regulatory · 1 news · cites [1–32]
- **T7** (Open-Source Frontier Models (Llama-4 vs ): 20 domains · 3 peer-reviewed · 0 gov/regulatory · 0 news · cites [1–34]
- **T8** (Deep-Sea Mining in the Clarion-Clipperto): 15 domains · 4 peer-reviewed · 0 gov/regulatory · 0 news · cites [1–34]
- **T9** (Global Housing Affordability Crisis (202): 17 domains · 1 peer-reviewed · 8 gov/regulatory · 0 news · cites [1–27]
- **T10** (Anti-Microbial Resistance (AMR) in G7 Ho): 13 domains · 7 peer-reviewed · 6 gov/regulatory · 0 news · cites [1–34]
- **T11** (Autonomous Trucking Deregulation (US & E): 26 domains · 1 peer-reviewed · 7 gov/regulatory · 0 news · cites [1–34]
- **T12** (6G Standardization Wars (ITU vs 3GPP)): 17 domains · 2 peer-reviewed · 4 gov/regulatory · 0 news · cites [1–33]
- **T13** (Colorado River Compact Re-Negotiation (2): 24 domains · 2 peer-reviewed · 5 gov/regulatory · 1 news · cites [1–37]
- **T14** (Lunar Permanent Infrastructure (Artemis ): 12 domains · 2 peer-reviewed · 5 gov/regulatory · 0 news · cites [1–33]
- **T15** (Global AI-Tutoring Experiment): 19 domains · 4 peer-reviewed · 5 gov/regulatory · 2 news · cites [1–31]

## Per-Topic Logs & Fact-Check Matrix

### T1 — BRICS+ New Development Bank vs IMF/World Bank

**Prompt:** Analyze the current (2026) lending capacity, conditionality frameworks, and currency settlement mechanisms of the BRICS+ New Development Bank (NDB) compared to the IMF and World Bank. Assess if the NDB is genuinely decoupling global south debt from dollar-hegemony.

**Run:** mode=standard · 425.3s · 14 sections · 244750 chars · 12 findings · 0 claims · evidence graph 0 edges · adjudicated {'supported': 0, 'contested': 0, 'synthetic': 0} · citations [1–35] · ship-gate PASS

**Checkpoints:** data 100% · geo 100% · sources 67% · contrarian 100% · temporal 100% · actionable 100% → **A**

| Fact (ground truth) | Status |
|---------------------|--------|
| NDB authorized capital | 🟢 GREEN (100 billion, $100B, 100,000) |
| NDB subscribed capital | 🟢 GREEN (50 billion, $50B) |
| Cumulative approvals end-2025 | 🟢 GREEN (42.9) |
| 2025 annual approvals | 🟢 GREEN (3.17, 19 project) |
| Local currency share | 🟢 GREEN (30%, 23%, 25%) |
| Russia lending frozen 2022 | 🟢 GREEN (Russia) |
| Fitch downgrade AA+ to AA 2022 | 🟢 GREEN (AA) |

**Ground truth summary:** NDB authorized capital $100B, initial subscribed $50B (equal $10B per founding member). Cumulative approved loans >$42.9B across ~139 projects by end-2025; 2025 annual approvals 19 projects = $3.17B. Local-currency share ~23-25%, targeting 30% (2022-2026 strategy). Russia: new lending frozen since March 2022 but keeps board seat. Ratings: S&P AA+, Fitch AA (downgraded AA+→AA July 2022, outlook Positive May 2026). NDB: no policy conditionality vs IMF structural adjustment.

**Research debt flags:** Open gap: Counter-evidence gathered — report must address limitations and failed cases

### T2 — AMOC Collapse Probability

**Prompt:** Synthesize the latest oceanographic data (2025-2026) regarding the Atlantic Meridional Overturning Circulation (AMOC). Provide the statistical probability of a collapse before 2050, and model the specific temperature differentials for Northern Europe, the US East Coast, and the Sahel region.

**Run:** mode=standard · 423.4s · 13 sections · 149231 chars · 27 findings · 22 claims · evidence graph 22 edges · adjudicated {'supported': 21, 'contested': 1, 'synthetic': 0} · citations [1–35] · ship-gate PASS

**Checkpoints:** data 40% · geo 75% · sources 60% · contrarian 100% · temporal 100% · actionable 100% → **A**

| Fact (ground truth) | Status |
|---------------------|--------|
| Ditlevsen collapse year 2057 | 🟢 GREEN (2057) |
| Ditlevsen probability | 🟢 GREEN (15%) |
| van Westen/Smolders pre-2050 probability | 🟢 GREEN (59%, 59 ± 17, 59) |
| Greenland melt flux Gt/yr | 🟢 GREEN (250, 300, Gt) |
| OSNAP salinity PSU | 🟢 GREEN (34.9, 35.0) |
| UK wheat t/ha | 🟢 GREEN (7.0, 8.0, t/ha) |
| IPCC AR6 'unlikely' collapse | 🟢 GREEN (unlikely) |

**Ground truth summary:** Ditlevsen & Ditlevsen 2023: collapse central estimate 2057 (CI 2037-2095), ~15% probability over next 100 years. Smolders/van Westen et al. 2025: 59±17% probability of AMOC collapse onset before 2050. Greenland melt ~250-300 Gt/yr (hosing thresholds up to 5,000 Gt/yr). OSNAP salinity ~34.9-35.0 PSU baseline. UK wheat ~7-8 t/ha normal, collapse scenarios -1.0 to -3.0 t/ha or -40% production. IPCC AR6: 'very likely decline, collapse during 21st century unlikely (medium confidence)'.

**Research debt flags:** ...; ...

### T3 — Global Uranium Enrichment & SMR Viability

**Prompt:** Map the global supply chain for High-Assay Low-Enriched Uranium (HALEU) in 2026. Compare the operational readiness of Small Modular Reactors (SMRs) in the US, UK, and China, focusing on fuel availability and Levelized Cost of Energy (LCOE) against solar+storage.

**Run:** mode=standard · 418.4s · 13 sections · 170686 chars · 14 findings · 6 claims · evidence graph 6 edges · adjudicated {'supported': 6, 'contested': 0, 'synthetic': 0} · citations [1–36] · ship-gate PASS

**Checkpoints:** data 100% · geo 75% · sources 87% · contrarian 100% · temporal 100% · actionable 100% → **A**

| Fact (ground truth) | Status |
|---------------------|--------|
| Centrus HALEU capacity | 🟢 GREEN (920) |
| Centrus DOE contract | 🟢 GREEN (900 million, $900) |
| NuScale module | 🟢 GREEN (77) |
| SMR LCOE | 🟢 GREEN (100, 150, MWh) |
| Solar LCOE | 🟢 GREEN (40, 98) |
| Battery pack price | 🟢 GREEN (108, $108) |

**Ground truth summary:** Centrus: ~920 kg HALEU produced, $900M DOE contract July 2026 to scale toward 12,000 kg/yr (12 t). NuScale uprated 77 MWe module. SMR FOAK LCOE ~$100-150+/MWh vs utility solar $40-98/MWh; battery packs $108/kWh 2025 (-8% YoY), ESS $70/kWh. NRC 10 CFR Part 53 finalization ~2027. ONR GDA ongoing for Rolls-Royce SMR.

**Research debt flags:** Open gap: No comprehensive mapping of the global HALEU supply chain for 2026 is provided in the content.; Open gap: Operational readiness comparisons of SMRs in the US, UK, and China are not included.; Open gap: Specific LCOE values for SMRs versus solar+storage are not provided.; Open gap: Details on HALEU fuel availability for SMRs in 2026 are missing.

### T4 — ASAT Capabilities & Orbital Debris Cascade

**Prompt:** Assess the current (2026) anti-satellite (ASAT) capabilities of the US, China, Russia, and India. Using the current orbital debris density, calculate the risk of a Kessler Syndrome event in Low Earth Orbit (LEO) over the next decade.

**Run:** mode=standard · 483.9s · 13 sections · 197680 chars · 21 findings · 11 claims · evidence graph 11 edges · adjudicated {'supported': 11, 'contested': 0, 'synthetic': 0} · citations [1–41] · ship-gate PASS

**Checkpoints:** data 100% · geo 100% · sources 80% · contrarian 100% · temporal 100% · actionable 100% → **A**

| Fact (ground truth) | Status |
|---------------------|--------|
| Trackable objects | 🟢 GREEN (46000) |
| LEO debris count | 🔴 RED |
| Kosmos inspector launch | 🟢 GREEN (2581, Feb) |
| Shijian launch | 🟢 GREEN (Shijian, 29) |
| WEF cost | 🟢 GREEN (25.8, 42.3, billion) |
| ADR missions | 🟢 GREEN (Astroscale, ClearSpace, ADR) |

**Ground truth summary:** ~46,200 trackable objects; 27,465 in LEO (16,811 payloads, 4,709 fragmentation debris >10cm). Russia Kosmos-2581/2/3 inspector launches Feb 5, 2025; China Shijian-29A/29B Jan 29, 2026 (GEO). WEF: $25.8-42.3B debris cost over decade, $14.2-30.7B anomalies. ADR: ADRAS-J (Astroscale), ClearSpace-1 (~€86M). India Mission Shakti 2019 kinetic.

**Research debt flags:** Open gap: Counter-evidence gathered — report must address limitations and failed cases

### T5 — Avian Influenza (H5N1) Human Transmission Risk

**Prompt:** Analyze the genomic mutations of the current H5N1 clade circulating in dairy cattle (2025-2026). Evaluate the efficacy of existing mRNA stockpiles versus traditional adjuvanted vaccines if human-to-human transmission is declared by the WHO.

**Run:** mode=standard · 443.3s · 15 sections · 196469 chars · 14 findings · 7 claims · evidence graph 7 edges · adjudicated {'supported': 7, 'contested': 0, 'synthetic': 0} · citations [1–34] · ship-gate PASS

**Checkpoints:** data 40% · geo 75% · sources 80% · contrarian 100% · temporal 60% · actionable 100% → **A**

| Fact (ground truth) | Status |
|---------------------|--------|
| PB2 mutations | 🟢 GREEN (E627K, D701N, PB2) |
| Dairy herds | 🟢 GREEN (1073) |
| R0 estimate | 🟢 GREEN (1.4, 2.2, 2.5) |
| BARDA doses | 🟢 GREEN (4.8) |
| HERA doses | 🟡 YELLOW (665000) |
| mRNA timeline | 🟢 GREEN (14, 30) |
| Egg timeline | 🟢 GREEN (60, 120) |

**Ground truth summary:** H5N1 clade 2.3.4.4b genotype B3.13 in dairy (1,073+ herds). Mutations: PB2-M631L (majority), PB2-E627K, PB2-D701N. R0 avian 0.1-0.3; human-adapted pandemic estimate 1.4-2.2 (up to 2.5). BARDA 4.8M finished doses; EU HERA 665,000 doses (framework to 40M); China ~20M/yr capacity. mRNA booster 14-30 days vs egg-based 60-120 days.

**Research debt flags:** Open gap: No direct comparative efficacy data between mRNA stockpiles and traditional adjuvanted vaccines against the cu; Open gap: Lack of real-world human vaccine effectiveness data against contemporary H5N1 clades.; Open gap: Unclear timeline and likelihood of WHO declaring human-to-human H5N1 transmission.; Open gap: Limited data on cross-protection breadth of existing mRNA vaccines against diverse 2.3.4.4b subgenotypes.

### T6 — Japan's Yen Carry Trade Unwind & Global Liquidity

**Prompt:** Model the impact of the Bank of Japan's 2026 interest rate hikes on the global carry trade. Quantify the contagion risk to emerging markets (Turkey, Egypt, Pakistan) and US Tech equities.

**Run:** mode=standard · 730.7s · 14 sections · 170673 chars · 32 findings · 15 claims · evidence graph 15 edges · adjudicated {'supported': 13, 'contested': 2, 'synthetic': 0} · citations [1–32] · ship-gate PASS

**Checkpoints:** data 70% · geo 50% · sources 73% · contrarian 100% · temporal 60% · actionable 100% → **B**

| Fact (ground truth) | Status |
|---------------------|--------|
| BoJ rate | 🟢 GREEN (1.0%, 1.00%, 0.75) |
| JGB taper | 🔴 RED |
| USD/JPY | 🟢 GREEN (158, 162, 163, 165) |
| Aug 2024 unwind | 🟢 GREEN (1 trillion, $1T) |
| Correlation | 🟢 GREEN (0.65, 0.78) |

**Ground truth summary:** BoJ policy rate 1.0% (hike from 0.75% June 2026). JGB taper toward ~JPY 2T/month, pause April 2027. USD/JPY 158-162 mid-2026; Goldman: 162 (3m) / 163 (6m) / 165 (12m). Aug 2024 carry unwind ~$1T; mid-2026 event hundreds of billions. Nikkei-NASDAQ 3m correlation +0.65 to +0.78. Goldman: unwind supports Japan structural rebalancing.

**Research debt flags:** Contested claim needs stronger evidence: Contagion risk to emerging‑market currencies such as Turkey, Egypt, and Pakista; Open gap: Counter-evidence gathered — report must address limitations and failed cases; Contested claim needs stronger evidence: US technology equities may experience a negative spillover from BOJ rate hikes ; Open gap: Budget: Tool-call budget exceeded (25 >= 25)

### T7 — Open-Source Frontier Models (Llama-4 vs GPT-5)

**Prompt:** Benchmark the real-world capabilities of Meta's Llama-4 (open-source) against OpenAI's GPT-5 (closed) in agentic coding, multi-modal reasoning, and adversarial robustness as of August 2026. Assess the regulatory response in the EU AI Act.

**Run:** mode=standard · 588.3s · 13 sections · 169335 chars · 13 findings · 7 claims · evidence graph 7 edges · adjudicated {'supported': 7, 'contested': 0, 'synthetic': 0} · citations [1–34] · ship-gate PASS

**Checkpoints:** data 40% · geo 50% · sources 40% · contrarian 100% · temporal 60% · actionable 100% → **B**

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

**Research debt flags:** ...; ...

### T8 — Deep-Sea Mining in the Clarion-Clipperton Zone

**Prompt:** Evaluate the 2026 status of the International Seabed Authority (ISA) mining code. Quantify the environmental impact of extracting polymetallic nodules versus the geopolitical necessity of reducing reliance on Chinese rare-earth processing.

**Run:** mode=standard · 682.6s · 13 sections · 197616 chars · 12 findings · 6 claims · evidence graph 6 edges · adjudicated {'supported': 6, 'contested': 0, 'synthetic': 0} · citations [1–34] · ship-gate PASS

**Checkpoints:** data 100% · geo 100% · sources 40% · contrarian 100% · temporal 100% · actionable 100% → **A**

| Fact (ground truth) | Status |
|---------------------|--------|
| ISA code not adopted | 🟢 GREEN (not, no) |
| Contracts | 🟢 GREEN (31, 17, 19) |
| China contracts | 🟢 GREEN (5) |
| Plume radius | 🟢 GREEN (4.5) |
| Sediment multiplier | 🟡 YELLOW (10000) |
| EV metal demand | 🟢 GREEN (56) |

**Ground truth summary:** ISA mining code NOT adopted as of 2026 (31st session; ISBA/30/C/CRP.1 in negotiation). 31 exploration contracts total, 17-19 for CCZ nodules. China COMRA holds 5 contracts (most of any member). Plume: 4.5-9 km dispersion; 10,000x sediment concentration; ~5 cm top sediment removed; ~3 cm smothering layer. 56 kg Ni + 7 kg Co per 75 kWh EV. US not ratified UNCLOS (DSHMRA 1980, EO 14285); China full party.

**Research debt flags:** ...; ...

### T9 — Global Housing Affordability Crisis (2026 Index)

**Prompt:** Compare the 2026 housing affordability indices (Price-to-Income ratio) for Sydney, Toronto, London, Mumbai, and Berlin. Analyze the specific policy interventions (rent control, supply-side subsidies, foreign buyer bans) that have failed or succeeded.

**Run:** mode=standard · 998.5s · 14 sections · 185144 chars · 24 findings · 11 claims · evidence graph 11 edges · adjudicated {'supported': 9, 'contested': 2, 'synthetic': 0} · citations [1–27] · ship-gate PASS

**Checkpoints:** data 10% · geo 100% · sources 53% · contrarian 50% · temporal 60% · actionable 100% → **A**

| Fact (ground truth) | Status |
|---------------------|--------|
| Sydney multiple | 🟢 GREEN (12.2) |
| Toronto multiple | 🟢 GREEN (7.7) |
| UK 2-yr rate | 🟢 GREEN (4.87) |
| UK 5-yr rate | 🟢 GREEN (4.98) |
| Germany long rate | 🟢 GREEN (3.38, 3.95, 2.85) |
| Berlin cap | 🟢 GREEN (10%, 11%) |

**Ground truth summary:** Demographia 2026: Sydney median multiple 12.2 (2nd least affordable), Toronto 7.7. UK rates 4.87% (2-yr fix), 4.98% (5-yr fix); Germany 2.85% short-term, 3.38-3.95% long-term. Berlin Mietpreisbremse extended to 2029, cap 10% above Mietspiegel; historic freeze studies ~11% advertised rent drop in restricted segments. YIMBY: zoning deregulation only durable fix; demand subsidies inflationary in supply-constrained markets.

**Research debt flags:** ...; ...

### T10 — Anti-Microbial Resistance (AMR) in G7 Hospitals

**Prompt:** Track the global spread of carbapenem-resistant Enterobacteriaceae (CRE) in 2026. Compare the mortality rates and treatment costs of new beta-lactamase inhibitors (e.g., tebipenem) versus phage therapy alternatives.

**Run:** mode=standard · 258.4s · 5 sections · 53492 chars · 5 findings · 0 claims · evidence graph 0 edges · adjudicated {'supported': 0, 'contested': 0, 'synthetic': 0} · citations [1–34] · ship-gate PASS

**Checkpoints:** data 10% · geo 75% · sources 80% · contrarian 50% · temporal 60% · actionable 100% → **B**

| Fact (ground truth) | Status |
|---------------------|--------|
| CDC CRE rate | 🟢 GREEN (100,000) |
| NDM surge | 🟢 GREEN (1.35) |
| Tebipenem approval | 🟢 GREEN (tebipenem) |
| ICU cost | 🟡 YELLOW (66031) |
| Phage cost | 🟢 GREEN (5,000) |

**Ground truth summary:** CDC: CRE incidence rose from <2 to >3 per 100,000 population (2019 vs 2023-25, +69%); NDM-CRE +460% (0.25 → 1.35 per 100,000). Tebipenem (Utebzi) FDA-approved June 17, 2026 — first oral carbapenem. ICU CRE treatment $22,484-$66,031+ per patient; phage therapy $5,000-15,000+. WHO supports delinked pull incentives / subscription models (PASTEUR Act).

**Research debt flags:** ...; ...

### T11 — Autonomous Trucking Deregulation (US & EU)

**Prompt:** Analyze the 2026 legislative breakthroughs allowing Level-4 autonomous trucks on interstate highways. Contrast the adoption rates, insurance liability frameworks, and job displacement metrics in the US (FHWA) vs EU (UNECE).

**Run:** mode=standard · 229.5s · 6 sections · 53402 chars · 30 findings · 12 claims · evidence graph 16 edges · adjudicated {'supported': 12, 'contested': 0, 'synthetic': 0} · citations [1–34] · ship-gate PASS

**Checkpoints:** data 10% · geo 75% · sources 53% · contrarian 100% · temporal 60% · actionable 100% → **B**

| Fact (ground truth) | Status |
|---------------------|--------|
| FMCSA docket | 🟡 YELLOW (0958, 20252) |
| UNECE ADS | 🟢 GREEN (June 24, WP.29) |
| Human CPM | 🟡 YELLOW (2.336, 2.34) |
| AV CPM | 🟢 GREEN (1.89) |
| Deadhead | 🟢 GREEN (15%, 20%, 22%) |
| IIHS 68% | 🔴 RED |

**Ground truth summary:** FMCSA docket FMCSA-2026-0958 (91 FR 20252, Apr 15, 2026) — Aurora 5-yr exemption from 49 CFR 392.22(b)/393.25(e)/393.95(f); prior waiver expired July 9, 2026. UNECE WP.29 adopted first global ADS regulation June 24, 2026. ATRI 2026: human CPM $2.336 (ex-fuel $1.854); AV pilot $1.89/mi; parity ~2028. Deadhead 15-22% cut by 15-20%. 1 remote-monitor role per 5-10 driving jobs displaced. IIHS July 2026: AVs 68% fewer crashes; weather remains ODD vulnerability.

**Research debt flags:** Open gap: Actual adoption rates of Level‑4 autonomous trucks on US interstate highways versus EU roads.; Open gap: Specific insurance liability frameworks adopted by the US FHWA and EU regulatory bodies for Level‑4 trucks.; Open gap: Quantitative job displacement metrics (e.g., number of truck drivers affected) in the US and EU.; Open gap: Details on how the UNECE framework will be integrated into national regulations beyond the technical approval 

### T12 — 6G Standardization Wars (ITU vs 3GPP)

**Prompt:** Assess the current state of 6G spectrum allocation (sub-THz bands) and standard-setting. Compare the patent essentiality declared by Huawei/China, Samsung/Korea, and Ericsson/EU.

**Run:** mode=standard · 380.1s · 13 sections · 171482 chars · 5 findings · 0 claims · evidence graph 0 edges · adjudicated {'supported': 0, 'contested': 0, 'synthetic': 0} · citations [1–33] · ship-gate PASS

**Checkpoints:** data 100% · geo 75% · sources 67% · contrarian 100% · temporal 100% · actionable 100% → **A**

| Fact (ground truth) | Status |
|---------------------|--------|
| Huawei SEP share | 🟢 GREEN (15.39, 22.94) |
| Samsung share | 🟢 GREEN (10%, 15%) |
| Ericsson share | 🟢 GREEN (10%, 12%) |
| IMT-2030 | 🟢 GREEN (2030, 2027) |
| GaN PAE | 🟢 GREEN (20%, 30%) |
| SiGe PAE | 🟢 GREEN (15%, 25%) |

**Ground truth summary:** 6G SEPs pre-standardization; 5G baseline: Huawei 15.39% patent families / 22.94% 3GPP contributions; Samsung 10-15%; Ericsson 10-12% (peak 17.6-20.1%). IMT-2030: framework ITU-R M.2160 June 22, 2023; TPRs Feb 2026 (5/116); eval guidelines June 2026 (5/119); submissions Feb 2027-Oct 2029; final specs June 2029-June 2030. GaN PAE 20-30% vs SiGe 15-25% at sub-THz. DoD: sub-THz unusable for long-range battlefield (attenuation, LOS-only).

**Research debt flags:** Open gap: Counter-evidence gathered — report must address limitations and failed cases

### T13 — Colorado River Compact Re-Negotiation (2026)

**Prompt:** Analyze the 2026 re-negotiation of the Colorado River water usage tiers. Quantify the mandatory cutbacks for California, Arizona, and Nevada, and compare the efficacy of desalination (Mexico) vs agricultural fallowing (Imperial Valley).

**Run:** mode=standard · 345.0s · 13 sections · 225168 chars · 11 findings · 5 claims · evidence graph 5 edges · adjudicated {'supported': 5, 'contested': 0, 'synthetic': 0} · citations [1–37] · ship-gate PASS

**Checkpoints:** data 100% · geo 25% · sources 73% · contrarian 100% · temporal 100% · actionable 100% → **B**

| Fact (ground truth) | Status |
|---------------------|--------|
| Lake Mead elevation | 🟢 GREEN (1040) |
| Lake Powell elevation | 🟢 GREEN (3521) |
| Arizona cut | 🔴 RED |
| California cut | 🔴 RED |
| Nevada cut | 🟢 GREEN (50,000) |
| Fallowing payout | 🟢 GREEN (840, acre-foot) |

**Ground truth summary:** Lake Mead 1,040.4 ft (Aug 7, 2026); Lake Powell ~3,521.09 ft (Aug 9, 2026); Powell dead pool 3,490 ft. Lower Basin cuts 2027-28 up to 1.5M acre-feet: Arizona 760K, California 440K, Nevada 50K. Imperial Valley fallowing up to $840/acre-foot. Navajo Nation v. US (June 22, 2023, 5-4): no affirmative treaty duty. Tribes challenge prior appropriation via Winters doctrine.

**Research debt flags:** Open gap: Counter-evidence gathered — report must address limitations and failed cases

### T14 — Lunar Permanent Infrastructure (Artemis vs ILRS)

**Prompt:** Compare the 2026 architectural design and funding status of NASA's Artemis Base Camp versus China/Russia's International Lunar Research Station (ILRS). Focus on in-situ resource utilization (ISRU) for water ice mining.

**Run:** mode=standard · 369.7s · 6 sections · 57221 chars · 21 findings · 14 claims · evidence graph 14 edges · adjudicated {'supported': 14, 'contested': 0, 'synthetic': 0} · citations [1–33] · ship-gate PASS

**Checkpoints:** data 40% · geo 75% · sources 67% · contrarian 50% · temporal 100% · actionable 100% → **C**

| Fact (ground truth) | Status |
|---------------------|--------|
| LTV teams | 🟢 GREEN (Lunar Outpost, Astrolab) |
| Artemis budget | 🟢 GREEN (93, 102.5, billion) |
| Chang'e 5 | 🔴 RED |
| Chang'e 6 | 🔴 RED |
| ISRU electrolysis | 🟢 GREEN (96%, electrolysis, Sabatier) |
| Blue Moon | 🔴 RED |

**Ground truth summary:** LTV: Lunar Outpost Pegasus + Venturi Astrolab CLV-1 (May 2026 awards), launch late 2020s; Astrolab FLIP late 2026 via Griffin-1. Artemis cumulative ~$93-102.5B; China space budget $19-20B/yr; ILRS crew-ready mid-2030s. Chang'e 5: 8,200 kg, Nov 23, 2020, 1,731 g samples. Chang'e 6: 8,350 kg, May 3, 2024, 1,935.3 g. ISRU: molten regolith electrolysis up to 96% oxygen extraction; Sabatier for methane. Blue Moon Mk2: 21,350 kg, 3,000 kg payload, demo 2027, crewed 2030.

**Research debt flags:** Open gap: Counter-evidence gathered — report must address limitations and failed cases

### T15 — Global AI-Tutoring Experiment

**Prompt:** Evaluate the 2026 results from large-scale AI tutoring deployments (K-12) in the UK, Singapore, and the US (Newark district). Compare standardized test score improvements against traditional classroom controls, specifically analyzing equity gaps.

**Run:** mode=standard · 548.7s · 15 sections · 221219 chars · 11 findings · 6 claims · evidence graph 6 edges · adjudicated {'supported': 6, 'contested': 0, 'synthetic': 0} · citations [1–31] · ship-gate PASS

**Checkpoints:** data 100% · geo 75% · sources 93% · contrarian 50% · temporal 60% · actionable 100% → **B**

| Fact (ground truth) | Status |
|---------------------|--------|
| Harvard effect size | 🟢 GREEN (0.73, 1.30, SD) |
| Eedi UK trial | 🟢 GREEN (66.2, 60.7) |
| AI license cost | 🟢 GREEN (15, 40, student) |
| Tutor cost | 🟢 GREEN (35, 80) |
| Learned helplessness | 🔴 RED |

**Ground truth summary:** Harvard RCT (Kestin, Scientific Reports 2025): AI tutor effect size 0.73-1.30 SD vs active-learning controls. Eedi/Google LearnLM UK trial: AI 66.2% vs 60.7% human-tutored control on novel problems. Engagement 20-30 min/session 3-5x/week (~50-60 hrs/yr). Cost: AI license $15-40/student/yr vs human tutors $35-80/hr (~50-100x cheaper). Cognitive science: learned helplessness, cognitive offloading, metacognition erosion.

**Research debt flags:** Open gap: No specific data or results from 2026 large-scale AI tutoring deployments in the UK, Singapore, or the Newark ; Open gap: There is no direct comparison of standardized test score improvements between AI tutoring and traditional clas; Open gap: No analysis of equity gaps in relation to AI tutoring interventions is included in the available content.; Open gap: The content does not specify which AI tools were used in Newark or how they were implemented in the tutoring p

## Strengths / Weaknesses vs Rubric

- **Best topic:** T1 — fact acc 1.00
- **Weakest topic:** T14 — fact acc 0.50

- **Checkpoint averages:** actionable_thesis 100% · contrarian_fork 87% · temporal_trajectory 81% · geographic_equity 75% · source_diversity 68% · data_granularity 64%

- **Red-flag facts by topic:** T14 (3); T13 (2); T4 (1); T6 (1); T7 (1); T11 (1)

---
*Generated by `benchmarks/score_benchmark.py` from per-topic run logs + ground-truth web research.*