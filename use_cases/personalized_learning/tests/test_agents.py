"""
test_agents.py  -  Conversation tests for all A2A agents.

Ports:
  Topic Explainer Agent  -> http://localhost:8091
  Assessment Agent       -> http://localhost:8092
  Study Plan Agent       -> http://localhost:8093
  Orchestrator Agent     -> http://localhost:8090

Run standalone: python tests/test_agents.py
Or via master runner: python tests/run_all_tests.py
"""

import asyncio
import sys
import os

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import call_agent, server_is_up

TIMEOUT = 90

# ---------------------------------------------------------------------------
# Agent URLs
# ---------------------------------------------------------------------------
TOPIC_EXPLAINER_URL = "http://localhost:8091"
ASSESSMENT_URL      = "http://localhost:8092"
STUDY_PLAN_URL      = "http://localhost:8093"
ORCHESTRATOR_URL    = "http://localhost:8090"

# ---------------------------------------------------------------------------
# Conversation scenarios per agent
# ---------------------------------------------------------------------------
TOPIC_EXPLAINER_TESTS = [
    {
        "name": "TopicExplainer - MCP beginner",
        "message": "Explain MCP for a beginner.",
        "expect_contains": ["mcp", "key concepts"],
    },
    {
        "name": "TopicExplainer - A2A intermediate",
        "message": "Explain A2A for an intermediate developer.",
        "expect_contains": ["a2a", "intermediate"],
    },
    {
        "name": "TopicExplainer - RAG overview",
        "message": "What are the key concepts in RAG?",
        "expect_contains": ["rag", "key concept"],
    },
    {
        "name": "TopicExplainer - Python async beginner",
        "message": "What is Python async programming?",
        "expect_contains": ["async", "coroutine"],
    },
    {
        "name": "TopicExplainer - Prompt engineering advanced",
        "message": "Give me an advanced overview of prompt engineering.",
        "expect_contains": ["prompt", "advanced"],
    },
]

ASSESSMENT_TESTS = [
    {
        "name": "Assessment - Quiz for MCP",
        "message": "Give me a short quiz for MCP.",
        "expect_contains": ["question", "mcp"],
    },
    {
        "name": "Assessment - What is my level in A2A",
        "message": "What is my current A2A level?",
        "expect_contains": ["level", "a2a"],
    },
    {
        "name": "Assessment - Assess RAG knowledge",
        "message": "Test my knowledge of RAG at beginner level.",
        "expect_contains": ["question", "rag"],
    },
    {
        "name": "Assessment - Quiz prompt engineering",
        "message": "Quiz me on prompt engineering.",
        "expect_contains": ["question", "prompt"],
    },
]

STUDY_PLAN_TESTS = [
    {
        "name": "StudyPlan - 2-hour MCP plan",
        "message": "Build me a 2-hour study plan for MCP.",
        "expect_contains": ["step", "mcp"],
    },
    {
        "name": "StudyPlan - beginner A2A plan",
        "message": "Create a beginner study plan for A2A.",
        "expect_contains": ["step", "a2a"],
    },
    {
        "name": "StudyPlan - 30-minute RAG plan",
        "message": "I have 30 minutes. What should I study for RAG?",
        "expect_contains": ["rag"],
    },
    {
        "name": "StudyPlan - Career plan candidate_1 ai_engineer",
        "message": "Prepare a learning plan for candidate_1 for the AI Engineer role.",
        "expect_contains": ["learning", "plan"],
    },
    {
        "name": "StudyPlan - 1-day prompt engineering",
        "message": "Give me a 1-day study plan for prompt engineering.",
        "expect_contains": ["prompt", "step"],
    },
]

ORCHESTRATOR_TESTS = [
    {
        "name": "Orchestrator - Route to TopicExplainer",
        "message": "Explain MCP for a complete beginner.",
        "expect_contains": ["mcp"],
        "expected_agent": "topic_explainer",
    },
    {
        "name": "Orchestrator - Route to Assessment",
        "message": "Quiz me on A2A.",
        "expect_contains": ["a2a"],
        "expected_agent": "assessment",
    },
    {
        "name": "Orchestrator - Route to StudyPlan",
        "message": "Build me a 2-hour study plan for RAG.",
        "expect_contains": ["rag"],
        "expected_agent": "study_plan",
    },
    {
        "name": "Orchestrator - Career learning flow",
        "message": "Prepare a learning plan for candidate_1 for the AI Engineer role.",
        "expect_contains": ["learning", "plan"],
        "expected_agent": "study_plan",
    },
    {
        "name": "Orchestrator - Full learning flow (explain + assess + plan)",
        "message": "I want to learn MCP. Assess my level and build me a 2-hour study plan.",
        "expect_contains": ["mcp"],
        "expected_agent": "multi",
    },
]


# ---------------------------------------------------------------------------
# Pytest-compatible tests
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("test_case", TOPIC_EXPLAINER_TESTS, ids=[t["name"] for t in TOPIC_EXPLAINER_TESTS])
async def test_topic_explainer(test_case):
    if not await server_is_up(TOPIC_EXPLAINER_URL):
        pytest.skip(f"Topic Explainer not reachable at {TOPIC_EXPLAINER_URL}")
    response = await call_agent(TOPIC_EXPLAINER_URL, test_case["message"], timeout=TIMEOUT)
    missing = [kw for kw in test_case.get("expect_contains", []) if kw.lower() not in response.lower()]
    assert not missing, f"Missing keywords {missing} in response:\n{response[:500]}"


