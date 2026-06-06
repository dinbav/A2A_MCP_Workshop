import httpx
import json
import os
from uuid import uuid4
from typing import AsyncGenerator
from dataclasses import dataclass

import dotenv
dotenv.load_dotenv()

from a2a.client import A2ACardResolver, ClientFactory, ClientConfig
from a2a.types import (
    Message,
    Role,
    AgentCard,
    Task,
    TaskArtifactUpdateEvent,
    TaskStatusUpdateEvent,
    TextPart,
)


@dataclass
class RemoteAgent:
    """Holds agent card, client, and extracted keywords for routing."""
    name: str
    url: str
    agent_card: AgentCard
    client: object
    keywords: set[str]


class OrchestratorAgentLogic:
    """Routes requests to remote agents based on keyword matching against their agent cards."""

    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(current_dir, 'agents_registry.json')) as f:
            data = json.load(f)
        self.agent_registry = {agent['name']: agent['url'] for agent in data['agents']}
        self._remote_agents: dict[str, RemoteAgent] = {}
        self._httpx_client: httpx.AsyncClient | None = None
        self._initialized = False

    async def _ensure_initialized(self) -> None:
        """Fetch agent cards from all registered agents and build keyword index."""
        if self._initialized:
            return

        self._httpx_client = httpx.AsyncClient(timeout=60.0)
        factory = ClientFactory(ClientConfig(httpx_client=self._httpx_client))

        for agent_name, agent_url in self.agent_registry.items():
            try:
                resolver = A2ACardResolver(httpx_client=self._httpx_client, base_url=agent_url)
                agent_card = await resolver.get_agent_card()
                client = factory.create(agent_card)
                self._remote_agents[agent_name] = RemoteAgent(
                    name=agent_card.name,
                    url=agent_url,
                    agent_card=agent_card,
                    client=client,
                    keywords=self._extract_keywords(agent_card),
                )
            except Exception as e:
                print(f"[Orchestrator] Could not discover agent {agent_name} at {agent_url}: {e}")

        self._initialized = True

    def _extract_keywords(self, agent_card: AgentCard) -> set[str]:
        """Extract significant words from agent description, skill names, tags, and examples."""
        stop = {'the', 'and', 'for', 'with', 'that', 'this', 'from', 'can', 'based', 'agent'}
        keywords = set()

        def _add_words(text: str, min_len: int = 4):
            for w in text.lower().split():
                w = w.strip('.,!?()[]{}')
                if len(w) >= min_len:
                    keywords.add(w)

        if agent_card.description:
            _add_words(agent_card.description)

        for skill in (agent_card.skills or []):
            if skill.name:
                _add_words(skill.name, min_len=1)
            for tag in (skill.tags or []):
                keywords.add(tag.lower())
            if skill.description:
                _add_words(skill.description)
            for example in (skill.examples or []):
                _add_words(example)

        return keywords - stop

    def _match_score(self, user_input: str, agent: RemoteAgent) -> int:
        """Return the number of agent keywords present in the user input."""
        user_words = {w.strip('.,!?()[]{}').lower() for w in user_input.split()}
        return len(user_words & agent.keywords)

    async def _select_agents(self, user_input: str) -> tuple[list[RemoteAgent], list[tuple[int, RemoteAgent]]]:
        """Return selected agents and full score table for status reporting."""
        await self._ensure_initialized()
        lower_input = user_input.lower()

        scored = sorted(
            [(self._match_score(user_input, a), a) for a in self._remote_agents.values()],
            key=lambda x: x[0],
            reverse=True,
        )
        scored = [(s, a) for s, a in scored if s > 0]

        if scored:
            threshold = scored[0][0] * 0.5
            selected = [a for s, a in scored if s >= threshold]

            # If the user explicitly asks to explain/learn a topic, always include explainer.
            if any(k in lower_input for k in ("explain", "learn", "teach", "overview")):
                topic_agent = next(
                    (a for a in self._remote_agents.values() if "topic explainer" in a.name.lower()),
                    None,
                )
                if topic_agent and topic_agent not in selected:
                    selected.append(topic_agent)

            return selected, scored

        fallback = list(self._remote_agents.values())[:1]
        return fallback, [(0, a) for a in fallback]

    async def _send_to_agent(self, agent: RemoteAgent, user_input: str,
                              context_id: str = None) -> AsyncGenerator:
        """Stream all A2A events from a remote agent."""
        try:
            msg = Message(
                message_id=uuid4().hex,
                role=Role.user,
                context_id=context_id,
                parts=[TextPart(text=user_input)],
            )

            async for response in agent.client.send_message(msg):
                if isinstance(response, Message):
                    yield response
                    continue

                task, event = response
                if isinstance(event, (TaskArtifactUpdateEvent, TaskStatusUpdateEvent)):
                    yield event
                elif event is None and isinstance(task, Task):
                    if task.status and task.status.message:
                        yield task.status.message

        except Exception as e:
            yield {
                "completed": False,
                "failed": True,
                "input_required": False,
                "content": f"Error communicating with {agent.name}: {e}",
            }

    async def stream(self, user_input: str, context_id: str = None) -> AsyncGenerator[dict, None]:
        """Route user input to matching agent(s) and stream their responses."""
        try:
            yield {
                "completed": False,
                "failed": False,
                "input_required": False,
                "event_type": "status",
                "status_state": "submitted",
                "content": "[status] Analyzing request and matching specialist agents...",
            }

            agents, scored = await self._select_agents(user_input)

            if not agents:
                yield {"completed": False, "failed": True, "input_required": False,
                       "content": "No suitable agent found for your request."}
                return

            agent_names = [a.name for a in agents]
            score_summary = ", ".join(f"{a.name}={s}" for s, a in scored)
            yield {
                "completed": False,
                "failed": False,
                "input_required": False,
                "event_type": "status",
                "status_state": "working",
                "content": f"[status] Routing scores: {score_summary}",
            }
            yield {"completed": False, "failed": False, "input_required": False,
                   "content": f"Running agents: {', '.join(agent_names)}\n\n"}

            for i, agent in enumerate(agents):
                if i > 0:
                    yield {"completed": False, "failed": False, "input_required": False,
                           "content": "\n---\n\n"}
                yield {
                    "completed": False,
                    "failed": False,
                    "input_required": False,
                    "event_type": "status",
                    "status_state": "working",
                    "content": f"[status] Starting {agent.name} ({i + 1}/{len(agents)})...",
                }

                agent_responded = False
                async for event in self._send_to_agent(agent, user_input, context_id=context_id):
                    agent_responded = True
                    yield event

                if not agent_responded:
                    yield {"completed": False, "failed": False, "input_required": False,
                           "content": "(No response from agent)"}
                    yield {
                        "completed": False,
                        "failed": False,
                        "input_required": False,
                        "event_type": "status",
                        "status_state": "working",
                        "content": f"[status] {agent.name} finished with no content.",
                    }
                else:
                    yield {
                        "completed": False,
                        "failed": False,
                        "input_required": False,
                        "event_type": "status",
                        "status_state": "working",
                        "content": f"[status] Completed {agent.name}.",
                    }

            yield {
                "completed": True,
                "failed": False,
                "input_required": False,
                "event_type": "status",
                "status_state": "completed",
                "content": "[status] Orchestration complete.",
            }

        except Exception as e:
            import traceback
            traceback.print_exc()
            yield {"completed": False, "failed": True, "input_required": False,
                   "content": f"Orchestrator error: {e}"}
