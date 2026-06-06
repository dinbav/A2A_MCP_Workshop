# When Agents Talk: Your First Multi-Agent System — No LLM Tokens Required

## A Detailed Exploration of Building a Complete Orchestrator, 3 Agents, and an MCP Tool Server — Without a Single AI API Call

*From the **When Agents Talk** workshop · Part 2 of 5*

---

> *"By Author using DALL-E"*
> *(Hero image: creative image of AI agents as small construction workers building a pipeline without any brain/AI symbol present, emphasizing teamwork and structure, flat illustration style, pastel colors)*

---

What if I told you that you can build a fully working multi-agent system — four agents collaborating, routing requests, and serving structured responses — without calling OpenAI, Anthropic, or any LLM at all?

No tokens. No API key. No cost per request.

Here's how.

This is Part 2 of the **When Agents Talk** series. If you're new to the vocabulary — **Agent Card**, **Orchestrator**, **MCP**, **Context ID** — read [Part 1: The Language of Multi-Agent AI](post1_terminology.md) first. It's a 5-minute read and will make this one click immediately.

*In [Part 3](post3_patterns.md), we add LLM reasoning to the mix — and show exactly where it adds value vs. where it would just add cost.*

· What We're Building · The MCP Server: Your Data Layer · The Agent Anatomy: Five Files, One Blueprint · Agent Logic: The Only File That Changes · The Orchestrator: Routing Without AI · Running It · What You Just Built · Sources and Further Reading

---

## What We're Building

The **Personalized Learning** system. A user types a message — "explain MCP to me" — and a multi-agent system figures out who should answer it, asks the right specialist, queries a data server, and returns a structured response.

Four agents. Eight tools. Zero LLM calls.

<!-- DIAGRAM D2.1: post2_architecture.excalidraw — Full system architecture with port numbers -->

![Personalized Learning Architecture — see post2_architecture.excalidraw](diagrams/post2_architecture.png)

Here's what runs where:

| Component | Port | What it does |
|-----------|------|-------------|
| **MCP Server** | 8004 | Serves 8 data tools (topics, assessments, study paths, career data) |
| **Topic Explainer Agent** | 8091 | Explains learning topics (MCP, A2A, RAG, async...) at a given level |
| **Assessment Agent** | 8092 | Generates quiz questions and updates learning scores |
| **Study Plan Agent** | 8093 | Builds personalized study paths and career gap analyses |
| **Orchestrator** | 8090 | Reads agent cards, scores the request, routes to the right agent(s) |

The user talks only to the Orchestrator. Everything else happens behind the scenes.

---

## The MCP Server: Your Data Layer

**MCP (Model Context Protocol)** is the standard that lets agents call tools — functions that return data. Think of it as the backend API layer of your multi-agent system.

In our workshop, MCP tools are built with **FastMCP** — a Python library that turns a regular function into an A2A-compatible tool with one decorator.

Here is the complete pattern, using `get_topic_summary` as the example:

```python
# use_cases/personalized_learning/mcp/fastmcp_server.py  (lines 61–100)

@mcp.tool(tags={"topic", "explanation"})
def get_topic_summary(topic: str, level: str = "beginner") -> dict:
    """
    Get a structured summary of a learning topic at a specific level.

    Args:
        topic: One of: mcp, a2a, rag, prompt_engineering, python_async
        level: One of: beginner, intermediate, advanced
    """
    topic_key = topic.lower().strip().replace(" ", "_")
    level_key = level.lower().strip()

    if topic_key not in TOPICS:
        return {"found": False, "message": f"Topic '{topic}' not found."}

    data = TOPICS[topic_key][level_key]
    return {
        "topic": topic_key,
        "level": level_key,
        "found": True,
        "summary": data["summary"],
        "key_concepts": data["key_concepts"],
        "common_misconceptions": data["common_misconceptions"],
        "next_step": data.get("next_step", ""),
    }
```

Three things to notice:

- **`@mcp.tool(tags={"topic", "explanation"})`** — the decorator makes this function a callable MCP tool. The `tags` are how agents filter tools. An agent interested in `"topic"` will find this tool; one interested only in `"career"` will not.
- **Plain Python function** — no special base class, no framework magic. FastMCP wraps the function and exposes it over HTTP.
- **Returns a dict** — the agent receives this dict as a string and parses it.

The MCP server has 8 tools in total. All 8 follow this exact pattern — same decorator, same return style, different function body. We won't repeat them. The pattern is the same.

