# Autonomous Research Agent

An autonomous AI agent that researches any topic by searching the web, analyzing results, and generating a structured Markdown report. All decisions (what to search, when to stop, how to structure findings) are made by an LLM -- no hardcoded rules.

Built with: **LangGraph** (agent orchestration), **Groq** (LLM inference), **Tavily** (web search API).

## Prerequisites

- Python 3.14+
- **uv** (Python package manager) -- install it:

  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
  Or see other install methods at https://docs.astral.sh/uv/#installation

- A **Groq API key** (free) -- get one at https://console.groq.com
- A **Tavily API key** (free) -- get one at https://app.tavily.com

## Setup

```bash
# 1. Clone the repository
git clone <repo-url>
cd xiarch_assessment

# 2. Create virtual environment and install dependencies
uv venv
uv sync

# 3. Create .env file with your API keys
cp .env.example .env
# Then edit .env and paste your actual keys:
#   GROQ_API_KEY=gsk_abc123...
#   TAVILY_API_KEY=tvly-xyz789...
```

## Usage

```bash
# Research a topic
uv run python main.py "your research topic here"

# View past searches
uv run python main.py --history
```

### Example

```bash
uv run python main.py "latest developments in quantum computing"
```

The agent will:
1. Analyze your query via LLM
2. Generate 3-5 search queries
3. Run all searches in parallel (5 concurrent)
4. Extract full content from top results
5. Deduplicate and filter using LLM
6. Evaluate if more research is needed (loops up to 3 times)
7. Synthesize a structured report
8. Save to `reports/` directory as Markdown

### Expected Output

```
============================================================
  RESEARCH: latest developments in quantum computing
============================================================

[0] Analyzing your query...
[1] Planning search queries (iteration 1)...
[1] Searching the web...
  Found 21 unique results
...
[3] Synthesizing research report...
  Report generated (8085 chars)

============================================================
  RESEARCH COMPLETE
============================================================
  Time: 137.4s
  Iterations: 3
  Findings: 22
  Sources: 24
  Report: /home/user/xiarch_assessment/reports/research_...md
```

Your report is at the path shown under "Report:".

## Project Structure

```
src/
  llm.py       Groq LLM wrapper (with rate limit retry)
  search.py    Tavily search (parallel execution)
  state.py     State type definition (the data backpack)
  nodes.py     9 LangGraph node functions
  graph.py     Graph builder with conditional edges
  memory.py    Past search memory (JSON file)
  export.py    Markdown report export
main.py        CLI entry point
test_run.py    Unit tests
```

## Report Format

Each generated report includes:
- **Overview** -- 2-3 paragraph summary
- **Key Points** -- bullet points of most important findings
- **Detailed Findings** -- deeper dive into key topics
- **Sources/References** -- numbered list with URLs
- **Actionable Insights** -- specific takeaways
- **Methodology** -- how the research was conducted

## Tests

```bash
uv run python test_run.py
```

Expected output: `5/5 tests passed`

## Troubleshooting

**"Rate limit reached" error (429)**
Groq free tier allows 8K tokens per minute. Each research session uses 5-8 LLM calls. If you hit the limit:
- Wait 60 seconds and retry
- The agent has built-in retry (exponential backoff: 2s, 4s, 8s)

**"No module named 'src.xxx'"**
Make sure you ran `uv sync` from the project root directory.

## Features

### Required
- Accepts any user query/topic as input
- Searches external sources via Tavily web search API
- Extracts full content from top results
- LLM-powered deduplication of irrelevant/duplicate content
- Generates structured report: key points, findings, sources, insights

### Bonus
- LLM allows to autonomously selects search strategies and sources
- Parallel information gathering (5 concurrent searches per iteration)
- Export as Markdown
- Stores past searches in JSON memory (keyword-based recall)
- Multi-step reasoning with up to 3 research iterations
- Conditional looping: LLM decides when research is complete
- Progress output with status messages
