"""
run_all_tests.py  -  Master test runner for the A2A MCP Workshop.

Runs all tests in order and prints a consolidated report.

Usage:
  python tests/run_all_tests.py                     # all tests
  python tests/run_all_tests.py --skip-agents       # MCP tools only (fast)
  python tests/run_all_tests.py --skip-mcp          # agents only
  python tests/run_all_tests.py --only orchestrator # one agent only
  python tests/run_all_tests.py --verbose           # show full responses

Run from the workshop root directory:
  cd C:\\Users\\dinab\\PycharmProjects\\a2a_mcp_workshop
  python tests/run_all_tests.py
"""

import asyncio
import argparse
import sys
import os
import time
from datetime import datetime

# Ensure UTF-8 output on Windows (avoids charmap errors with emoji from LLM responses)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Make sure imports resolve from the project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_mcp import run_tests as run_mcp_tests
from tests.test_agents import (
    run_packing_tests,
    run_weather_tests,
    run_orchestrator_tests,
)
from tests.test_local_tips import (
    run_local_tips_mcp_tests,
    run_local_tips_agent_tests,
)

# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------
WIDTH = 65

def _line(char="-"):
    return "  " + char * WIDTH

def _header(title):
    pad = (WIDTH - len(title) - 2) // 2
    return "  " + "=" * pad + " " + title + " " + "=" * (WIDTH - pad - len(title) - 1)

def _print_result_row(result: dict, verbose: bool = False):
    icon = "PASS" if result["passed"] else "FAIL"
    name = result["name"]
    # Truncate long names
    if len(name) > 52:
        name = name[:49] + "..."
    print(f"  [{icon}] {name}")
    if not result["passed"]:
        err = result.get("error", "")[:100]
        print(f"         -> {err}")
    if verbose and result.get("response"):
        # Print first 300 chars of response indented
        resp = result["response"][:300].replace("\n", "\n           ")
        print(f"         Response: {resp}")
        print()

def _section_summary(results: list[dict]) -> tuple[int, int]:
    passed = sum(1 for r in results if r["passed"])
    return passed, len(results)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
