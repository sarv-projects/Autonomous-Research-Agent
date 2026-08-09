"""
Autonomous Research Agent
=========================
Multi-agent research: Planner · Researcher · Critic · Synthesizer · Compiler
Gateway + RAG + progressive section output + citation ship-gate

Commands:
    uv run python main.py research "topic" [--mode MODE]   Run research
    uv run python main.py chat                              Start chat session
    uv run python main.py doctor                            Check provider/tool status
    uv run python main.py --history                         Show past searches
"""

import sys
import time

from src.graph import run_research
from src.llm import call_llm, gateway_info
from src.memory import get_history, save_search, find_similar
from src.eval import create_component_evaluator, create_system_evaluator
from src.web import app


def print_header(text: str) -> None:
    print()
    print("=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_section(text: str) -> None:
    print()
    print(f"  {text}")
    print("  " + "-" * 40)


def _check_tavily() -> tuple[bool, str]:
    import os
    key = os.getenv("TAVILY_API_KEY", "")
    return bool(key), key[:8] + "..." if key else "not set"


def doctor() -> None:
    """Display provider/tool readiness."""
    print_header("SYSTEM DOCTOR")

    print_section("LLM Gateway")
    info = gateway_info()
    print(f"  Fast routes: {info['fast_routes']}  |  Strong routes: {info['strong_routes']}")
    if info["routes"]:
        print()
        for r in info["routes"]:
            key_status = "key" if r["has_key"] else "free"
            print(f"  [{r['tier']}] {r['provider']}/{r['model']}  [{key_status}]")
    else:
        print("  No routes — check .env")

    from src.tools import get_registry
    print_section("Research Tools")
    registry = get_registry()
    for tool in registry.list_all():
        caps = ", ".join(sorted(tool.capabilities))
        free_paid = "free (no config)" if "free" in tool.capabilities else "needs API key"
        print(f"  {tool.name:<20} p={tool.priority:<4} {free_paid}")
        print(f"  {'':20}    [{caps}]")

    tavily_ok, preview = _check_tavily()
    if not tavily_ok:
        print(f"\n  💡 Tip: set TAVILY_API_KEY for comprehensive web search")

    print_section("Environment")
    import os
    for var in ["GROQ_API_KEY", "OPENAI_API_KEY", "OPENROUTER_API_KEY",
                "GEMINI_API_KEY", "ANTHROPIC_API_KEY", "DEEPSEEK_API_KEY",
                "NVIDIA_API_KEY", "CO_API_KEY"]:
        print(f"  {var:<25} {'set' if os.getenv(var) else '  -'}")

    print_section("Modes")
    print("  chat | quick | standard | deep | recency | academic | compare | ultra-long")
    print()


def chat(mode: str = "chat") -> None:
    """Start a chat session with conversation memory."""
    from src.engine.modes import load_modes, get_mode
    from src.rag.chat_memory import get_chat_memory, reset_chat_memory

    registry = load_modes()
    chat_mode = get_mode(registry, mode)
    memory = get_chat_memory()

    print_header(f"CHAT ({chat_mode.description})")
    print(f"  Budget: ${chat_mode.budgets.max_cost_usd:.2f} max")
    print(f"  Memory: {len(memory)} messages loaded")
    print("  /exit /doctor /research <topic> /clear")
    print()

    SYSTEM_PROMPT = (
        "You are a helpful, knowledgeable research assistant. "
        "Answer accurately and cite sources when possible. "
        "Be concise but thorough."
    )

    while True:
        try:
            user_input = input("  You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Goodbye!")
            break
        if not user_input:
            continue
        if user_input.lower() in ("/exit", "/quit", "/q"):
            print("  Goodbye!"); break
        if user_input.lower() == "/doctor":
            doctor(); continue
        if user_input.lower() == "/clear":
            reset_chat_memory()
            memory = get_chat_memory()
            print("  Memory cleared."); continue
        if user_input.lower().startswith("/research"):
            topic = user_input[len("/research"):].strip()
            if topic:
                print(f"  Escalating to research: {topic}")
                _run_research(topic)
            else:
                print("  Usage: /research <topic>")
            continue

        # Add user message to memory
        memory.add("user", user_input)
        messages = memory.build_context(SYSTEM_PROMPT)

        print("  ", end="", flush=True)
        try:
            response = call_llm(
                SYSTEM_PROMPT,
                user_input
            )
            print(f"Assistant: {response}\n")
            memory.add("assistant", response)
        except RuntimeError as e:
            print(f"\n  Error: {e}\n")


def _run_research(query: str, mode: str = "standard") -> None:
    """Run multi-agent research with progressive output display."""
    from src.engine.modes import load_modes, get_mode
    registry = load_modes()
    mode_config = get_mode(registry, mode)

    print_header(f"RESEARCH: {query}")
    print(f"  Mode: {mode} ({mode_config.description})")
    print(f"  Budget: {mode_config.budgets.max_iterations} iters, ${mode_config.budgets.max_cost_usd:.2f} max")
    start = time.time()

    try:
        result = run_research(query, mode=mode)
        elapsed = time.time() - start

        print_header("RESEARCH COMPLETE")
        print(f"  Time: {elapsed:.1f}s")
        print(f"  Iterations: {result.get('iteration', 0)}")
        print(f"  Findings: {len(result.get('findings', []))}")
        print(f"  Claims: {len(result.get('claims', []))}")
        print(f"  Sources tracked: {len(result.get('evidence_map', {}))}")
        print(f"  Report: {result.get('markdown_path', 'N/A')}")
        print()

        # Show section-by-section preview
        sections = result.get("sections", [])
        if sections:
            print("─" * 60)
            for s in sections:
                content = s.get("content", "")
                print(f"  ## {s['title']} ({len(content)} chars)")
            print("─" * 60)
            if sections:
                preview = sections[0].get("content", "")
                print(preview[:400])
                if len(preview) > 400:
                    print("...")
                print("─" * 60)
        else:
            # Fallback to legacy output
            preview = result.get("report", "")[:500]
            if preview:
                print("─" * 60)
                print(preview)
                print("...")
                print("─" * 60)

        # Save to memory
        save_search(
            query=query,
            search_queries=result.get("search_queries", []),
            report_path=result.get("markdown_path", ""),
            findings=result.get("findings", []),
        )

    except Exception as e:
        print(f"\n  Error: {e}")
        import traceback
        traceback.print_exc()


def show_history() -> None:
    """Display past searches."""
    print_header("PAST RESEARCHES")
    history = get_history(20)
    if not history:
        print("  No past searches found.")
    for entry in history:
        print(f"  {entry['timestamp']} — {entry['query']}")
        print(f"    Report: {entry.get('report_path', 'N/A')}")


def run_eval(suite: str = "all") -> None:
    """Run evaluation suites."""
    print_header(f"EVALUATION: {suite.upper()}")
    
    if suite == "component":
        evaluator = create_component_evaluator()
        suites = evaluator.run_all_component_suites()
    elif suite == "system":
        evaluator = create_system_evaluator()
        suites = evaluator.run_system_suites()
    elif suite == "all":
        evaluator = create_component_evaluator()
        component_suites = evaluator.run_all_component_suites()
        
        evaluator = create_system_evaluator()
        system_suites = evaluator.run_system_suites()
        
        suites = component_suites + system_suites
    else:
        print(f"  Unknown suite: {suite}")
        print("  Available: component, system, all")
        return
    
    print(f"  Running {len(suites)} evaluation suites...")
    print()
    
    total_passed = 0
    total_tests = 0
    
    for suite in suites:
        print(f"  Suite: {suite.name}")
        print(f"    Pass rate: {suite.pass_rate:.2%} ({suite.passed_count}/{suite.total_count})")
        
        for result in suite.results:
            status = "✅" if result.passed else "❌"
            print(f"    {status} {result.name}: {result.score:.2f} ({result.duration_seconds:.2f}s)")
        
        total_passed += suite.passed_count
        total_tests += suite.total_count
        print()
    
    overall_rate = total_passed / total_tests if total_tests > 0 else 0.0
    print(f"  Overall: {overall_rate:.2%} ({total_passed}/{total_tests})")
    print()
    
    if overall_rate < 0.8:
        print("  ⚠️  Warning: Overall pass rate below 80%")
    else:
        print("  ✅ All evaluations passed")


def print_usage() -> None:
    print("Autonomous Research Agent")
    print()
    print("Commands:")
    print('  uv run python main.py research "topic" [--mode MODE]')
    print("  uv run python main.py chat [--mode MODE]")
    print("  uv run python main.py doctor")
    print("  uv run python main.py eval [suite]")
    print("  uv run python main.py server")
    print("  uv run python main.py --history")
    print()
    print("Modes: chat | quick | standard | deep | recency | academic | compare | ultra-long")
    print()
    print("Eval suites: component | system | all")


def main() -> None:
    args = sys.argv[1:]

    if not args:
        print_usage()
        return

    if "--history" in args:
        show_history()
        return

    if args[0] == "doctor":
        doctor()
        return

    if args[0] == "eval":
        suite = "all"
        if len(args) > 1:
            suite = args[1]
        run_eval(suite)
        return

    if args[0] == "server":
        import uvicorn
        print("Starting web API server...")
        print("API docs: http://localhost:8000/docs")
        uvicorn.run(app, host="0.0.0.0", port=8000)
        return

    if args[0] == "chat":
        mode = "chat"
        if "--mode" in args:
            idx = args.index("--mode")
            if idx + 1 < len(args):
                mode = args[idx + 1]
        chat(mode=mode)
        return

    if args[0] == "research":
        remaining = args[1:]
    else:
        remaining = args

    mode = "standard"
    query_parts = []
    i = 0
    while i < len(remaining):
        if remaining[i] == "--mode" and i + 1 < len(remaining):
            mode = remaining[i + 1]
            i += 2
        else:
            query_parts.append(remaining[i])
            i += 1

    query = " ".join(query_parts)
    if not query:
        print("Error: Please provide a research topic.")
        print('Usage: uv run python main.py research "your topic" [--mode standard]')
        sys.exit(1)

    similar = find_similar(query)
    if similar:
        print_header("PAST SIMILAR RESEARCH FOUND")
        for s in similar:
            print(f"  {s['timestamp']} — {s['query']}")
            print(f"    Report: {s.get('report_path', 'N/A')}")
        print()

    _run_research(query, mode=mode)


if __name__ == "__main__":
    main()
