# MULTI-TURN MEMORY TEST
# Run with: python -m tests.test_memory
# Requires all agents running (start_all.ps1)
#
# Tests that context_id threads conversation history across turns so that
# follow-up messages do not need to repeat the topic.
#
# Scenario:
#   Turn 1: "I want to learn MCP. I am a beginner."
#   Turn 2: "Assess me."            <-- agent should know topic=MCP
#   Turn 3: "I got 3 out of 4."    <-- agent should know topic=MCP, update level, advance
#   Turn 4: "Build me a plan for 2 hours."  <-- study plan agent should use MCP

import asyncio
import sys
import os
import pytest
from uuid import uuid4

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from helpers import call_agent_with_context, server_is_up

ORCHESTRATOR_URL = "http://localhost:8090"

CONVERSATION = [
    "I want to learn MCP. I am a complete beginner.",
    "Assess me on MCP.",
    "I got 3 out of 4 correct.",
    "Build me a 2-hour study plan based on my current level.",
]

EXPECTED_KEYWORDS_PER_TURN = [
    ["mcp"],
    ["question", "mcp"],
    ["intermediate"],          # 3/4 = 75% — meets threshold (>= 0.75), advances to intermediate
    ["step", "mcp"],
]


# ---------------------------------------------------------------------------
# Pytest-compatible test
# ---------------------------------------------------------------------------
async def test_memory_multi_turn():
    if not await server_is_up(ORCHESTRATOR_URL):
        pytest.skip(f"Orchestrator not reachable at {ORCHESTRATOR_URL}")

    ctx_id = str(uuid4())
    for i, (user_input, expected) in enumerate(zip(CONVERSATION, EXPECTED_KEYWORDS_PER_TURN), 1):
        response = await call_agent_with_context(ORCHESTRATOR_URL, user_input, context_id=ctx_id)
        missing = [kw for kw in expected if kw.lower() not in response.lower()]
        assert not missing, (
            f"Turn {i}: Missing keywords {missing} in response.\n"
            f"Input: {user_input!r}\nResponse: {response}"
        )


async def run_memory_tests() -> list[dict]:
    """Return test results in the standard run_all_tests format."""
    results = []
    if not await server_is_up(ORCHESTRATOR_URL):
        return [{"name": "Multi-turn memory (4 turns)", "passed": False,
                 "error": f"Orchestrator not reachable at {ORCHESTRATOR_URL}",
                 "section": "Memory", "response": ""}]

    ctx_id = str(uuid4())
    for i, (user_input, expected) in enumerate(zip(CONVERSATION, EXPECTED_KEYWORDS_PER_TURN), 1):
        try:
            response = await call_agent_with_context(ORCHESTRATOR_URL, user_input, context_id=ctx_id)
            missing = [kw for kw in expected if kw.lower() not in response.lower()]
            results.append({
                "name": f"Turn {i}: {user_input}",
                "passed": not missing,
                "error": f"Missing keywords: {missing}" if missing else "",
                "section": "Memory",
                "response": response,
            })
        except Exception as e:
            results.append({
                "name": f"Turn {i}: {user_input}",
                "passed": False,
                "error": str(e),
                "section": "Memory",
                "response": "",
            })
    return results


async def main():
    ctx_id = str(uuid4())
    print(f"\nMemory / Multi-Turn Test")
    print(f"Context ID: {ctx_id[:8]}...")
    print("=" * 60)

    for i, user_input in enumerate(CONVERSATION, 1):
        print(f"\nTurn {i} — User: {user_input}")
        response = await call_agent_with_context(
            ORCHESTRATOR_URL, user_input, context_id=ctx_id
        )
        print(f"Turn {i} — Agent: {response}")
        print("-" * 40)

    print("\n[Done]\n")


if __name__ == "__main__":
    asyncio.run(main())
