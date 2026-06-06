"""
test_local_tips.py  -  Tests for the Local Tips extension.

Sections:
  1. MCP tool direct     - calls get_local_tips_by_city via FastMCP (port 8003)
  2. Agent direct        - Local Tips Agent (port 8083)
  3. Agent via Orchestrator (port 8080)

Run standalone: python tests/test_local_tips.py
Or via master runner: python tests/run_all_tests.py --only local-tips
"""

import asyncio
import sys

from fastmcp import Client
from tests.helpers import call_agent, server_is_up

MCP_URL          = "http://127.0.0.1:8003/mcp"
LOCAL_TIPS_URL   = "http://localhost:8083"
ORCHESTRATOR_URL = "http://localhost:8080"
TIMEOUT          = 30  # no LLM calls, so 30s is plenty


# ---------------------------------------------------------------------------
# Section 1: MCP Tool direct tests
# ---------------------------------------------------------------------------
MCP_TESTS = [
    {
        "name": "MCP - Tel Aviv family trip",
        "tool": "get_local_tips_by_city",
        "args": {"city": "Tel Aviv", "trip_type": "family"},
        "expect_contains": "transportation",
    },
    {
        "name": "MCP - Paris cultural trip",
        "tool": "get_local_tips_by_city",
        "args": {"city": "Paris", "trip_type": "cultural"},
        "expect_contains": "food",
    },
    {
        "name": "MCP - Barcelona beach trip",
        "tool": "get_local_tips_by_city",
        "args": {"city": "Barcelona", "trip_type": "beach"},
        "expect_contains": "safety",
    },
    {
        "name": "MCP - Rome general trip",
        "tool": "get_local_tips_by_city",
        "args": {"city": "Rome", "trip_type": "general"},
        "expect_contains": "recommended_hours",
    },
    {
        "name": "MCP - London adventure trip",
        "tool": "get_local_tips_by_city",
        "args": {"city": "London", "trip_type": "adventure"},
        "expect_contains": "local_highlights",
    },
    {
        "name": "MCP - unknown city returns not found",
        "tool": "get_local_tips_by_city",
        "args": {"city": "Atlantis", "trip_type": "general"},
        "expect_contains": "No tips found",
    },
]


async def run_local_tips_mcp_tests() -> list[dict]:
    results = []

    try:
        async with Client(MCP_URL) as client:
            await client.ping()
    except Exception as e:
        return [{"name": "MCP connectivity", "passed": False,
                 "response": "", "error": str(e), "section": "Local Tips MCP Tool"}]

    async with Client(MCP_URL) as client:
        for test in MCP_TESTS:
            result = {
                "name": test["name"],
                "passed": False,
                "response": "",
                "error": "",
                "section": "Local Tips MCP Tool",
            }
            try:
                tool_result = await client.call_tool(test["tool"], test["args"])
                raw = tool_result.content[0].text if tool_result.content else ""
                result["response"] = raw[:300]

                expect = test.get("expect_contains", "")
                if not expect or expect.lower() in raw.lower():
                    result["passed"] = True
                else:
                    result["error"] = f"Expected '{expect}' not found in response"

            except Exception as e:
                result["error"] = str(e)

            results.append(result)

    return results


# ---------------------------------------------------------------------------
# Section 2 & 3: Agent conversation tests
# ---------------------------------------------------------------------------
LOCAL_TIPS_AGENT_TESTS = [
    {
        "name": "Agent - Tel Aviv family tips",
        "message": "Give me local tips for Tel Aviv for a family trip",
        "expect_contains": ["tel aviv", "transportation"],
    },
    {
        "name": "Agent - Paris cultural tips",
        "message": "What are the local tips for a Paris cultural visit?",
        "expect_contains": ["paris", "food"],
    },
    {
        "name": "Agent - Barcelona beach tips",
        "message": "Local tips for a Barcelona beach trip",
        "expect_contains": ["barcelona", "safety"],
    },
]

ORCHESTRATOR_TESTS = [
    {
        "name": "Orchestrator - routes to Local Tips Agent",
        "message": "Give me local tips for Barcelona beach trip",
        "expect_contains": ["barcelona", "tips"],
    },
    {
        "name": "Orchestrator - local city guide for London",
        "message": "I need a local city guide for London, romantic trip",
        "expect_contains": ["london"],
    },
]


async def _run_agent_tests(url: str, tests: list[dict], section: str) -> list[dict]:
    results = []

    up = await server_is_up(url)
    if not up:
        for t in tests:
            results.append({
                "name": t["name"], "passed": False, "response": "",
                "error": f"Server not reachable at {url}", "section": section,
            })
        return results

    for test in tests:
        result = {"name": test["name"], "passed": False, "response": "",
                  "error": "", "section": section}
        try:
            print(f"  [...] {test['name']}", end="", flush=True)
            response_text = await call_agent(url, test["message"])
            result["response"] = response_text[:500]

            keywords = test.get("expect_contains", [])
            missing  = [kw for kw in keywords if kw.lower() not in response_text.lower()]

            if not missing:
                result["passed"] = True
                print(f"\r  [PASS] {test['name']}")
            else:
                result["error"] = f"Missing keywords: {missing}"
                print(f"\r  [FAIL] {test['name']}  (missing: {missing})")

        except Exception as e:
            result["error"] = str(e)
            print(f"\r  [FAIL] {test['name']}  ({str(e)[:80]})")

        results.append(result)

    return results


async def run_local_tips_agent_tests() -> list[dict]:
    agent_results = await _run_agent_tests(
        LOCAL_TIPS_URL, LOCAL_TIPS_AGENT_TESTS, "Local Tips Agent"
    )
    orch_results = await _run_agent_tests(
        ORCHESTRATOR_URL, ORCHESTRATOR_TESTS, "Local Tips via Orchestrator"
    )
    return agent_results + orch_results


# ---------------------------------------------------------------------------
# Standalone runner
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    async def _main():
        print(f"\n  Local Tips MCP Tool Tests  ({MCP_URL})")
        print("  " + "=" * 55)
        mcp_res = await run_local_tips_mcp_tests()
        for r in mcp_res:
            icon = "PASS" if r["passed"] else "FAIL"
            print(f"  [{icon}] {r['name']}")
            if not r["passed"]:
                print(f"         -> {r['error']}")
        p = sum(1 for r in mcp_res if r["passed"])
        print(f"\n  Result: {p}/{len(mcp_res)} passed\n")

        print(f"  Local Tips Agent Tests  ({LOCAL_TIPS_URL})")
        print("  " + "=" * 55)
        agent_res = await run_local_tips_agent_tests()
        for r in agent_res:
            if not r["passed"]:  # already printed by _run_agent_tests
                pass
        p = sum(1 for r in agent_res if r["passed"])
        print(f"\n  Result: {p}/{len(agent_res)} passed\n")

    asyncio.run(_main())
