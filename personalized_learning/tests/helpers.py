"""Shared helpers for Personalized Learning agent test suites."""
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from uuid import uuid4
import httpx
from a2a.client import A2ACardResolver, ClientFactory, ClientConfig
from a2a.types import Message, Role, TaskArtifactUpdateEvent, TaskStatusUpdateEvent, TextPart


def _collect_text_from_parts(parts) -> list[str]:
    chunks = []
    for part in parts or []:
        text = getattr(part, "text", None)
        if not text and hasattr(part, "root"):
            text = getattr(part.root, "text", None)
        if not text and hasattr(part, "model_dump"):
            dumped = part.model_dump()
            if isinstance(dumped, dict):
                text = dumped.get("text")
        if text:
            chunks.append(str(text))
    return chunks


async def call_agent(base_url: str, user_input: str, timeout: int = 90) -> str:
    """Send a message to an A2A agent and return the full text response."""
    async with httpx.AsyncClient(timeout=timeout) as http:
        resolver   = A2ACardResolver(httpx_client=http, base_url=base_url)
        agent_card = await resolver.get_agent_card()
        client     = ClientFactory(ClientConfig(httpx_client=http)).create(agent_card)

        msg = Message(
            message_id=str(uuid4()),
            role=Role.user,
            parts=[TextPart(text=user_input)],
        )

        parts_collected = []
        async for response in client.send_message(msg):
            if isinstance(response, Message):
                parts_collected.extend(_collect_text_from_parts(response.parts))
                continue

            task, event = response
            if isinstance(event, TaskArtifactUpdateEvent):
                parts_collected.extend(_collect_text_from_parts(getattr(event.artifact, "parts", [])))
            elif isinstance(event, TaskStatusUpdateEvent) and event.status.message:
                parts_collected.extend(_collect_text_from_parts(getattr(event.status.message, "parts", [])))
            elif event is None and task.status.message:
                parts_collected.extend(_collect_text_from_parts(getattr(task.status.message, "parts", [])))

    return "\n".join(parts_collected)


async def call_agent_with_context(base_url: str, user_input: str,
                                  context_id: str, timeout: int = 90) -> str:
    """Send a message reusing an existing contextId for multi-turn conversation."""
    async with httpx.AsyncClient(timeout=timeout) as http:
        resolver   = A2ACardResolver(httpx_client=http, base_url=base_url)
        agent_card = await resolver.get_agent_card()
        client     = ClientFactory(ClientConfig(httpx_client=http)).create(agent_card)

        msg = Message(
            message_id=str(uuid4()),
            role=Role.user,
            context_id=context_id,
            parts=[TextPart(text=user_input)],
        )

        parts_collected = []
        async for response in client.send_message(msg):
            if isinstance(response, Message):
                parts_collected.extend(_collect_text_from_parts(response.parts))
                continue

            task, event = response
            if isinstance(event, TaskArtifactUpdateEvent):
                parts_collected.extend(_collect_text_from_parts(getattr(event.artifact, "parts", [])))
            elif isinstance(event, TaskStatusUpdateEvent) and event.status.message:
                parts_collected.extend(_collect_text_from_parts(getattr(event.status.message, "parts", [])))
            elif event is None and task.status.message:
                parts_collected.extend(_collect_text_from_parts(getattr(task.status.message, "parts", [])))
    return "\n".join(parts_collected)


async def server_is_up(url: str) -> bool:
    """Return True if the agent card endpoint at url responds with 200."""
    try:
        async with httpx.AsyncClient(timeout=5) as http:
            r = await http.get(f"{url}/.well-known/agent-card.json")
            return r.status_code == 200
    except Exception:
        return False