To start the server:

```bash
cd use_cases/personalized_learning
python mcp/fastmcp_server.py
# Runs on http://0.0.0.0:8004/mcp
```

---

## The Agent Anatomy: Five Files, One Blueprint

Every agent in this workshop — all four of them — is built from exactly five files. The structure never changes.

<!-- DIAGRAM D2.2: post2_agent_anatomy.excalidraw — 5-file stack, green = identical, orange = unique -->

![Agent Anatomy — see post2_agent_anatomy.excalidraw](diagrams/post2_agent_anatomy.png)

| File | What it does | Same for every agent? |
|------|-------------|----------------------|
| `__main__.py` | Entry point — 3 lines that start the server | ✅ Yes — identical |
| `agent_card.py` | Declares the agent's name, skills, tags, and examples | Structure identical; content differs |
| `agent_executor.py` | Bridges the A2A SDK ↔ agent logic | ✅ Yes — identical |
| `agent_logic.py` | The actual business logic — what the agent *does* | ❌ No — the ONLY file that changes |
| `server_factory.py` | Shared HTTP server bootstrap (one file for all agents) | ✅ Yes — shared, not per-agent |

We will show each file once, using the **Topic Explainer Agent** as the canonical example. The other three agents follow the exact same structure — we won't repeat them.

---

### The Agent Card

The **Agent Card** is how the orchestrator discovers what this agent can do. It's served automatically at `/.well-known/agent-card.json`.

```python
# use_cases/personalized_learning/a2a_agents/remote_agents/topic_explainer_agent/agent_card.py

from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill

explain_topic_skill = AgentSkill(
    id='explain_topic',
    name='Explain Topic Skill',
    description='Explains a learning topic (MCP, A2A, RAG, prompt engineering, '
                'Python async) at the requested level.',
    tags=['explanation', 'topic', 'concepts', 'beginner', 'intermediate',
          'advanced', 'learn', 'explain'],
    examples=[
        'Explain MCP for a beginner.',
        'Explain A2A for an intermediate developer.',
        'What are the key concepts in RAG?',
    ],
)

public_agent_card = AgentCard(
    name='Topic Explainer Agent',
    description='An agent that explains learning topics at the requested level.',
    url='http://localhost:8091/',
    supported_interfaces=[AgentInterface(url='http://localhost:8091/', transport='JSONRPC')],
    version='1.0.0',
    capabilities=AgentCapabilities(streaming=True),
    skills=[explain_topic_skill],
    default_input_modes=['text'],
    default_output_modes=['text'],
)
```

The orchestrator reads `tags` (`explanation`, `topic`, `learn`, `explain`) and `examples` to build its keyword index. When a user types "explain MCP to me", the word "explain" appears in both the user message and the card — the orchestrator knows to route here.

---

### The Agent Executor

The **Agent Executor** is the bridge. It receives the A2A SDK's request context, extracts the user's message and conversation history, calls the agent logic, and sends events back.

```python
# use_cases/personalized_learning/a2a_agents/remote_agents/topic_explainer_agent/agent_executor.py

from a2a_agents.base_executor import BaseAgentExecutor
from .agent_logic import AgentLogic

class AgentExecutor(BaseAgentExecutor):
    def _make_logic(self):
        return AgentLogic()
```

That's it. Two lines of real logic.

The base class (`BaseAgentExecutor`) handles the actual SDK interaction — reading history from the task store, streaming artifacts, marking tasks as complete or failed. Every agent in the workshop uses the same base class. You never rewrite this.

```python
# use_cases/personalized_learning/a2a_agents/base_executor.py  (key section)

async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
    history = context.current_task.history if context.current_task else []

    async for response in self.agent.stream(context.get_user_input(), history=history):
        completed      = response.get("completed", False)
        failed         = response.get("failed", False)
        input_required = response.get("input_required", False)
        content        = response.get("content", "")

        if failed:
            await updater.failed(...)
        elif completed:
            await updater.add_artifact(...)
            await updater.complete()
        ...
```

The executor reads a simple dict contract from `agent_logic.stream()`:
- `completed: True/False` — is this the final response?
- `failed: True/False` — did something go wrong?
- `input_required: True/False` — should we ask the user for more info?
- `content: str` — the text to send

---

### The Server Factory

