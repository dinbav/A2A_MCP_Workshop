"""
test_e2e.py  -  End-to-end flow tests for the Personalized Learning use case.

Tests all 5 orchestrator flows:
  Flow 1: Topic Explanation
  Flow 2: Assessment
  Flow 3: Study Plan
  Flow 4: Full Learning Flow (explain + assess + plan)
  Flow 5: Career Learning Flow

Run standalone: python tests/test_e2e.py
Or via master runner: python tests/run_all_tests.py --only e2e
"""

import asyncio
import sys
import os

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import call_agent, server_is_up

ORCHESTRATOR_URL    = "http://localhost:8090"
TOPIC_EXPLAINER_URL = "http://localhost:8091"
ASSESSMENT_URL      = "http://localhost:8092"
STUDY_PLAN_URL      = "http://localhost:8093"
MCP_URL             = "http://127.0.0.1:8004/mcp"

# ---------------------------------------------------------------------------
# Flow tests
# ---------------------------------------------------------------------------

E2E_TESTS = [
    # --- Flow 1: Topic Explanation ---
    {
        "name": "E2E Flow 1 - Explain MCP beginner (direct)",
        "url": TOPIC_EXPLAINER_URL,
        "message": "Explain MCP for a beginner.",
        "expect_contains": ["mcp", "key concept"],
        "section": "E2E Flows",
    },
    {
        "name": "E2E Flow 1 - Explain A2A intermediate (via orchestrator)",
        "url": ORCHESTRATOR_URL,
        "message": "Explain A2A for an intermediate developer.",
        "expect_contains": ["a2a"],
        "section": "E2E Flows",
    },

    # --- Flow 2: Assessment ---
    {
        "name": "E2E Flow 2 - Assessment quiz MCP (direct)",
        "url": ASSESSMENT_URL,
        "message": "Give me a 4-question quiz for MCP at beginner level.",
        "expect_contains": ["question", "mcp"],
        "section": "E2E Flows",
    },
    {
        "name": "E2E Flow 2 - Assessment via orchestrator",
        "url": ORCHESTRATOR_URL,
        "message": "Quiz me on RAG.",
        "expect_contains": ["rag"],
        "section": "E2E Flows",
    },

    # --- Flow 3: Study Plan ---
    {
        "name": "E2E Flow 3 - Study plan for MCP 2 hours (direct)",
        "url": STUDY_PLAN_URL,
        "message": "Build me a 2-hour study plan for MCP at beginner level.",
        "expect_contains": ["step", "mcp"],
        "section": "E2E Flows",
    },
    {
        "name": "E2E Flow 3 - Study plan via orchestrator",
        "url": ORCHESTRATOR_URL,
        "message": "Create a beginner study plan for A2A in 30 minutes.",
        "expect_contains": ["a2a"],
        "section": "E2E Flows",
    },

    # --- Flow 4: Full Learning Flow ---
    {
        "name": "E2E Flow 4 - Full flow: explain + assess + plan",
        "url": ORCHESTRATOR_URL,
        "message": "I want to learn MCP. Assess my level and build me a 2-hour study plan.",
        "expect_contains": ["mcp"],
        "section": "E2E Flows",
    },

    # --- Flow 5: Career Learning Flow ---
    {
        "name": "E2E Flow 5 - Career flow candidate_1 ai_engineer",
        "url": ORCHESTRATOR_URL,
        "message": "Prepare a learning plan for candidate_1 for the AI Engineer role.",
        "expect_contains": ["learning", "plan"],
        "section": "E2E Flows",
    },
    {
        "name": "E2E Flow 5 - Career flow candidate_2 data_scientist",
        "url": STUDY_PLAN_URL,
        "message": "Prepare a learning plan for candidate_2 for the data_scientist role.",
        "expect_contains": ["learning"],
        "section": "E2E Flows",
    },
]

# ---------------------------------------------------------------------------
# Offline guarantee tests (MCP tools only — no LLM needed)
# ---------------------------------------------------------------------------
OFFLINE_TESTS = [
    {
        "name": "Offline - get_topic_summary data_source is local_json",
        "tool": "get_topic_summary",
        "args": {"topic": "mcp", "level": "beginner"},
        "expect": "local_json",
        "section": "Offline Guarantees",
    },
    {
        "name": "Offline - get_study_path data_source is local_json",
        "tool": "get_study_path",
        "args": {"topic": "a2a", "level": "intermediate", "available_time": "2_hours"},
        "expect": "local_json",
        "section": "Offline Guarantees",
    },
    {
        "name": "Offline - get_skill_gap_analysis data_source is local_json",
        "tool": "get_skill_gap_analysis",
        "args": {"job_id": "ai_engineer", "candidate_id": "candidate_1"},
        "expect": "local_json",
        "section": "Offline Guarantees",
    },
    {
        "name": "Offline - get_assessment_questions data_source is local_json",
        "tool": "get_assessment_questions_by_topic",
        "args": {"topic": "rag", "level": "beginner"},
        "expect": "local_json",
        "section": "Offline Guarantees",
    },
    {
        "name": "Offline - get_learning_state data_source is local_json",
        "tool": "get_learning_state",
        "args": {"user_id": "user_1", "topic": "mcp"},
        "expect": "local_json",
        "section": "Offline Guarantees",
    },
]


