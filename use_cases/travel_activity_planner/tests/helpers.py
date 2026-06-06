"""Shared helpers for A2A agent test suites."""
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from uuid import uuid4
import httpx
from a2a.client import A2ACardResolver, ClientFactory, ClientConfig
from a2a.types import (
    Message, Part, TextPart, Role,
    TaskArtifactUpdateEvent,
)


def _part_text(p: Part) -> str:
    """Extract text from a Part safely."""
    if hasattr(p, 'root') and hasattr(p.root, 'text'):
        return p.root.text or ""
    return ""


async def call_agent(base_url: str, user_input: str, timeout: int = 90) -> str:
    """Send a message to an A2A agent and return the full text response."""
    async with httpx.AsyncClient(timeout=timeout) as http:
        resolver   = A2ACardResolver(httpx_client=http, base_url=base_url)
        agent_card = await resolver.get_agent_card()
        client     = ClientFactory(ClientConfig(httpx_client=http)).create(agent_card)

        msg = Message(
            message_id=str(uuid4()),
            role=Role.user,
            parts=[Part(root=TextPart(text=user_input))],
        )

        parts_collected = []
        async for event in client.send_message(msg):
            if isinstance(event, tuple):
                _, update = event
                if isinstance(update, TaskArtifactUpdateEvent) and update.artifact.parts:
                    parts_collected.append(_part_text(update.artifact.parts[0]))
            elif isinstance(event, Message) and event.parts:
                parts_collected.append(_part_text(event.parts[0]))

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
            parts=[Part(root=TextPart(text=user_input))],
        )

        parts_collected = []
        async for event in client.send_message(msg):
            if isinstance(event, tuple):
                _, update = event
                if isinstance(update, TaskArtifactUpdateEvent) and update.artifact.parts:
                    parts_collected.append(_part_text(update.artifact.parts[0]))
            elif isinstance(event, Message) and event.parts:
                parts_collected.append(_part_text(event.parts[0]))

    return "\n".join(parts_collected)


async def server_is_up(url: str) -> bool:
    """Return True if the agent card endpoint at url responds with 200."""
    try:
        async with httpx.AsyncClient(timeout=5) as http:
            r = await http.get(f"{url}/.well-known/agent-card.json")
            return r.status_code == 200
    except Exception:
        return False
