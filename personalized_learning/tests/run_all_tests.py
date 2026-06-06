"""
run_all_tests.py  -  Master test runner for the Personalized Learning Workshop.

Runs all tests in order and prints a consolidated report.

Usage:
  python tests/run_all_tests.py                     # all tests
  python tests/run_all_tests.py --skip-agents       # MCP tools only (fast)
  python tests/run_all_tests.py --skip-mcp          # agents only
  python tests/run_all_tests.py --only mcp          # one group only
  python tests/run_all_tests.py --only topic
  python tests/run_all_tests.py --only assessment
  python tests/run_all_tests.py --only study
  python tests/run_all_tests.py --only orchestrator
  python tests/run_all_tests.py --only e2e
  python tests/run_all_tests.py --only memory
  python tests/run_all_tests.py --verbose           # show full responses

Run from the use case root:
  cd use_cases/personalized_learning
  python tests/run_all_tests.py
"""

import asyncio
import argparse
import sys
import os
import time
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_mcp import run_tests as run_mcp_tests
from tests.test_agents import (
    run_topic_explainer_tests,
    run_assessment_tests,
    run_study_plan_tests,
    run_orchestrator_tests,
)
from tests.test_e2e import run_e2e_tests, run_offline_tests
from tests.test_memory import run_memory_tests

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
    if len(name) > 52:
        name = name[:49] + "..."
    print(f"  [{icon}] {name}")
    if not result["passed"]:
        err = result.get("error", "")[:100]
        print(f"         -> {err}")
    if verbose and result.get("response"):
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
    parser = argparse.ArgumentParser(description="Personalized Learning Workshop - Test Runner")
    parser.add_argument("--skip-mcp",    action="store_true", help="Skip MCP tool tests")
    parser.add_argument("--skip-agents", action="store_true", help="Skip all agent tests")
    parser.add_argument(
        "--only",
        choices=["mcp", "topic", "assessment", "study", "orchestrator", "e2e", "offline", "memory"],
        help="Run only this test group",
    )
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show full response text for each test")
    args = parser.parse_args()

    start_time = time.time()
    all_results: list[dict] = []

    print()
    print(_header("Personalized Learning - Test Suite"))
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(_line("="))

    # ------------------------------------------------------------------ MCP
    run_mcp = not args.skip_mcp and (args.only is None or args.only == "mcp")
    if run_mcp:
        print()
        print(_header("MCP Tools  (port 8004)"))
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

    # ------------------------------------------------------ Topic Explainer
    run_topic = not args.skip_agents and (args.only is None or args.only == "topic")
    if run_topic:
        print()
        print(_header("Topic Explainer Agent  (port 8091)"))
        print(_line())
        t0 = time.time()
        results = await run_topic_explainer_tests()
        elapsed = time.time() - t0
        for r in results:
            _print_result_row(r, args.verbose)
        p, total = _section_summary(results)
        print(_line())
        print(f"  Topic Explainer: {p}/{total} passed  ({elapsed:.1f}s)")
        all_results.extend(results)

    # ---------------------------------------------------------- Assessment
    run_assess = not args.skip_agents and (args.only is None or args.only == "assessment")
    if run_assess:
        print()
        print(_header("Assessment Agent  (port 8092)"))
        print(_line())
        t0 = time.time()
        results = await run_assessment_tests()
        elapsed = time.time() - t0
        for r in results:
            _print_result_row(r, args.verbose)
        p, total = _section_summary(results)
        print(_line())
        print(f"  Assessment: {p}/{total} passed  ({elapsed:.1f}s)")
        all_results.extend(results)

    # ---------------------------------------------------------- Study Plan
    run_study = not args.skip_agents and (args.only is None or args.only == "study")
    if run_study:
        print()
        print(_header("Study Plan Agent  (port 8093)"))
        print(_line())
        t0 = time.time()
        results = await run_study_plan_tests()
        elapsed = time.time() - t0
        for r in results:
            _print_result_row(r, args.verbose)
        p, total = _section_summary(results)
        print(_line())
        print(f"  Study Plan: {p}/{total} passed  ({elapsed:.1f}s)")
        all_results.extend(results)

    # --------------------------------------------------------- Orchestrator
    run_orch = not args.skip_agents and (args.only is None or args.only == "orchestrator")
    if run_orch:
        print()
        print(_header("Orchestrator Agent  (port 8090)"))
        print(_line())
        t0 = time.time()
        results = await run_orchestrator_tests()
        elapsed = time.time() - t0
        for r in results:
            _print_result_row(r, args.verbose)
        p, total = _section_summary(results)
        print(_line())
        print(f"  Orchestrator: {p}/{total} passed  ({elapsed:.1f}s)")
        all_results.extend(results)

    # --------------------------------------------------------------- E2E
    run_e2e = not args.skip_agents and (args.only is None or args.only == "e2e")
    if run_e2e:
        print()
        print(_header("End-to-End Flows"))
        print(_line())
        t0 = time.time()
        results = await run_e2e_tests()
        elapsed = time.time() - t0
        for r in results:
            _print_result_row(r, args.verbose)
        p, total = _section_summary(results)
        print(_line())
        print(f"  E2E Flows: {p}/{total} passed  ({elapsed:.1f}s)")
        all_results.extend(results)

    # ------------------------------------------------------------ Offline
    run_offline = not args.skip_mcp and (args.only is None or args.only == "offline")
    if run_offline:
        print()
        print(_header("Offline Guarantees  (MCP: port 8004)"))
        print(_line())
        t0 = time.time()
        results = await run_offline_tests()
        elapsed = time.time() - t0
        for r in results:
            _print_result_row(r, args.verbose)
        p, total = _section_summary(results)
        print(_line())
        print(f"  Offline Guarantees: {p}/{total} passed  ({elapsed:.1f}s)")
        all_results.extend(results)

    # ----------------------------------------------------------- Memory
    run_memory = not args.skip_agents and (args.only is None or args.only == "memory")
    if run_memory:
        print()
        print(_header("Multi-Turn Memory  (port 8090)"))
        print(_line())
        t0 = time.time()
        results = await run_memory_tests()
        elapsed = time.time() - t0
        for r in results:
            _print_result_row(r, args.verbose)
        p, total = _section_summary(results)
        print(_line())
        print(f"  Memory: {p}/{total} passed  ({elapsed:.1f}s)")
        all_results.extend(results)

    # -------------------------------------------------------- Final summary
    total_elapsed = time.time() - start_time
    total_passed = sum(1 for r in all_results if r["passed"])
    total_failed = len(all_results) - total_passed

    print()
    print(_line("="))
    print(_header("FINAL SUMMARY"))
    print(_line("="))
    print()

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

    sys.exit(0 if total_failed == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