async def main():
    parser = argparse.ArgumentParser(description="A2A MCP Workshop - Test Runner")
    parser.add_argument("--skip-mcp",    action="store_true", help="Skip MCP tool tests")
    parser.add_argument("--skip-agents", action="store_true", help="Skip all agent tests")
    parser.add_argument("--only",
                        choices=["mcp", "packing", "weather", "orchestrator", "local-tips"],
                        help="Run only this test group")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show full response text for each test")
    args = parser.parse_args()

    start_time = time.time()
    all_results: list[dict] = []

    print()
    print(_header("A2A MCP Workshop - Test Suite"))
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(_line("="))

    # ------------------------------------------------------------------ MCP
    run_mcp = not args.skip_mcp and (args.only is None or args.only == "mcp")
    if run_mcp:
        print()
        print(_header("MCP Tools  (port 8003)"))
        print(_line())
        t0 = time.time()
        mcp_results = await run_mcp_tests()
        elapsed = time.time() - t0
        for r in mcp_results:
            _print_result_row(r, args.verbose)
        p, total = _section_summary(mcp_results)
        print(_line())
        print(f"  MCP Tools: {p}/{total} passed  ({elapsed:.1f}s)")
        all_results.extend(mcp_results)

    # ---------------------------------------------------------- Packing Agent
    run_packing = not args.skip_agents and (args.only is None or args.only == "packing")
    if run_packing:
        print()
        print(_header("Packing List Agent  (port 8081)"))
        print(_line())
        t0 = time.time()
        packing_results = await run_packing_tests()
        elapsed = time.time() - t0
        for r in packing_results:
            _print_result_row(r, args.verbose)
        p, total = _section_summary(packing_results)
        print(_line())
        print(f"  Packing Agent: {p}/{total} passed  ({elapsed:.1f}s)")
        all_results.extend(packing_results)

    # ---------------------------------------------------------- Weather Agent
    run_weather = not args.skip_agents and (args.only is None or args.only == "weather")
    if run_weather:
        print()
        print(_header("Weather & Activity Agent  (port 8082)"))
        print(_line())
        t0 = time.time()
        weather_results = await run_weather_tests()
        elapsed = time.time() - t0
        for r in weather_results:
            _print_result_row(r, args.verbose)
        p, total = _section_summary(weather_results)
        print(_line())
        print(f"  Weather Agent: {p}/{total} passed  ({elapsed:.1f}s)")
        all_results.extend(weather_results)

    # ------------------------------------------------------- Orchestrator
    run_orch = not args.skip_agents and (args.only is None or args.only == "orchestrator")
    if run_orch:
        print()
        print(_header("Orchestrator Agent  (port 8080)"))
        print(_line())
        t0 = time.time()
        orch_results = await run_orchestrator_tests()
        elapsed = time.time() - t0
        for r in orch_results:
            _print_result_row(r, args.verbose)
        p, total = _section_summary(orch_results)
        print(_line())
        print(f"  Orchestrator: {p}/{total} passed  ({elapsed:.1f}s)")
        all_results.extend(orch_results)

    # ------------------------------------------------------- Local Tips
    run_local = args.only is None or args.only == "local-tips"
    if run_local:
        # MCP tool tests (always fast)
        if not args.skip_mcp:
            print()
            print(_header("Local Tips MCP Tool  (port 8003)"))
            print(_line())
            t0 = time.time()
            lt_mcp_results = await run_local_tips_mcp_tests()
            elapsed = time.time() - t0
            for r in lt_mcp_results:
                _print_result_row(r, args.verbose)
            p, total = _section_summary(lt_mcp_results)
            print(_line())
            print(f"  Local Tips MCP: {p}/{total} passed  ({elapsed:.1f}s)")
            all_results.extend(lt_mcp_results)

        # Agent + orchestrator tests
        if not args.skip_agents:
            print()
            print(_header("Local Tips Agent  (port 8083)"))
            print(_line())
            t0 = time.time()
            lt_agent_results = await run_local_tips_agent_tests()
            elapsed = time.time() - t0
            for r in lt_agent_results:
                _print_result_row(r, args.verbose)
            p, total = _section_summary(lt_agent_results)
            print(_line())
            print(f"  Local Tips Agent: {p}/{total} passed  ({elapsed:.1f}s)")
            all_results.extend(lt_agent_results)

    # ---------------------------------------------------------- Final summary
    total_elapsed = time.time() - start_time
    total_passed = sum(1 for r in all_results if r["passed"])
    total_failed = len(all_results) - total_passed

    print()
    print(_line("="))
    print(_header("FINAL SUMMARY"))
    print(_line("="))
    print()

    # Group by section for the summary table
    sections: dict[str, list] = {}
    for r in all_results:
        sec = r.get("section", "Other")
        sections.setdefault(sec, []).append(r)

    col_w = 35
    print(f"  {'Section':<{col_w}}  {'Passed':>6}  {'Failed':>6}  {'Total':>6}")
    print("  " + "-" * (col_w + 22))
    for sec, res in sections.items():
        p = sum(1 for r in res if r["passed"])
        f = len(res) - p
        status = "" if f == 0 else "  <-- FAILURES"
        print(f"  {sec:<{col_w}}  {p:>6}  {f:>6}  {len(res):>6}{status}")
    print("  " + "-" * (col_w + 22))
    print(f"  {'TOTAL':<{col_w}}  {total_passed:>6}  {total_failed:>6}  {len(all_results):>6}")
    print()

    if total_failed > 0:
        print("  Failed tests:")
        for r in all_results:
            if not r["passed"]:
                err = r.get("error", "")[:80]
                print(f"    - [{r['section']}] {r['name']}")
                print(f"        {err}")
        print()

    pct = int(100 * total_passed / len(all_results)) if all_results else 0
    overall = "ALL PASSED" if total_failed == 0 else f"{total_failed} FAILED"
    print(f"  Result: {overall}  ({pct}%  |  {total_elapsed:.1f}s)")
    print()
    print(_line("="))
    print()

    # Exit code: 0 = all pass, 1 = some fail
    sys.exit(0 if total_failed == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
