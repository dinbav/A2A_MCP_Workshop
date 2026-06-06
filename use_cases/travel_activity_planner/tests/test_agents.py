"""
test_agents.py  -  Conversation tests for all A2A agents.

Ports:
  Packing List Agent     -> http://localhost:8081
  Weather/Activity Agent -> http://localhost:8082
  Orchestrator Agent     -> http://localhost:8080

Run standalone: python tests/test_agents.py
Or via master runner: python tests/run_all_tests.py
"""

import asyncio

from tests.helpers import call_agent, server_is_up

TIMEOUT = 90

# ---------------------------------------------------------------------------
# Agent URLs
# ---------------------------------------------------------------------------
PACKING_URL     = "http://localhost:8081"
WEATHER_URL     = "http://localhost:8082"
ORCHESTRATOR_URL = "http://localhost:8080"

# ---------------------------------------------------------------------------
# Conversation scenarios per agent
# ---------------------------------------------------------------------------
PACKING_TESTS = [
    {
        "name": "Packing - Beach trip for 2 adults",
        "message": "I'm going on a 3-day beach trip to Tel Aviv with my partner. "
                   "What should I pack?",
        "expect_contains": ["pack", "clothes", "sunscreen"],
    },
    {
        "name": "Packing - Ski trip in the Alps",
        "message": "We're going skiing in the Alps next weekend. "
                   "Create a packing list for 4 adults.",
        "expect_contains": ["gloves", "jacket", "ski"],
    },
    {
        "name": "Packing - Family trip with kids invitation",
        "message": "Write an invitation for a family trip to Paris for 2 adults and 2 kids, "
                   "happening next month for 5 days.",
        "expect_contains": ["paris", "invite"],
    },
    {
        "name": "Packing - Camping weekend",
        "message": "Weekend camping trip in the Galilee for 6 people. "
                   "Give me a full packing list.",
        "expect_contains": ["tent", "sleeping"],
    },
]

WEATHER_TESTS = [
    {
        "name": "Weather - Current weather in Tel Aviv",
        "message": "What is the weather like in Tel Aviv today?",
        "expect_contains": ["tel aviv", "temperature"],
    },
    {
        "name": "Weather - Weekend activities in London",
        "message": "What activities do you suggest for London this weekend?",
        "expect_contains": ["london", "activities"],
    },
    {
        "name": "Weather - Outdoor vs indoor for Berlin",
        "message": "Is it a good day for outdoor activities in Berlin? "
                   "If not, suggest indoor alternatives.",
        "expect_contains": ["berlin", "indoor"],
    },
    {
        "name": "Weather - Next week forecast New York",
        "message": "What will the weather be like in New York next week and "
                   "what should I do there?",
        "expect_contains": ["new york", "weather"],
    },
]

ORCHESTRATOR_TESTS = [
    {
        "name": "Orchestrator - Route to Packing agent",
        "message": "I need a packing list for a trip to Rome for 2 people for 4 days.",
        "expect_contains": ["pack"],
        "expected_agent": "packing",
    },
    {
        "name": "Orchestrator - Route to Weather agent",
        "message": "What is the weather forecast for Paris this weekend?",
        "expect_contains": ["weather", "paris"],
        "expected_agent": "weather",
    },
    {
        "name": "Orchestrator - Route to both agents (weather + packing)",
        "message": "I'm planning a trip to Barcelona next weekend. "
                   "What is the weather and what should I pack?",
        "expect_contains": ["barcelona"],
        "expected_agent": "both",
    },
    {
        "name": "Orchestrator - Activity suggestions via Weather agent",
        "message": "Suggest outdoor activities for Amsterdam today.",
        "expect_contains": ["amsterdam", "activities"],
        "expected_agent": "weather",
    },
]

# ---------------------------------------------------------------------------
# Generic test runner for a list of scenario tests
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

            # Check all expected keywords (case-insensitive)
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
# Public entry points (called by run_all_tests.py)
# ---------------------------------------------------------------------------
async def run_packing_tests() -> list[dict]:
    return await run_scenario_tests(PACKING_URL, PACKING_TESTS, "Packing List Agent")


async def run_weather_tests() -> list[dict]:
    return await run_scenario_tests(WEATHER_URL, WEATHER_TESTS, "Weather & Activity Agent")


async def run_orchestrator_tests() -> list[dict]:
    return await run_scenario_tests(ORCHESTRATOR_URL, ORCHESTRATOR_TESTS, "Orchestrator Agent")


# ---------------------------------------------------------------------------
# Standalone runner
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run A2A agent conversation tests")
    parser.add_argument("--agent", choices=["packing", "weather", "orchestrator", "all"],
                        default="all", help="Which agent to test (default: all)")
    args = parser.parse_args()

    async def _main():
        all_results = []

        if args.agent in ("packing", "all"):
            print(f"\n  Packing List Agent Tests  ({PACKING_URL})")
            print("  " + "=" * 55)
            all_results += await run_packing_tests()

        if args.agent in ("weather", "all"):
            print(f"\n  Weather & Activity Agent Tests  ({WEATHER_URL})")
            print("  " + "=" * 55)
            all_results += await run_weather_tests()

        if args.agent in ("orchestrator", "all"):
            print(f"\n  Orchestrator Agent Tests  ({ORCHESTRATOR_URL})")
            print("  " + "=" * 55)
            all_results += await run_orchestrator_tests()

        passed = sum(1 for r in all_results if r["passed"])
        print(f"\n  Total: {passed}/{len(all_results)} passed\n")

    asyncio.run(_main())
