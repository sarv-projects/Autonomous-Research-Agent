"""
Benchmark topics — 15 high-complexity prompts stress-testing the research agent.

Each topic carries:
  - prompt:     the exact user query sent to the research engine
  - anchors:    topic-specific expected items (from the rubric) used for scoring
  - gt:         ground-truth verification questions (answered via web research)
                used to fact-check the report's numbers Green/Yellow/Red.
"""

TOPICS = [
    {
        "id": 1,
        "title": "BRICS+ New Development Bank vs IMF/World Bank",
        "domain": "Geopolitics & Trade",
        "prompt": (
            "Analyze the current (2026) lending capacity, conditionality frameworks, and "
            "currency settlement mechanisms of the BRICS+ New Development Bank (NDB) compared "
            "to the IMF and World Bank. Assess if the NDB is genuinely decoupling global south "
            "debt from dollar-hegemony."
        ),
        "anchors": [
            "Exact NDB total authorized capital (USD)",
            "Total approved loans in 2025 vs 2026",
            "% of loans settled in non-USD (CNY, INR, BRL)",
            "Structural adjustment terms for a specific distressed nation (Sri Lanka or Argentina)",
            "Russia's operational status within NDB post-sanctions",
            "Contrarian: NDB will fail to surpass IMF by 2030 (credit rating downgrades)",
        ],
        "gt": [
            "What is the New Development Bank's total authorized capital in USD as of 2026?",
            "How much did the NDB approve in new loans in 2025 and 2026?",
            "What share of NDB loans are settled in non-USD currencies (CNY, INR, BRL)?",
            "What lending conditions did the IMF and World Bank attach to Sri Lanka or Argentina debt programs?",
            "What is Russia's operational status inside the NDB after sanctions?",
            "Have NDB bonds been downgraded or is the bank facing credit rating pressure?",
        ],
    },
    {
        "id": 2,
        "title": "AMOC Collapse Probability",
        "domain": "Climate Tipping Points",
        "prompt": (
            "Synthesize the latest oceanographic data (2025-2026) regarding the Atlantic "
            "Meridional Overturning Circulation (AMOC). Provide the statistical probability of a "
            "collapse before 2050, and model the specific temperature differentials for Northern "
            "Europe, the US East Coast, and the Sahel region."
        ),
        "anchors": [
            "Specific salinity anomaly readings (PSU) at the OSNAP array",
            "Precise probability percentage (45% vs 55%) from two leading competing studies (Ditlevsen vs Rahmstorf)",
            "Projected UK wheat yield loss (tons/hectare) vs Brazilian soybean gains",
            "Greenland ice sheet meltwater flux (Gt/year) as forcing factor",
            "Contrarian: IPCC's conservative rebuttal that the probability is overblown",
        ],
        "gt": [
            "What is the latest AMOC collapse probability estimate before 2050 (Ditlevsen vs Rahmstorf)?",
            "What salinity anomaly readings (PSU) has the OSNAP array reported recently?",
            "What is the Greenland ice sheet meltwater flux in Gt/year?",
            "How much UK wheat yield loss is projected from AMOC collapse and how much Brazilian soybean gain?",
            "What does the IPCC's conservative assessment say about AMOC collapse probability?",
        ],
    },
    {
        "id": 3,
        "title": "Global Uranium Enrichment & SMR Viability",
        "domain": "Energy Grids",
        "prompt": (
            "Map the global supply chain for High-Assay Low-Enriched Uranium (HALEU) in 2026. "
            "Compare the operational readiness of Small Modular Reactors (SMRs) in the US, UK, and "
            "China, focusing on fuel availability and Levelized Cost of Energy (LCOE) against "
            "solar+storage."
        ),
        "anchors": [
            "Operational HALEU centrifuges: US (Centrus) vs Russia (Tenex) vs China (CNNC)",
            "Exact LCOE per MWh for first commercial SMR (NuScale or LING LONG One)",
            "NRC and ONR licensing approval timeline — specific 2027 dates",
            "Contrarian: SMRs already economically obsolete due to plummeting lithium prices",
        ],
        "gt": [
            "How much HALEU enrichment capacity does Centrus have in the US in 2026?",
            "What is the estimated LCOE per MWh of first-generation SMRs (NuScale, ACP100/LING LONG One) in 2026?",
            "What are the NRC (US) and ONR (UK) licensing decision dates scheduled for 2027?",
            "What is the current LCOE of solar plus storage vs SMRs?",
            "Have lithium battery prices fallen enough to undercut SMR economics?",
        ],
    },
    {
        "id": 4,
        "title": "ASAT Capabilities & Orbital Debris Cascade",
        "domain": "Space Warfare",
        "prompt": (
            "Assess the current (2026) anti-satellite (ASAT) capabilities of the US, China, Russia, "
            "and India. Using the current orbital debris density, calculate the risk of a Kessler "
            "Syndrome event in Low Earth Orbit (LEO) over the next decade."
        ),
        "anchors": [
            "Exact number of trackable debris >10cm added in 2025",
            "Specific launch dates of new 'inspector' satellites",
            "Electronic warfare (jamming) capabilities vs kinetic kill vehicles",
            "Projected annual loss (USD) to telecom industry if a LEO band is unusable",
            "Contrarian: SpaceX/Starlink — active debris removal (ADR) outpaces collision risk",
        ],
        "gt": [
            "How many trackable debris objects >10cm were added to the catalog in 2025?",
            "What is the current total trackable debris count in LEO?",
            "Which new 'inspector' or ASAT-capable satellites were launched in 2025-2026?",
            "What is the projected economic cost of losing a LEO band to debris?",
            "What is the status of active debris removal (ADR) missions in 2026?",
        ],
    },
    {
        "id": 5,
        "title": "Avian Influenza (H5N1) Human Transmission Risk",
        "domain": "Synthetic Biology / Epidemiology",
        "prompt": (
            "Analyze the genomic mutations of the current H5N1 clade circulating in dairy cattle "
            "(2025-2026). Evaluate the efficacy of existing mRNA stockpiles versus traditional "
            "adjuvanted vaccines if human-to-human transmission is declared by the WHO."
        ),
        "anchors": [
            "Specific PB2 and HA gene mutations identified",
            "Exact R0 (basic reproduction number) estimated if adapted to humans",
            "Exact vaccine courses held by US BARDA, EU HERA, China CDC",
            "Time-to-market (days) for targeted mRNA booster vs egg-based production",
            "Contrarian: gain-of-function defense — lab escape more likely than zoonotic spillover",
        ],
        "gt": [
            "Which PB2 and HA mutations are circulating in H5N1 clade 2.3.4.4b in dairy cattle 2025-2026?",
            "What is the estimated R0 of H5N1 if it adapts to human-to-human transmission?",
            "How many H5 vaccine courses does BARDA, HERA, and China's CDC hold?",
            "How quickly can an mRNA H5 booster vs egg-based vaccine be produced?",
            "What are the arguments about lab escape vs zoonotic spillover for H5N1?",
        ],
    },
    {
        "id": 6,
        "title": "Japan's Yen Carry Trade Unwind & Global Liquidity",
        "domain": "Macro-Economics",
        "prompt": (
            "Model the impact of the Bank of Japan's 2026 interest rate hikes on the global carry "
            "trade. Quantify the contagion risk to emerging markets (Turkey, Egypt, Pakistan) and "
            "US Tech equities."
        ),
        "anchors": [
            "Exact JPY/USD forward curve",
            "Specific amount of leverage (USD trillions) unwound in July/August 2026",
            "Correlation coefficient between Nikkei 225 and NASDAQ-100 over last 3 months",
            "BoJ's specific QE tapering schedule (JPY billion per month)",
            "Contrarian: Goldman Sachs — unwind beneficial for structural rebalancing",
        ],
        "gt": [
            "What is the BoJ policy rate and QE tapering schedule in 2026?",
            "How much carry-trade leverage was unwound in July/August 2026?",
            "What is the JPY/USD exchange rate and forward curve in 2026?",
            "What is the 3-month correlation between Nikkei 225 and NASDAQ-100?",
            "What is Goldman Sachs' view on the yen carry trade unwind?",
        ],
    },
    {
        "id": 7,
        "title": "Open-Source Frontier Models (Llama-4 vs GPT-5)",
        "domain": "AI Alignment",
        "prompt": (
            "Benchmark the real-world capabilities of Meta's Llama-4 (open-source) against OpenAI's "
            "GPT-5 (closed) in agentic coding, multi-modal reasoning, and adversarial robustness as "
            "of August 2026. Assess the regulatory response in the EU AI Act."
        ),
        "anchors": [
            "Exact scores on SWE-bench, MMLU-Pro, MATH-500 for both models (specific versions)",
            "Exact FLOPs and training cost (USD) for each",
            "Specific EU AI Act articles applying to each model's tier (systemic risk)",
            "Contrarian: 'scaling laws are dead' — both models represent a reasoning plateau",
        ],
        "gt": [
            "What are the exact SWE-bench, MMLU-Pro, and MATH-500 scores for Llama-4 and GPT-5?",
            "What is the estimated training compute (FLOPs) and cost for Llama-4 and GPT-5?",
            "Which EU AI Act articles apply to systemic-risk models (GPT-5 tier)?",
            "What evidence exists for or against 'scaling laws are dead' in 2026?",
        ],
    },
    {
        "id": 8,
        "title": "Deep-Sea Mining in the Clarion-Clipperton Zone",
        "domain": "Critical Minerals",
        "prompt": (
            "Evaluate the 2026 status of the International Seabed Authority (ISA) mining code. "
            "Quantify the environmental impact of extracting polymetallic nodules versus the "
            "geopolitical necessity of reducing reliance on Chinese rare-earth processing."
        ),
        "anchors": [
            "Exact tonnage of nodules required to meet 2030 EV battery demand (Nickel/Cobalt)",
            "Current ISA license holders",
            "Specific studies on sediment plume dispersion (km radius) and benthic impact",
            "US vs China positions on ratification",
            "Contrarian: terrestrial mining (Indonesia) ecologically less damaging than abyssal plain",
        ],
        "gt": [
            "Has the ISA adopted the mining code (exploitation regulations) in 2026?",
            "How many tons of polymetallic nodules would 2030 EV battery demand need?",
            "Who holds ISA exploration contracts in the Clarion-Clipperton Zone?",
            "What do sediment plume dispersion studies say about impact radius?",
            "What are the US and China positions on deep-sea mining ratification?",
        ],
    },
    {
        "id": 9,
        "title": "Global Housing Affordability Crisis (2026 Index)",
        "domain": "Social Infrastructure",
        "prompt": (
            "Compare the 2026 housing affordability indices (Price-to-Income ratio) for Sydney, "
            "Toronto, London, Mumbai, and Berlin. Analyze the specific policy interventions (rent "
            "control, supply-side subsidies, foreign buyer bans) that have failed or succeeded."
        ),
        "anchors": [
            "Exact Demographia International Housing Affordability ratings for each city",
            "Impact of 2026 mortgage rates (fixed vs variable) on new purchase volumes",
            "Exact drop in rents (percentage) in Berlin from 2025 rent cap renewal",
            "Contrarian: YIMBY — zoning deregulation is the only solution; demand subsidies inflationary",
        ],
        "gt": [
            "What are the 2026 Demographia price-to-income ratings for Sydney, Toronto, London, Mumbai, Berlin?",
            "What are 2026 mortgage rates in Australia, Canada, UK, Germany and their effect on purchase volumes?",
            "How much did Berlin rents fall after the 2025 rent cap renewal?",
            "What is the YIMBY vs rent-control policy debate in 2026?",
        ],
    },
    {
        "id": 10,
        "title": "Anti-Microbial Resistance (AMR) in G7 Hospitals",
        "domain": "Epidemiology",
        "prompt": (
            "Track the global spread of carbapenem-resistant Enterobacteriaceae (CRE) in 2026. "
            "Compare the mortality rates and treatment costs of new beta-lactamase inhibitors "
            "(e.g., tebipenem) versus phage therapy alternatives."
        ),
        "anchors": [
            "CDC and ECDC specific incidence rates (per 100,000 patient-days) for 2025 vs 2026",
            "Specific FDA/EMA approval dates for new antibiotics in Q2/Q3 2026",
            "Exact treatment cost per patient (USD) for ICU care vs phage therapy",
            "Contrarian: WHO — antibiotic development economically broken; 'subscription' models needed",
        ],
        "gt": [
            "What are the CDC and ECDC CRE incidence rates per 100,000 patient-days for 2025 and 2026?",
            "Which new antibiotics got FDA/EMA approval in Q2-Q3 2026 (e.g., tebipenem)?",
            "What does CRE treatment cost per patient in the ICU vs phage therapy?",
            "What is the WHO's position on antibiotic subscription/pull incentives?",
        ],
    },
    {
        "id": 11,
        "title": "Autonomous Trucking Deregulation (US & EU)",
        "domain": "Transportation",
        "prompt": (
            "Analyze the 2026 legislative breakthroughs allowing Level-4 autonomous trucks on "
            "interstate highways. Contrast the adoption rates, insurance liability frameworks, and "
            "job displacement metrics in the US (FHWA) vs EU (UNECE)."
        ),
        "anchors": [
            "Specific FMCSA ruling numbers and effective dates",
            "Cost-per-mile comparison (Autonomous vs Human) incl. deadhead reduction %",
            "Exact Teamsters job losses Q1 2026 vs newly created remote-monitor roles",
            "Contrarian: insurance data — autonomous trucks more prone to software-edge-case collisions in bad weather",
        ],
        "gt": [
            "What FMCSA rules allow Level-4 autonomous trucks on US interstates in 2026?",
            "What is the cost-per-mile of autonomous vs human-driven trucking in 2026?",
            "What are the job displacement numbers for US truck drivers (Teamsters) in 2026?",
            "What does the insurance industry say about autonomous truck safety in bad weather?",
        ],
    },
    {
        "id": 12,
        "title": "6G Standardization Wars (ITU vs 3GPP)",
        "domain": "Geopolitical Technology",
        "prompt": (
            "Assess the current state of 6G spectrum allocation (sub-THz bands) and standard-setting. "
            "Compare the patent essentiality declared by Huawei/China, Samsung/Korea, and "
            "Ericsson/EU."
        ),
        "anchors": [
            "Exact percentage of declared standard-essential patents (SEPs) per nation/entity",
            "Specific dates for the ITU-R IMT-2030 framework finalization",
            "Gallium Nitride (GaN) vs Silicon-Germanium (SiGe) power amplifier efficiencies",
            "Contrarian: DoD — 6G sub-THz frequencies useless for long-range battlefield comms",
        ],
        "gt": [
            "What percentage of declared 6G standard-essential patents do China, Korea, and EU hold?",
            "What is the ITU-R IMT-2030 finalization timeline?",
            "What are GaN vs SiGe power amplifier efficiency numbers for sub-THz?",
            "What are the military arguments against sub-THz for battlefield comms?",
        ],
    },
    {
        "id": 13,
        "title": "Colorado River Compact Re-Negotiation (2026)",
        "domain": "Water Security",
        "prompt": (
            "Analyze the 2026 re-negotiation of the Colorado River water usage tiers. Quantify the "
            "mandatory cutbacks for California, Arizona, and Nevada, and compare the efficacy of "
            "desalination (Mexico) vs agricultural fallowing (Imperial Valley)."
        ),
        "anchors": [
            "Exact Lake Mead and Lake Powell water elevations (feet) for August 2026",
            "Specific acre-feet of water that must be cut; exact payout per acre-foot for fallowing subsidies",
            "Specific Supreme Court rulings or federal decrees issued",
            "Contrarian: tribal/indigenous argument — prior appropriation doctrine must be overturned",
        ],
        "gt": [
            "What are Lake Mead and Lake Powell elevations in August 2026?",
            "How many acre-feet must California, Arizona, and Nevada cut under the 2026 agreement?",
            "What is the per-acre-foot payout for Imperial Valley fallowing?",
            "What is the tribal position on prior appropriation in the Colorado River talks?",
        ],
    },
    {
        "id": 14,
        "title": "Lunar Permanent Infrastructure (Artemis vs ILRS)",
        "domain": "Space Economy",
        "prompt": (
            "Compare the 2026 architectural design and funding status of NASA's Artemis Base Camp "
            "versus China/Russia's International Lunar Research Station (ILRS). Focus on in-situ "
            "resource utilization (ISRU) for water ice mining."
        ),
        "anchors": [
            "Specific mass (kg) and launch dates for the Lunar Terrain Vehicle (LTV) and Chinese landers",
            "Exact allocated USD (inflation-adjusted) for each project through 2026",
            "Specific chemical electrolysis processes for lunar regolith → oxygen/methane",
            "Contrarian: private sector (SpaceX/Blue Origin) — government bases outdated, will be privatized",
        ],
        "gt": [
            "What is the Lunar Terrain Vehicle (LTV) mass and launch date?",
            "What are the Artemis Base Camp and ILRS budgets through 2026?",
            "Which ISRU processes convert lunar regolith into oxygen and methane?",
            "What is SpaceX/Blue Origin's lunar infrastructure timeline vs Artemis?",
        ],
    },
    {
        "id": 15,
        "title": "Global AI-Tutoring Experiment",
        "domain": "Education & Workforce",
        "prompt": (
            "Evaluate the 2026 results from large-scale AI tutoring deployments (K-12) in the UK, "
            "Singapore, and the US (Newark district). Compare standardized test score improvements "
            "against traditional classroom controls, specifically analyzing equity gaps."
        ),
        "anchors": [
            "Exact standard deviation improvements (Effect Size) in Math and Reading PISA-equivalent scores",
            "Specific data on student dropout rates and engagement hours",
            "Cost-per-student for AI license vs human teaching assistant salaries",
            "Contrarian: cognitive science — AI tutors create 'learned helplessness', reduce neural plasticity",
        ],
        "gt": [
            "What effect sizes did AI tutoring show on math and reading tests in 2026 deployments (UK, Singapore, Newark)?",
            "What are the engagement hours and dropout data for AI tutoring programs?",
            "What is the cost per student of AI tutoring vs human teaching assistants?",
            "What does cognitive science say about AI tutors and learned helplessness?",
        ],
    },
]