@pytest.mark.parametrize("test_case", ASSESSMENT_TESTS, ids=[t["name"] for t in ASSESSMENT_TESTS])
async def test_assessment_agent(test_case):
    if not await server_is_up(ASSESSMENT_URL):
        pytest.skip(f"Assessment Agent not reachable at {ASSESSMENT_URL}")
    response = await call_agent(ASSESSMENT_URL, test_case["message"], timeout=TIMEOUT)
    missing = [kw for kw in test_case.get("expect_contains", []) if kw.lower() not in response.lower()]
    assert not missing, f"Missing keywords {missing} in response:\n{response[:500]}"


@pytest.mark.parametrize("test_case", STUDY_PLAN_TESTS, ids=[t["name"] for t in STUDY_PLAN_TESTS])
async def test_study_plan_agent(test_case):
    if not await server_is_up(STUDY_PLAN_URL):
        pytest.skip(f"Study Plan Agent not reachable at {STUDY_PLAN_URL}")
    response = await call_agent(STUDY_PLAN_URL, test_case["message"], timeout=TIMEOUT)
    missing = [kw for kw in test_case.get("expect_contains", []) if kw.lower() not in response.lower()]
    assert not missing, f"Missing keywords {missing} in response:\n{response[:500]}"


@pytest.mark.parametrize("test_case", ORCHESTRATOR_TESTS, ids=[t["name"] for t in ORCHESTRATOR_TESTS])
async def test_orchestrator_agent(test_case):
    if not await server_is_up(ORCHESTRATOR_URL):
        pytest.skip(f"Orchestrator not reachable at {ORCHESTRATOR_URL}")
    response = await call_agent(ORCHESTRATOR_URL, test_case["message"], timeout=TIMEOUT)
    missing = [kw for kw in test_case.get("expect_contains", []) if kw.lower() not in response.lower()]
    assert not missing, f"Missing keywords {missing} in response:\n{response[:500]}"


# ---------------------------------------------------------------------------
# Generic test runner
# ---------------------------------------------------------------------------
async def run_scenario_tests(
    url: str,
    tests: list[dict],
    section: str,
    print_live: bool = True,
) -> list[dict]:
    results = []

    up = await server_is_up(url)
    if not up:
        print(f"  [ERROR] Server not reachable at {url}")
        for t in tests:
            results.append({
                "name": t["name"],
                "passed": False,
                "response": "",
                "error": f"Server not reachable at {url}",
                "section": section,
            })
        return results

    for test in tests:
        result = {
            "name": test["name"],
            "passed": False,
            "response": "",
            "error": "",
            "section": section,
        }
        try:
            if print_live:
                print(f"  [...] {test['name']}", end="", flush=True)

            response_text = await call_agent(url, test["message"])
            result["response"] = response_text[:500]

            keywords = test.get("expect_contains", [])
            missing = [kw for kw in keywords
                       if kw.lower() not in response_text.lower()]

            if not missing:
                result["passed"] = True
                if print_live:
                    print(f"\r  [PASS] {test['name']}")
            else:
                result["error"] = f"Missing keywords: {missing}"
                if print_live:
                    print(f"\r  [FAIL] {test['name']}")
                    print(f"         Missing: {missing}")

        except Exception as e:
            result["error"] = str(e)
            if print_live:
                print(f"\r  [FAIL] {test['name']}")
                print(f"         Error: {str(e)[:120]}")

        results.append(result)

    return results


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------
async def run_topic_explainer_tests() -> list[dict]:
    return await run_scenario_tests(TOPIC_EXPLAINER_URL, TOPIC_EXPLAINER_TESTS, "Topic Explainer Agent")


async def run_assessment_tests() -> list[dict]:
    return await run_scenario_tests(ASSESSMENT_URL, ASSESSMENT_TESTS, "Assessment Agent")


async def run_study_plan_tests() -> list[dict]:
    return await run_scenario_tests(STUDY_PLAN_URL, STUDY_PLAN_TESTS, "Study Plan Agent")


async def run_orchestrator_tests() -> list[dict]:
    return await run_scenario_tests(ORCHESTRATOR_URL, ORCHESTRATOR_TESTS, "Orchestrator Agent")


# ---------------------------------------------------------------------------
# Standalone runner
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run A2A agent conversation tests")
    parser.add_argument("--agent",
                        choices=["topic", "assessment", "study", "orchestrator", "all"],
                        default="all", help="Which agent to test (default: all)")
    args = parser.parse_args()

    async def _main():
        all_results = []

        if args.agent in ("topic", "all"):
            print(f"\n  Topic Explainer Agent Tests  ({TOPIC_EXPLAINER_URL})")
            print("  " + "=" * 55)
            all_results += await run_topic_explainer_tests()

        if args.agent in ("assessment", "all"):
            print(f"\n  Assessment Agent Tests  ({ASSESSMENT_URL})")
            print("  " + "=" * 55)
            all_results += await run_assessment_tests()

        if args.agent in ("study", "all"):
            print(f"\n  Study Plan Agent Tests  ({STUDY_PLAN_URL})")
            print("  " + "=" * 55)
            all_results += await run_study_plan_tests()

        if args.agent in ("orchestrator", "all"):
            print(f"\n  Orchestrator Agent Tests  ({ORCHESTRATOR_URL})")
            print("  " + "=" * 55)
            all_results += await run_orchestrator_tests()

        passed = sum(1 for r in all_results if r["passed"])
        print(f"\n  Total: {passed}/{len(all_results)} passed\n")

    asyncio.run(_main())