# ---------------------------------------------------------------------------
# Pytest-compatible tests
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("test_case", E2E_TESTS, ids=[t["name"] for t in E2E_TESTS])
async def test_e2e_flow(test_case):
    if not await server_is_up(test_case["url"]):
        pytest.skip(f"Server not reachable at {test_case['url']}")
    response = await call_agent(test_case["url"], test_case["message"])
    missing = [kw for kw in test_case.get("expect_contains", []) if kw.lower() not in response.lower()]
    assert not missing, f"Missing keywords {missing} in response:\n{response[:500]}"


@pytest.mark.parametrize("test_case", OFFLINE_TESTS, ids=[t["name"] for t in OFFLINE_TESTS])
async def test_offline_guarantee(test_case):
    from fastmcp import Client
    try:
        async with Client(MCP_URL) as client:
            await client.ping()
    except Exception as e:
        pytest.skip(f"MCP server not reachable at {MCP_URL}: {e}")

    async with Client(MCP_URL) as client:
        tool_result = await client.call_tool(test_case["tool"], test_case["args"])
        raw = tool_result.content[0].text if tool_result.content else ""
        expect = test_case.get("expect", "")
        if expect:
            assert expect.lower() in raw.lower(), (
                f"Expected '{expect}' not found in response.\nGot: {raw[:300]}"
            )


async def run_e2e_tests() -> list[dict]:
    from fastmcp import Client
    results = []

    for test in E2E_TESTS:
        result = {
            "name": test["name"],
            "passed": False,
            "response": "",
            "error": "",
            "section": test["section"],
        }
        try:
            print(f"  [...] {test['name']}", end="", flush=True)
            up = await server_is_up(test["url"])
            if not up:
                result["error"] = f"Server not reachable at {test['url']}"
                print(f"\r  [FAIL] {test['name']}")
                results.append(result)
                continue

            response_text = await call_agent(test["url"], test["message"])
            result["response"] = response_text[:500]

            keywords = test.get("expect_contains", [])
            missing = [kw for kw in keywords if kw.lower() not in response_text.lower()]

            if not missing:
                result["passed"] = True
                print(f"\r  [PASS] {test['name']}")
            else:
                result["error"] = f"Missing keywords: {missing}"
                print(f"\r  [FAIL] {test['name']}")
                print(f"         Missing: {missing}")

        except Exception as e:
            result["error"] = str(e)
            print(f"\r  [FAIL] {test['name']}")
            print(f"         Error: {str(e)[:120]}")

        results.append(result)

    return results


async def run_offline_tests() -> list[dict]:
    from fastmcp import Client
    results = []

    try:
        async with Client(MCP_URL) as client:
            await client.ping()
    except Exception as e:
        return [{"name": "MCP offline connectivity", "passed": False,
                 "response": "", "error": str(e), "section": "Offline Guarantees"}]

    async with Client(MCP_URL) as client:
        for test in OFFLINE_TESTS:
            result = {
                "name": test["name"],
                "passed": False,
                "response": "",
                "error": "",
                "section": test["section"],
            }
            try:
                tool_result = await client.call_tool(test["tool"], test["args"])
                raw = tool_result.content[0].text if tool_result.content else ""
                result["response"] = raw[:200]
                if test["expect"].lower() in raw.lower():
                    result["passed"] = True
                else:
                    result["error"] = f"Expected '{test['expect']}' in response"
            except Exception as e:
                result["error"] = str(e)
            results.append(result)

    return results


if __name__ == "__main__":
    async def _main():
        print(f"\n  E2E Flow Tests  (Orchestrator: {ORCHESTRATOR_URL})")
        print("  " + "=" * 55)
        e2e_results = await run_e2e_tests()
        p = sum(1 for r in e2e_results if r["passed"])
        print(f"\n  E2E: {p}/{len(e2e_results)} passed")

        print(f"\n  Offline Guarantee Tests  (MCP: {MCP_URL})")
        print("  " + "=" * 55)
        offline_results = await run_offline_tests()
        for r in offline_results:
            icon = "PASS" if r["passed"] else "FAIL"
            print(f"  [{icon}] {r['name']}")
        p2 = sum(1 for r in offline_results if r["passed"])
        print(f"\n  Offline: {p2}/{len(offline_results)} passed\n")

    asyncio.run(_main())
