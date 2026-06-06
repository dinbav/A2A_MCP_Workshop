"""
fastmcp_client.py  -  Example async client demonstrating all MCP tools.

Usage:
    python mcp/fastmcp_client.py

Requires MCP server running: python mcp/fastmcp_server.py
"""

import asyncio
import json
from fastmcp import Client

MCP_URL = "http://127.0.0.1:8004/mcp"


async def main():
    print(f"\nPersonalized Learning MCP Client Demo")
    print(f"Server: {MCP_URL}")
    print("=" * 55)

    async with Client(MCP_URL) as client:
        await client.ping()
        print("\n[OK] Connected to MCP server\n")

        tools = await client.list_tools()
        print(f"Available tools ({len(tools)}):")
        for t in tools:
            print(f"  - {t.name}")

        print("\n" + "-" * 55)

        # 1. get_topic_summary
        print("\n[1] get_topic_summary(topic='mcp', level='beginner')")
        r = await client.call_tool("get_topic_summary", {"topic": "mcp", "level": "beginner"})
        data = json.loads(r.content[0].text)
        print(f"  Summary: {data['summary'][:100]}...")
        print(f"  Key concepts: {len(data['key_concepts'])} items")
        print(f"  data_source: {data['data_source']}")

        # 2. get_assessment_questions_by_topic
        print("\n[2] get_assessment_questions_by_topic(topic='mcp', level='beginner', limit=2)")
        r = await client.call_tool("get_assessment_questions_by_topic",
                                   {"topic": "mcp", "level": "beginner", "limit": 2})
        data = json.loads(r.content[0].text)
        print(f"  Questions returned: {len(data['questions'])}")
        print(f"  First question: {data['questions'][0]['question'][:80]}...")

        # 3. get_learning_state
        print("\n[3] get_learning_state(user_id='user_1', topic='mcp')")
        r = await client.call_tool("get_learning_state", {"user_id": "user_1", "topic": "mcp"})
        data = json.loads(r.content[0].text)
        print(f"  Level: {data['current_level']}")
        print(f"  Correct: {data['correct_answers']} / {data['total_answers']}")

        # 4. update_learning_state
        print("\n[4] update_learning_state(user_id='demo_user', topic='a2a', correct_count=4, total_count=4)")
        r = await client.call_tool("update_learning_state",
                                   {"user_id": "demo_user", "topic": "a2a",
                                    "correct_count": 4, "total_count": 4})
        data = json.loads(r.content[0].text)
        print(f"  Previous level: {data['previous_level']}")
        print(f"  New level: {data['new_level']}")
        print(f"  Score: {data['score']}")
        print(f"  Message: {data['message']}")

        # 5. get_study_path
        print("\n[5] get_study_path(topic='rag', level='beginner', available_time='2_hours')")
        r = await client.call_tool("get_study_path",
                                   {"topic": "rag", "level": "beginner", "available_time": "2_hours"})
        data = json.loads(r.content[0].text)
        print(f"  Steps: {len(data['ordered_steps'])}")
        print(f"  Objectives: {data['learning_objectives'][:2]}")
        print(f"  Estimated time: {data['estimated_total_time']}")

        # 6. get_job_description
        print("\n[6] get_job_description(job_id='ai_engineer')")
        r = await client.call_tool("get_job_description", {"job_id": "ai_engineer"})
        data = json.loads(r.content[0].text)
        print(f"  Title: {data['title']}")
        print(f"  Required skills: {data['required_skills']}")

        # 7. get_resume_profile
        print("\n[7] get_resume_profile(candidate_id='candidate_1')")
        r = await client.call_tool("get_resume_profile", {"candidate_id": "candidate_1"})
        data = json.loads(r.content[0].text)
        print(f"  Name: {data['name']}")
        print(f"  Skills: {data['skills']}")

        # 8. get_skill_gap_analysis
        print("\n[8] get_skill_gap_analysis(job_id='ai_engineer', candidate_id='candidate_1')")
        r = await client.call_tool("get_skill_gap_analysis",
                                   {"job_id": "ai_engineer", "candidate_id": "candidate_1"})
        data = json.loads(r.content[0].text)
        print(f"  Matched: {data['matched_skills']}")
        print(f"  Missing required: {data['missing_required_skills']}")
        print(f"  Learning topics: {data['recommended_learning_topics']}")

        print("\n" + "=" * 55)
        print("All tools exercised successfully.\n")


if __name__ == "__main__":
    asyncio.run(main())
