import json
import os
import re
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


def _parse_score(text: str) -> tuple[int, int] | None:
    patterns = [
        r"(\d+)\s*out of\s*(\d+)",
        r"(\d+)\s*/\s*(\d+)",
        r"(\d+)\s*from\s*(\d+)",
    ]
    lower = text.lower()
    for pattern in patterns:
        match = re.search(pattern, lower)
        if match:
            return int(match.group(1)), int(match.group(2))
    return None


class AgentLogic:
    def __init__(self):
        self.mcp_url = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8004/mcp")
        self.mcp_client = Client(self.mcp_url)

    async def _call_tool_json(self, tool_name: str, args: dict) -> dict:
        async with self.mcp_client:
            result = await self.mcp_client.call_tool(tool_name, args)
            raw = result.content[0].text if result.content else "{}"
        return json.loads(raw)

    async def stream(self, user_input: str, history=None) -> AsyncGenerator:
        try:
            history_texts = []
            for msg in (history or []):
                for part in msg.parts:
                    text = _extract_part_text(part)
                    if text:
                        history_texts.append(text)

            full_context = " ".join(history_texts + [user_input])
            topic = _parse_topic(full_context)

            score = _parse_score(user_input)
            if score:
                correct_count, total_count = score
                update = await self._call_tool_json(
                    "update_learning_state",
                    {
                        "user_id": "user_1",
                        "topic": topic,
                        "correct_count": correct_count,
                        "total_count": total_count,
                    },
                )
                content = (
                    f"Your {topic} level update:\n"
                    f"- Previous level: {update.get('previous_level')}\n"
                    f"- New level: {update.get('new_level')}\n"
                    f"- Score: {correct_count}/{total_count}\n"
                    f"- {update.get('message', '')}"
                )
                yield {"completed": True, "failed": False, "input_required": False, "content": content}
                return

            lower_input = user_input.lower()
            is_level_query = (
                "what is my level" in lower_input
                or "current level" in lower_input
                or ("my current" in lower_input and "level" in lower_input)
                or "what level" in lower_input
            )
            if is_level_query:
                state = await self._call_tool_json("get_learning_state", {"user_id": "user_1", "topic": topic})
                content = f"Your current {topic} level is {state.get('current_level', 'beginner')}."
                yield {"completed": True, "failed": False, "input_required": False, "content": content}
                return

            state = await self._call_tool_json("get_learning_state", {"user_id": "user_1", "topic": topic})
            level = state.get("current_level", "beginner")
            questions = await self._call_tool_json(
                "get_assessment_questions_by_topic",
                {"topic": topic, "level": level, "limit": 4},
            )

            rows = [f"Assessment questions for {topic} ({level} level):"]
            for idx, q in enumerate(questions.get("questions", []), 1):
                rows.append(f"Question {idx}: {q.get('question', '')}")
            if len(rows) == 1:
                rows.append("No question available for this topic right now.")

            yield {"completed": True, "failed": False, "input_required": False, "content": "\n".join(rows)}

        except Exception as e:
            yield {"completed": False, "failed": True, "input_required": False, "content": f"Error in assessment_agent: {e}"}
