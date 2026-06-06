"""
test_mcp.py  -  Direct tests for all MCP tools on the FastMCP server.

Requires: MCP server running on http://127.0.0.1:8003/mcp
Run standalone: python tests/test_mcp.py
Or via master runner: python tests/run_all_tests.py
"""

import asyncio
import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp"))

from fastmcp import Client

MCP_URL = "http://127.0.0.1:8003/mcp"

# ---------------------------------------------------------------------------
# Test definitions
# Each test: name, tool, args, expect_contains (case-insensitive substring)
# ---------------------------------------------------------------------------
TESTS = [
    # --- greet ---
    {
        "name": "greet - Hello Alice",
        "tool": "greet",
        "args": {"name": "Alice"},
        "expect_contains": "Hello, Alice",
    },
    {
        "name": "greet - Hello World",
        "tool": "greet",
        "args": {"name": "World"},
        "expect_contains": "Hello, World",
    },

    # --- suggest_activities_for_location_and_date ---
    {
        "name": "suggest_activities - no params (general list)",
        "tool": "suggest_activities_for_location_and_date",
        "args": {},
        "expect_contains": "suggested_activities",
    },
    {
        "name": "suggest_activities - indoor preference",
        "tool": "suggest_activities_for_location_and_date",
        "args": {"preference": "indoor"},
        "expect_contains": "Indoor activity",
    },
    {
        "name": "suggest_activities - outdoor preference",
        "tool": "suggest_activities_for_location_and_date",
        "args": {"preference": "outdoor"},
        "expect_contains": "Outdoor activity",
    },

    # --- get_weather_for_location_and_date_string ---
    {
        "name": "get_weather - Tel Aviv today",
        "tool": "get_weather_for_location_and_date_string",
        "args": {"location_str": "Tel Aviv, Israel", "date_str": "today"},
        "expect_contains": "temperature_range",
    },
    {
        "name": "get_weather - London this weekend",
        "tool": "get_weather_for_location_and_date_string",
        "args": {"location_str": "London, UK", "date_str": "this weekend"},
        "expect_contains": "date_range",
    },
    {
        "name": "get_weather - Paris next week",
        "tool": "get_weather_for_location_and_date_string",
        "args": {"location_str": "Paris, France", "date_str": "next week"},
        "expect_contains": "location",
    },
]


# ---------------------------------------------------------------------------
# Pytest-compatible tests (parametrized so each TESTS entry is a separate item)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("test_case", TESTS, ids=[t["name"] for t in TESTS])
async def test_mcp_tool(test_case):
    try:
        async with Client(MCP_URL) as client:
            await client.ping()
    except Exception as e:
        pytest.skip(f"MCP server not reachable at {MCP_URL}: {e}")

    async with Client(MCP_URL) as client:
        tool_result = await client.call_tool(test_case["tool"], test_case["args"])
        raw = tool_result.content[0].text if tool_result.content else ""
        expect = test_case.get("expect_contains", "")
        if expect:
            assert expect.lower() in raw.lower(), (
                f"Expected '{expect}' not found in response.\nGot: {raw[:300]}"
            )


# ---------------------------------------------------------------------------
# Runner (standalone execution: python tests/test_mcp.py)
# ---------------------------------------------------------------------------
async def run_tests() -> list[dict]:
    results = []

    try:
        async with Client(MCP_URL) as client:
            await client.ping()
    except Exception as e:
        print(f"  [ERROR] MCP server not reachable at {MCP_URL}: {e}")
        return [{"name": "MCP connectivity", "passed": False,
                 "response": "", "error": str(e), "section": "MCP Tools"}]

    async with Client(MCP_URL) as client:
        for test in TESTS:
            result = {
                "name": test["name"],
                "passed": False,
                "response": "",
                "error": "",
                "section": "MCP Tools",
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


if __name__ == "__main__":
    async def _main():
        print(f"\n  MCP Tool Tests  ({MCP_URL})")
        print("  " + "=" * 55)
        res = await run_tests()
        for r in res:
            icon = "PASS" if r["passed"] else "FAIL"
            print(f"  [{icon}] {r['name']}")
            if not r["passed"]:
                print(f"         -> {r['error']}")
        passed = sum(1 for r in res if r["passed"])
        print(f"\n  Result: {passed}/{len(res)} passed\n")

    asyncio.run(_main())
