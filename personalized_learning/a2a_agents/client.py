"""
client.py  -  Interactive CLI client for the Personalized Learning orchestrator.

Usage:
    python a2a_agents/client.py
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import asyncio
import re
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver, ClientFactory, ClientConfig
from a2a.types import Message, Role, TaskArtifactUpdateEvent, TaskStatusUpdateEvent, TextPart

ORCHESTRATOR_URL = "http://localhost:8090"

RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[96m"
BLUE = "\033[94m"
GREEN = "\033[92m"
MAGENTA = "\033[95m"
YELLOW = "\033[93m"


def _safe_text(value: str) -> str:
    """Normalize potentially invalid surrogate chars for terminal output."""
    return value.encode("utf-8", errors="replace").decode("utf-8", errors="replace")


def _extract_part_text(part) -> str | None:
    text = getattr(part, "text", None)
    if not text and hasattr(part, "root"):
        text = getattr(part.root, "text", None)
    if not text and hasattr(part, "model_dump"):
        dumped = part.model_dump()
        if isinstance(dumped, dict):
            text = dumped.get("text")
    return text


def _text_from_parts(parts) -> str:
    chunks = []
    for part in parts or []:
        text = _extract_part_text(part)
        if text:
            chunks.append(_safe_text(str(text)))
    return "".join(chunks)


def _print_with_label(source: str, event_kind: str, text: str, color: str) -> None:
    print(f"\n{color}{BOLD}{source} [{event_kind}]: {RESET}{color}{text}{RESET}", end="", flush=True)


def _normalize_state(state) -> str:
    return str(state).split(".")[-1]


def _detect_orchestrator_status(text: str) -> bool:
    return text.strip().startswith("[status]")


def _update_current_agent(current_agent: str | None, status_text: str) -> str | None:
    start_match = re.search(r"Starting (.+?) \(\d+/\d+\)", status_text)
    if start_match:
        return start_match.group(1).strip()
    end_match = re.search(r"Completed (.+?)\.", status_text)
    if end_match and current_agent and end_match.group(1).strip() == current_agent:
        return None
    return current_agent


async def main():
    print("Personalized Learning Assistant")
    print("Type your question or 'exit' to quit.\n")

    context_id = str(uuid4())
    print(f"[Session ID: {context_id[:8]}...]\n")

    async with httpx.AsyncClient(timeout=120.0) as http:
        resolver   = A2ACardResolver(httpx_client=http, base_url=ORCHESTRATOR_URL)
        agent_card = await resolver.get_agent_card()
        client     = ClientFactory(ClientConfig(httpx_client=http)).create(agent_card)

        while True:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break

            if user_input.lower() in ("exit", "quit", "q"):
                print("Goodbye!")
                break
            if not user_input:
                continue

            msg = Message(
                message_id=str(uuid4()),
                role=Role.user,
                context_id=context_id,
                parts=[TextPart(text=user_input)],
            )

            print("\nAssistant: ", end="", flush=True)
            current_agent = None
            try:
                async for response in client.send_message(msg):
                    if isinstance(response, Message):
                        text = _text_from_parts(response.parts)
                        _print_with_label("Agent", "message", text, CYAN)
                        continue

                    task, event = response
                    if isinstance(event, TaskArtifactUpdateEvent):
                        text = _text_from_parts(getattr(event.artifact, "parts", []))
                        source = f"Agent:{current_agent}" if current_agent else "Orchestrator"
                        color = CYAN if current_agent else MAGENTA
                        _print_with_label(source, "Artifact", text, color)
                    elif isinstance(event, TaskStatusUpdateEvent) and event.status.message:
                        state = _normalize_state(getattr(getattr(event, "status", None), "state", "unknown"))
                        text = _text_from_parts(getattr(event.status.message, "parts", []))
                        if _detect_orchestrator_status(text):
                            current_agent = _update_current_agent(current_agent, text)
                            _print_with_label("Orchestrator", f"Status: {state}", text, BLUE)
                        else:
                            source = f"Agent:{current_agent}" if current_agent else "Agent"
                            _print_with_label(source, f"Status: {state}", text, CYAN)
                    elif event is None and task.status.message:
                        state = _normalize_state(getattr(getattr(task, "status", None), "state", "unknown"))
                        text = _text_from_parts(getattr(task.status.message, "parts", []))
                        if _detect_orchestrator_status(text):
                            current_agent = _update_current_agent(current_agent, text)
                            _print_with_label("Orchestrator", f"Status: {state}", text, BLUE)
                        else:
                            source = f"Agent:{current_agent}" if current_agent else "Agent"
                            _print_with_label(source, f"Status: {state}", text, CYAN)
            except Exception as e:
                print(f"\n{YELLOW}[Error: {_safe_text(str(e))}]{RESET}")
            print("\n")


if __name__ == "__main__":
    asyncio.run(main())
