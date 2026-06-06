import json
import os
from typing import AsyncGenerator

import dotenv
from fastmcp import Client

dotenv.load_dotenv()

KNOWN_TOPICS = ["mcp", "a2a", "rag", "prompt_engineering", "python_async"]
TOPIC_ALIASES = {
    "model context protocol": "mcp",
    "agent to agent": "a2a",
    "agent-to-agent": "a2a",
    "retrieval augmented generation": "rag",
    "retrieval-augmented generation": "rag",
    "prompt": "prompt_engineering",
    "prompting": "prompt_engineering",
    "async": "python_async",
    "asyncio": "python_async",
    "asynchronous": "python_async",
}
KNOWN_LEVELS = ["beginner", "intermediate", "advanced"]
KNOWN_JOBS = ["ai_engineer", "data_scientist", "backend_engineer"]
KNOWN_CANDIDATES = ["candidate_1", "candidate_2"]


def _extract_part_text(part) -> str:
    text = getattr(part, "text", None)
    if not text and hasattr(part, "root"):
        text = getattr(part.root, "text", None)
    if not text and hasattr(part, "model_dump"):
        dumped = part.model_dump()
        if isinstance(dumped, dict):
            text = dumped.get("text")
    return str(text or "")


def _parse_topic(text: str) -> str:
    lower = text.lower()
    for alias, topic in TOPIC_ALIASES.items():
        if alias in lower:
            return topic
    for topic in KNOWN_TOPICS:
        if topic in lower or topic.replace("_", " ") in lower:
            return topic
    return "mcp"


def _parse_level(text: str) -> str | None:
    lower = text.lower()
    for level in KNOWN_LEVELS:
        if level in lower:
            return level
    return None


def _parse_time_slot(text: str) -> str:
    lower = text.lower()
    if "30 minute" in lower or "30-minute" in lower or "half hour" in lower:
        return "30_minutes"
    if "1 day" in lower or "one day" in lower or "full day" in lower:
        return "1_day"
    if "2 hour" in lower or "two hour" in lower:
        return "2_hours"
    return "2_hours"


def _parse_job_candidate(text: str) -> tuple[str | None, str | None]:
    lower = text.lower().replace(" ", "_")
    job = next((j for j in KNOWN_JOBS if j in lower), None)
    candidate = next((c for c in KNOWN_CANDIDATES if c in lower), None)
    return job, candidate


class AgentLogic:
    def __init__(self):
        self.mcp_url = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8004/mcp")
        self.mcp_client = Client(self.mcp_url)

    async def _call_tool_json(self, tool_name: str, args: dict) -> dict:
        async with self.mcp_client:
            result = await self.mcp_client.call_tool(tool_name, args)
            raw = result.content[0].text if result.content else "{}"
        return json.loads(raw)

    async def _build_topic_plan(self, topic: str, user_input: str) -> str:
        level = _parse_level(user_input)
        if not level:
            state = await self._call_tool_json("get_learning_state", {"user_id": "user_1", "topic": topic})
            level = state.get("current_level", "beginner")

        plan = await self._call_tool_json(
            "get_study_path",
            {"topic": topic, "level": level, "available_time": _parse_time_slot(user_input)},
        )

        lines = [f"Learning plan for {topic} ({level}):"]
        for i, step in enumerate(plan.get("ordered_steps", []), 1):
            lines.append(f"Step {i}: {step}")
        if not plan.get("ordered_steps"):
            lines.append("Step 1: Review the topic fundamentals and practice examples.")
        return "\n".join(lines)

    async def _build_career_plan(self, job: str, candidate: str) -> str:
        gap = await self._call_tool_json("get_skill_gap_analysis", {"job_id": job, "candidate_id": candidate})
        topics = gap.get("recommended_learning_topics", [])[:3] or ["mcp"]
        lines = [f"Career learning plan for {candidate} -> {job}:"]

        for topic in topics:
            plan = await self._call_tool_json(
                "get_study_path",
                {"topic": topic, "level": "beginner", "available_time": "2_hours"},
            )
            lines.append(f"\nTopic: {topic}")
            for i, step in enumerate(plan.get("ordered_steps", [])[:3], 1):
                lines.append(f"Step {i}: {step}")

        return "\n".join(lines)

    async def stream(self, user_input: str, history=None) -> AsyncGenerator:
        try:
            history_texts = []
            for msg in (history or []):
                for part in msg.parts:
                    text = _extract_part_text(part)
                    if text:
                        history_texts.append(text)

            full_context = " ".join(history_texts + [user_input])
            job, candidate = _parse_job_candidate(full_context)
            if job and candidate:
                content = await self._build_career_plan(job, candidate)
                yield {"completed": True, "failed": False, "input_required": False, "content": content}
                return

            topic = _parse_topic(full_context)
            content = await self._build_topic_plan(topic, full_context)
            yield {"completed": True, "failed": False, "input_required": False, "content": content}

        except Exception as e:
            yield {"completed": False, "failed": True, "input_required": False, "content": f"Error in study_plan_agent: {e}"}
