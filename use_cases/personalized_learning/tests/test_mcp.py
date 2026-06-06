"""
test_mcp.py  -  Direct tests for all 8 MCP tools on the FastMCP server.

Requires: MCP server running on http://127.0.0.1:8004/mcp
Run standalone: python tests/test_mcp.py
Or via master runner: python tests/run_all_tests.py
"""

import asyncio

import pytest
from fastmcp import Client

MCP_URL = "http://127.0.0.1:8004/mcp"

# ---------------------------------------------------------------------------
# Test definitions
# Each test: name, tool, args, expect_contains (case-insensitive substring)
# ---------------------------------------------------------------------------
TESTS = [
    # --- get_topic_summary ---
    {
        "name": "get_topic_summary - MCP beginner",
        "tool": "get_topic_summary",
        "args": {"topic": "mcp", "level": "beginner"},
        "expect_contains": "summary",
    },
    {
        "name": "get_topic_summary - A2A intermediate",
        "tool": "get_topic_summary",
        "args": {"topic": "a2a", "level": "intermediate"},
        "expect_contains": "key_concepts",
    },
    {
        "name": "get_topic_summary - RAG advanced",
        "tool": "get_topic_summary",
        "args": {"topic": "rag", "level": "advanced"},
        "expect_contains": "common_misconceptions",
    },
    {
        "name": "get_topic_summary - data_source is local_json",
        "tool": "get_topic_summary",
        "args": {"topic": "prompt_engineering", "level": "beginner"},
        "expect_contains": "local_json",
    },
    {
        "name": "get_topic_summary - unknown topic returns error",
        "tool": "get_topic_summary",
        "args": {"topic": "blockchain", "level": "beginner"},
        "expect_contains": "not found",
    },

    # --- get_assessment_questions_by_topic ---
    {
        "name": "get_assessment_questions - MCP beginner 4 questions",
        "tool": "get_assessment_questions_by_topic",
        "args": {"topic": "mcp", "level": "beginner", "limit": 4},
        "expect_contains": "questions",
    },
    {
        "name": "get_assessment_questions - A2A intermediate limit 2",
        "tool": "get_assessment_questions_by_topic",
        "args": {"topic": "a2a", "level": "intermediate", "limit": 2},
        "expect_contains": "question",
    },
    {
        "name": "get_assessment_questions - data_source is local_json",
        "tool": "get_assessment_questions_by_topic",
        "args": {"topic": "rag", "level": "beginner"},
        "expect_contains": "local_json",
    },
    {
        "name": "get_assessment_questions - unknown topic returns error",
        "tool": "get_assessment_questions_by_topic",
        "args": {"topic": "blockchain", "level": "beginner"},
        "expect_contains": "not found",
    },

    # --- get_learning_state ---
    {
        "name": "get_learning_state - user_1 MCP (seeded state)",
        "tool": "get_learning_state",
        "args": {"user_id": "user_1", "topic": "mcp"},
        "expect_contains": "current_level",
    },
    {
        "name": "get_learning_state - unknown user returns beginner default",
        "tool": "get_learning_state",
        "args": {"user_id": "unknown_user_xyz", "topic": "mcp"},
        "expect_contains": "beginner",
    },
    {
        "name": "get_learning_state - data_source is local_json",
        "tool": "get_learning_state",
        "args": {"user_id": "user_2", "topic": "a2a"},
        "expect_contains": "local_json",
    },

    # --- update_learning_state ---
    {
        "name": "update_learning_state - perfect score advances level",
        "tool": "update_learning_state",
        "args": {"user_id": "test_advance_user", "topic": "mcp",
                 "correct_count": 4, "total_count": 4},
        "expect_contains": "intermediate",
    },
    {
        "name": "update_learning_state - low score stays at level",
        "tool": "update_learning_state",
        "args": {"user_id": "test_stay_user", "topic": "a2a",
                 "correct_count": 2, "total_count": 4},
        "expect_contains": "beginner",
    },
    {
        "name": "update_learning_state - data_source is local_json",
        "tool": "update_learning_state",
        "args": {"user_id": "test_ds_user", "topic": "rag",
                 "correct_count": 3, "total_count": 4},
        "expect_contains": "local_json",
    },
    {
        "name": "update_learning_state - zero total_count returns error",
        "tool": "update_learning_state",
        "args": {"user_id": "user_1", "topic": "mcp",
                 "correct_count": 0, "total_count": 0},
        "expect_contains": "total_count",
    },

    # --- get_study_path ---
    {
        "name": "get_study_path - MCP beginner 2_hours",
        "tool": "get_study_path",
        "args": {"topic": "mcp", "level": "beginner", "available_time": "2_hours"},
        "expect_contains": "ordered_steps",
    },
    {
        "name": "get_study_path - RAG intermediate 30_minutes",
        "tool": "get_study_path",
        "args": {"topic": "rag", "level": "intermediate", "available_time": "30_minutes"},
        "expect_contains": "learning_objectives",
    },
    {
        "name": "get_study_path - python_async advanced 1_day",
        "tool": "get_study_path",
        "args": {"topic": "python_async", "level": "advanced", "available_time": "1_day"},
        "expect_contains": "practice_suggestions",
    },
    {
        "name": "get_study_path - data_source is local_json",
        "tool": "get_study_path",
        "args": {"topic": "a2a", "level": "beginner", "available_time": "2_hours"},
        "expect_contains": "local_json",
    },
    {
        "name": "get_study_path - unknown topic returns error",
        "tool": "get_study_path",
        "args": {"topic": "quantum_computing", "level": "beginner", "available_time": "2_hours"},
        "expect_contains": "not found",
    },

    # --- get_job_description ---
    {
        "name": "get_job_description - ai_engineer",
        "tool": "get_job_description",
        "args": {"job_id": "ai_engineer"},
        "expect_contains": "required_skills",
    },
    {
        "name": "get_job_description - data_scientist",
        "tool": "get_job_description",
        "args": {"job_id": "data_scientist"},
        "expect_contains": "data_scientist",
    },
    {
        "name": "get_job_description - data_source is local_json",
        "tool": "get_job_description",
        "args": {"job_id": "backend_engineer"},
        "expect_contains": "local_json",
    },
    {
        "name": "get_job_description - unknown job returns error",
        "tool": "get_job_description",
        "args": {"job_id": "astronaut"},
        "expect_contains": "not found",
    },

    # --- get_resume_profile ---
    {
        "name": "get_resume_profile - candidate_1",
        "tool": "get_resume_profile",
        "args": {"candidate_id": "candidate_1"},
        "expect_contains": "skills",
    },
    {
        "name": "get_resume_profile - candidate_2",
        "tool": "get_resume_profile",
        "args": {"candidate_id": "candidate_2"},
        "expect_contains": "current_role",
    },
    {
        "name": "get_resume_profile - data_source is local_json",
        "tool": "get_resume_profile",
        "args": {"candidate_id": "candidate_1"},
        "expect_contains": "local_json",
    },
    {
        "name": "get_resume_profile - unknown candidate returns error",
        "tool": "get_resume_profile",
        "args": {"candidate_id": "candidate_99"},
        "expect_contains": "not found",
    },

    # --- get_skill_gap_analysis ---
    {
        "name": "get_skill_gap_analysis - candidate_1 for ai_engineer",
        "tool": "get_skill_gap_analysis",
        "args": {"job_id": "ai_engineer", "candidate_id": "candidate_1"},
        "expect_contains": "missing_required_skills",
    },
    {
        "name": "get_skill_gap_analysis - recommended topics returned",
        "tool": "get_skill_gap_analysis",
        "args": {"job_id": "ai_engineer", "candidate_id": "candidate_1"},
        "expect_contains": "recommended_learning_topics",
    },
    {
        "name": "get_skill_gap_analysis - matched_skills present",
        "tool": "get_skill_gap_analysis",
        "args": {"job_id": "backend_engineer", "candidate_id": "candidate_1"},
        "expect_contains": "matched_skills",
    },
    {
        "name": "get_skill_gap_analysis - data_source is local_json",
        "tool": "get_skill_gap_analysis",
        "args": {"job_id": "data_scientist", "candidate_id": "candidate_2"},
        "expect_contains": "local_json",
    },
    {
        "name": "get_skill_gap_analysis - unknown job returns error",
        "tool": "get_skill_gap_analysis",
        "args": {"job_id": "astronaut", "candidate_id": "candidate_1"},
        "expect_contains": "not found",
    },
    {
        "name": "get_skill_gap_analysis - unknown candidate returns error",
        "tool": "get_skill_gap_analysis",
        "args": {"job_id": "ai_engineer", "candidate_id": "candidate_99"},
        "expect_contains": "not found",
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
