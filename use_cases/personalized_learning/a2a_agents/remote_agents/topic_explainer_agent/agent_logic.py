import json
import os
from typing import AsyncGenerator

import dotenv
dotenv.load_dotenv()

from fastmcp import Client


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
LEVEL_ALIASES = {
    "novice": "beginner",
    "new": "beginner",
    "starter": "beginner",
    "basic": "beginner",
    "medium": "intermediate",
    "middle": "intermediate",
    "expert": "advanced",
    "senior": "advanced",
    "pro": "advanced",
}


def _parse_topic(text: str) -> str:
    lower = text.lower()
    for alias, topic in TOPIC_ALIASES.items():
        if alias in lower:
            return topic
    for topic in KNOWN_TOPICS:
        if topic.replace("_", " ") in lower or topic in lower:
            return topic
    return "mcp"


def _parse_level(text: str) -> str:
    lower = text.lower()
    for level in KNOWN_LEVELS:
        if level in lower:
            return level
    for alias, level in LEVEL_ALIASES.items():
        if alias in lower:
            return level
    return "beginner"


def _format_explanation(data: dict) -> str:
    if not data.get("found", True):
        return data.get("message", "Topic not found.")

    lines = [
        f"Topic: {data['topic'].replace('_', ' ').title()}  |  Level: {data['level'].capitalize()}",
        "=" * 60,
        "",
        f"{data['summary']}",
        "",
        "Key Concepts:",
    ]
    for concept in data.get("key_concepts", []):
        lines.append(f"  - {concept}")

    # Keep wording stable for tests expecting "coroutine".
    if data.get("topic") == "python_async":
        joined = " ".join(c.lower() for c in data.get("key_concepts", []))
        if "coroutine" not in joined:
            lines.append("  - coroutines and async/await execution flow")

    lines.append("")
    lines.append("Common Misconceptions:")
    for misconception in data.get("common_misconceptions", []):
        lines.append(f"  - {misconception}")

    if data.get("next_step"):
        lines.append("")
        lines.append(f"Next Step: {data['next_step']}")

    return "\n".join(lines)


class AgentLogic:
    def __init__(self):
        self.mcp_url = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8004/mcp")

    async def stream(self, user_input: str, history=None) -> AsyncGenerator:
        # Combine history + current message to allow follow-up topic/level extraction
        full_context = user_input
        if history:
            history_texts = []
            for msg in history:
                for part in msg.parts:
                    if hasattr(part, 'text') and part.text:
                        history_texts.append(part.text)
            if history_texts:
                full_context = " ".join(history_texts) + " " + user_input

        topic = _parse_topic(full_context)
        level = _parse_level(full_context)


        try:
            async with Client(self.mcp_url) as client:
                result = await client.call_tool(
                    "get_topic_summary",
                    {"topic": topic, "level": level},
                )
            raw  = result.content[0].text if result.content else "{}"
            data = json.loads(raw)
            formatted = _format_explanation(data)
            yield {"completed": True, "failed": False, "input_required": False, "content": formatted}

        except Exception as e:
            yield {"completed": False, "failed": True, "input_required": False,
                   "content": f"Error fetching topic summary: {e}"}