```python
# use_cases/personalized_learning/a2a_agents/server_factory.py

def run(agent_card, executor_class, port: int) -> None:
    handler = DefaultRequestHandler(
        agent_executor=executor_class(),
        task_store=InMemoryTaskStore(),
    )
    app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=handler
    ).build(rpc_url='/')
    uvicorn.run(app, host='0.0.0.0', port=port)
```

One function. Every agent calls it with its own card, executor class, and port. The SDK handles the rest — routing, JSON-RPC, streaming, the agent card endpoint.

### The Entry Point

```python
# use_cases/personalized_learning/a2a_agents/remote_agents/topic_explainer_agent/__main__.py

from a2a_agents.server_factory import run
from .agent_card import public_agent_card
from .agent_executor import AgentExecutor

if __name__ == '__main__':
    run(public_agent_card, AgentExecutor, port=8091)
```

Three lines. Import card, import executor, call `run`. Every agent in the workshop looks exactly like this.

---

## Agent Logic: The Only File That Changes

Now for the only thing that actually differs between agents. This is where the learning system earns its keep.

All three learning agents use **Pattern 3: MCP Direct** — no LLM. Parse the input, call the right MCP tool, format the result.

Here is the Topic Explainer agent's logic:

```python
# use_cases/personalized_learning/a2a_agents/remote_agents/topic_explainer_agent/agent_logic.py
# (core stream() method)

async def stream(self, user_input: str, history=None) -> AsyncGenerator:
    # 1. Combine history + current message for follow-up context
    full_context = user_input
    if history:
        history_texts = [part.text for msg in history for part in msg.parts
                         if hasattr(part, 'text') and part.text]
        full_context = " ".join(history_texts) + " " + user_input

    # 2. Parse topic and level from plain text (no LLM needed)
    topic = _parse_topic(full_context)   # e.g. "mcp", "a2a", "rag"
    level = _parse_level(full_context)   # e.g. "beginner", "intermediate"

    # 3. Call the MCP tool directly
    async with Client(self.mcp_url) as client:
        result = await client.call_tool(
            "get_topic_summary",
            {"topic": topic, "level": level},
        )

    # 4. Format and return
    data = json.loads(result.content[0].text)
    formatted = _format_explanation(data)
    yield {"completed": True, "failed": False, "input_required": False,
           "content": formatted}
```

Step by step:
1. **No LLM to understand the intent** — a simple keyword parser (`_parse_topic`) finds "mcp", "a2a", "rag" etc. in the message.
2. **No LLM to decide what to call** — the tool name is hardcoded. This agent always calls `get_topic_summary`.
3. **One MCP call** — the result comes back as JSON, we parse it and format it.
4. **One `yield`** — the response is complete in one shot.

The assessment and study plan agents are structurally identical. They parse different keywords, call different MCP tools, format results differently. The shape of `stream()` is the same.

---

## The Orchestrator: Routing Without AI

<!-- DIAGRAM D2.3: post2_request_flow.excalidraw — End-to-end: "explain mcp" → routing → MCP call → response -->

![Request Flow — see post2_request_flow.excalidraw](diagrams/post2_request_flow.png)

The orchestrator is the most interesting piece — and it also uses no LLM.

Here is how it decides where to send a request:

```python
# use_cases/personalized_learning/a2a_agents/orchestrator_agent/agent_logic.py
# (routing core — _select_agents and _extract_keywords)

def _extract_keywords(self, agent_card: AgentCard) -> set[str]:
    """Pull significant words from the card's description, skill names, tags, and examples."""
    keywords = set()
    _add_words(agent_card.description)
    for skill in (agent_card.skills or []):
        _add_words(skill.name, min_len=1)
        keywords.update(tag.lower() for tag in (skill.tags or []))
        _add_words(skill.description)
        for example in (skill.examples or []):
            _add_words(example)
    return keywords - STOP_WORDS

def _match_score(self, user_input: str, agent: RemoteAgent) -> int:
    """Count how many of this agent's keywords appear in the user's message."""
    user_words = {w.strip('.,!?').lower() for w in user_input.split()}
    return len(user_words & agent.keywords)

async def _select_agents(self, user_input: str):
    scored = sorted(
        [(self._match_score(user_input, a), a) for a in self._remote_agents.values()],
        reverse=True,
    )
    scored = [(s, a) for s, a in scored if s > 0]

    if scored:
        threshold = scored[0][0] * 0.5          # within 50% of the top score
        selected = [a for s, a in scored if s >= threshold]
        return selected
    return [list(self._remote_agents.values())[0]]  # fallback: first agent
```

The routing logic:
1. At startup, fetch each agent's card from its live URL
2. Extract a keyword set from the card (description + skill names + tags + examples)
3. When a message arrives, count how many keywords from each agent's set appear in the message
4. Select all agents within 50% of the top score — so if two agents are both relevant, both get called

The registry is a simple JSON file:

```json
// use_cases/personalized_learning/a2a_agents/orchestrator_agent/agents_registry.json
{
  "agents": [
    { "name": "Topic Explainer Agent", "url": "http://localhost:8091" },
    { "name": "Assessment Agent",      "url": "http://localhost:8092" },
    { "name": "Study Plan Agent",      "url": "http://localhost:8093" }
  ]
}
```

The orchestrator reads this on startup, fetches the live cards, and builds its index. No LLM needed for routing — keyword overlap is enough.

---

## Running It

**Prerequisites:**

```bash
cd use_cases/personalized_learning
pip install -e .
```

**Create a `.env` file:**

```env
MCP_SERVER_URL=http://127.0.0.1:8004/mcp
# No LLM keys needed for this use case
```

**Start everything:**

```powershell
.\start_all.ps1
```

This opens five terminals:
- MCP Server on :8004
- Topic Explainer on :8091
- Assessment on :8092
- Study Plan on :8093
- Orchestrator on :8090

**Test it:**

```bash
python a2a_agents/client.py
# Type: explain mcp to me
```

What happens:
1. Your message goes to the Orchestrator on :8090
2. The orchestrator scores: Topic Explainer wins ("explain", "mcp" match its tags)
3. The orchestrator calls the Topic Explainer on :8091
4. The Topic Explainer parses "mcp" and "beginner", calls the MCP tool
5. The MCP server on :8004 returns the structured topic summary
6. The formatted response streams back to you

No LLM was called at any point.

---

## What You Just Built

Let's be concrete about what exists now:

- **4 agents** collaborating over the A2A protocol
- **8 MCP tools** serving structured learning, assessment, and career data
- **Keyword-based routing** with live agent card discovery
- **Conversation history** threaded by Context ID through the task store
- **Zero LLM calls** — fully deterministic, fully testable, zero per-request cost

To run the tests:

```bash
python tests/run_all_tests.py --only mcp        # fast — tests MCP tools directly
python tests/run_all_tests.py --skip-agents     # skip the agent conversation tests
```

The MCP tests run in seconds. The agent tests are also fast — no LLM latency.

---

## Summary

Key things we built and learned:

- **MCP tool pattern** — one `@mcp.tool()` decorator turns a Python function into a discoverable, callable tool
- **Agent anatomy** — five files per agent; four of them are identical across every agent; only `agent_logic.py` changes
- **Agent executor** — two lines that connect the A2A SDK to the agent logic; copy-paste for every new agent
- **MCP Direct pattern** — parse input → call tool → format result; no LLM required; fully deterministic
- **Orchestrator routing** — keyword scoring against live agent cards; no AI needed to decide who to call

In [Part 3](post3_patterns.md), we add the Travel Activity Planner — the use case where an LLM genuinely adds value. Three different agent patterns. One of them you already know.

---

If this post helped you, please clap 👏 (you can clap up to 50 times!) — it's the main way Medium surfaces articles to new readers. The more people see this, the more developers can build without the gatekeeping. Thank you for helping spread it.

---

## Sources and Further Reading

**Workshop Repository:**
- [When Agents Talk — Workshop Code](https://github.com/dinabavli/a2a_mcp_workshop) *(link to repo)*

**A2A Protocol:**
- [A2A Python SDK](https://github.com/a2aproject/a2a-python)
- [A2A Protocol Specification](https://a2a-protocol.org)

**FastMCP:**
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)

**Related Posts in This Series:**
- **Part 1**: [The Language of Multi-Agent AI](post1_terminology.md) — vocabulary before code
- **Part 3**: [Three Patterns for Agent Intelligence](post3_patterns.md) — adding LLM where it matters
- **Part 4**: [When Agents Talk in Production](post4_production.md) — going to production
- **Part 5**: [Migrating a2a-sdk 0.3 to 1.0](post5_migration.md) — upgrading the SDK

---

*Written by Dina Bavli · Data Scientist | NLP | AI Systems · ❤ sharing knowledge and contributing to the community*
