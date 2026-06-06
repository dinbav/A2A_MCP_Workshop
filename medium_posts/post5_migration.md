# When Agents Talk, But the Protocol Changed: Migrating a2a-sdk 0.3 to 1.0

## A Practical Before/After Guide for Every Breaking Change — From Part Types to Server Setup

*From the **When Agents Talk** workshop · Part 5 of 5*

---

> *"By Author using DALL-E"*
> *(Hero image: a bridge being built between two islands, one labeled "0.3" and one labeled "1.0", construction workers laying cable, optimistic morning light, flat illustration style)*

---

The workshop code in this series runs on `a2a-sdk==0.3.22`.

It is production-quality code. It works. It is tested. And you can absolutely ship it as-is.

But the A2A protocol hit a major milestone with `v1.0`. The Python SDK followed. There are breaking changes. If you're starting a new project today — or planning to upgrade an existing one — this post is your guide.

We will go through every breaking change, show you the 0.3 code from our workshop, and show you the 1.0 equivalent side by side. No assumptions about what you already know. No skipping the parts that feel obvious.

This is Part 5 of the **When Agents Talk** series. All the code from Parts 2, 3, and 4 is built on `0.3.22`. This post is the bridge.

*Read this if: you're upgrading an existing A2A project, or starting a new one and want to skip 0.3 entirely.*

· What Changed and Why · Change 1: The Part Type · Change 2: Enum Casing · Change 3: Server Setup · Change 4: Helper Utilities · Change 5: AgentCard — Interfaces · Change 6: Executor Streaming Rules · Change 7: Compatibility Mode · Upgrading Step by Step · Sources and Further Reading

---

## What Changed and Why

`a2a-sdk 1.0` is a major version bump for a reason. The core changes are:

1. **Protobuf types replace Pydantic models** — The SDK's type system moved from Pydantic to Protobuf-generated Python classes. This brings stronger interoperability with non-Python agents and stricter serialization guarantees.

2. **The `Part` type is unified** — `TextPart`, `FilePart`, `DataPart` were separate classes. Now there's one `Part` with fields for each content type.

3. **Enums are `SCREAMING_SNAKE_CASE`** — `"submitted"` became `"TASK_STATE_SUBMITTED"`. This follows the ProtoJSON specification.

4. **Server wrappers are gone** — `A2AStarletteApplication` was removed. You now compose routes using factory functions.

5. **Helper utilities are consolidated** — `a2a.utils.*` moved to `a2a.helpers`.

6. **Stricter executor rules** — The order and type of events emitted by an executor is now strictly validated.

<!-- DIAGRAM D5.1: post5_migration_overview.excalidraw — Side-by-side: 0.3 import tree vs 1.0 import tree -->

![Migration Overview — see post5_migration_overview.excalidraw](diagrams/post5_migration_overview.png)

---

## Change 1: The Part Type

This is the most impactful change. It touches every place you create or read message content.

**The concept:** In 0.3, you wrapped text in a `TextPart`, then placed that inside a `Part`. In 1.0, the wrapper types are gone — `Part` itself holds the content directly.

### Creating a text message

**Before (0.3.22):**
```python
from a2a.types import TextPart, Part, Message, Role

message = Message(
    message_id=uuid4().hex,
    role=Role.user,
    context_id=context_id,
    parts=[TextPart(text=user_input)],   # TextPart is a separate wrapper class
)
```

**After (1.0):**
```python
from a2a.types import Part, Message, Role

message = Message(
    message_id=uuid4().hex,
    role=Role.USER,                      # enum is now SCREAMING_SNAKE_CASE
    context_id=context_id,
    parts=[Part(text=user_input)],       # text is set directly on Part
)
```

Two changes at once: `TextPart` → `Part(text=...)`, and `Role.user` → `Role.USER`.

### Reading part content

**Before (0.3.22):**
```python
for msg in history:
    for part in msg.parts:
        if hasattr(part, 'text') and part.text:
            content = part.text
```

**After (1.0):**
```python
from a2a.helpers import get_text_from_message

for msg in history:
    text = get_text_from_message(msg)   # helper handles the extraction
    if text:
        content = text
```

Or manually with the new Part structure:
```python
for msg in history:
    for part in msg.parts:
        if part.HasField('text'):       # Protobuf field-presence check
            content = part.text
```

Note: `hasattr(part, 'text')` does not work reliably with Protobuf types. Use `HasField()` or the new helper functions.

---

## Change 2: Enum Casing

Every enum value changed from lowercase/snake_case to `SCREAMING_SNAKE_CASE`. This is a ProtoJSON standard requirement for cross-language interoperability.

**The mapping:**

| 0.3.22 | 1.0 |
|--------|-----|
| `Role.user` | `Role.USER` |
| `Role.agent` | `Role.AGENT` |
| `TaskState.submitted` | `TaskState.TASK_STATE_SUBMITTED` |
| `TaskState.working` | `TaskState.TASK_STATE_WORKING` |
| `TaskState.completed` | `TaskState.TASK_STATE_COMPLETED` |
| `TaskState.failed` | `TaskState.TASK_STATE_FAILED` |
| `TaskState.input_required` | `TaskState.TASK_STATE_INPUT_REQUIRED` |
| `TaskState.canceled` | `TaskState.TASK_STATE_CANCELED` |
| `TaskState.rejected` | `TaskState.TASK_STATE_REJECTED` |

### In the agent logic files

**Before (0.3.22):**
```python
# use_cases/travel_activity_planner/a2a_agents/remote_agents/packing_list_agent/agent_logic.py

from a2a.types import Role

for msg in (history or []):
    for part in msg.parts:
        if hasattr(part, 'text') and part.text:
            if msg.role == Role.ROLE_USER:          # 0.3 uses Role.ROLE_USER
                messages.append(HumanMessage(content=part.text))
            else:
                messages.append(AIMessage(content=part.text))
```

**After (1.0):**
```python
from a2a.types import Role

for msg in (history or []):
    for part in msg.parts:
        if part.HasField('text'):
            if msg.role == Role.USER:               # 1.0 uses Role.USER
                messages.append(HumanMessage(content=part.text))
            else:
                messages.append(AIMessage(content=part.text))
```

---

## Change 3: Server Setup

This is the most visible structural change. The `A2AStarletteApplication` wrapper class is removed. Server setup now uses explicit route factory functions.

**Before (0.3.22):**
```python
# use_cases/personalized_learning/a2a_agents/server_factory.py

from a2a.server.apps.jsonrpc.starlette_app import A2AStarletteApplication
from a2a.server.request_handlers.default_request_handler import DefaultRequestHandler
from a2a.server.tasks.inmemory_task_store import InMemoryTaskStore
import uvicorn
from starlette.applications import Starlette

def create_app(agent_card, executor_class) -> Starlette:
    handler = DefaultRequestHandler(
        agent_executor=executor_class(),
        task_store=InMemoryTaskStore(),
    )
    return A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=handler
    ).build(rpc_url='/')


def run(agent_card, executor_class, port: int) -> None:
    app = create_app(agent_card, executor_class)
    uvicorn.run(app, host='0.0.0.0', port=port)
```

**After (1.0):**
```python
# server_factory.py — 1.0 version

from starlette.applications import Starlette
from starlette.routing import Route
from a2a.server.apps import create_jsonrpc_routes, create_agent_card_routes
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
import uvicorn


def create_app(agent_card, executor_class) -> Starlette:
    handler = DefaultRequestHandler(
        agent_executor=executor_class(),
        task_store=InMemoryTaskStore(),
    )

    # Compose routes explicitly — no wrapper class
    routes = [
        *create_agent_card_routes(agent_card),   # serves /.well-known/agent-card.json
        *create_jsonrpc_routes(handler),          # serves the JSON-RPC endpoint at /
    ]
    return Starlette(routes=routes)


def run(agent_card, executor_class, port: int) -> None:
    app = create_app(agent_card, executor_class)
    uvicorn.run(app, host='0.0.0.0', port=port)
```

The change is explicit: you compose the routes yourself. This is more verbose — but it gives you full control over middleware, auth, and routing without fighting the wrapper class.

---

## Change 4: Helper Utilities

In 0.3.22, utilities were scattered across `a2a.utils.*`. In 1.0, they are consolidated under `a2a.helpers`.

### Message helpers

**Before (0.3.22):**
```python
from a2a.utils.message import new_agent_text_message
from a2a.utils.artifact import new_text_artifact
```

**After (1.0):**
```python
from a2a.helpers import new_agent_text_message, new_text_artifact
```

### In the base executor

**Before (0.3.22):**
```python
# use_cases/personalized_learning/a2a_agents/base_executor.py

from a2a.utils.artifact import new_text_artifact
from a2a.utils.message import new_agent_text_message

class BaseAgentExecutor(_AgentExecutor):
    async def execute(self, context, event_queue):
        ...
        message = new_agent_text_message(
            text=safe_content,
            context_id=context_id,
            task_id=task_id
        )
        await updater.failed(message)
```

**After (1.0):**
```python
from a2a.helpers import new_agent_text_message, new_text_artifact

class BaseAgentExecutor(_AgentExecutor):
    async def execute(self, context, event_queue):
        ...
        message = new_agent_text_message(
            text=safe_content,
            context_id=context_id,
            task_id=task_id
        )
        await updater.failed(message)
```

Only the import line changes. The function signatures remain compatible.

---

## Change 5: AgentCard — Interfaces

The way an agent card declares its network interface changed. In 0.3.22, `supported_interfaces` used an `AgentInterface` type. In 1.0, `supportedInterfaces` is an array of interface objects with a `protocolVersion` field, and `preferredTransport` is removed.

**Before (0.3.22):**
```python
# agent_card.py (0.3)

from a2a.types import AgentCard, AgentCapabilities, AgentInterface, AgentSkill

public_agent_card = AgentCard(
    name='Topic Explainer Agent',
    url='http://localhost:8091/',
    supported_interfaces=[
        AgentInterface(url='http://localhost:8091/', transport='JSONRPC')
    ],
    version='1.0.0',
    capabilities=AgentCapabilities(streaming=True),
    skills=[explain_topic_skill],
    default_input_modes=['text'],
    default_output_modes=['text'],
)
```

**After (1.0):**
```python
# agent_card.py (1.0)

from a2a.types import (
    AgentCard, AgentCapabilities, AgentInterface, AgentSkill,
    ProtocolVersion
)

public_agent_card = AgentCard(
    name='Topic Explainer Agent',
    url='http://localhost:8091/',
    supported_interfaces=[
        AgentInterface(
            url='http://localhost:8091/',
            protocol_binding='JSONRPC',       # replaces `transport`
            protocol_version=ProtocolVersion.V1_0,   # explicit version
        )
    ],
    version='1.0.0',
    capabilities=AgentCapabilities(streaming=True),
    skills=[explain_topic_skill],
    default_input_modes=['text'],
    default_output_modes=['text'],
)
```

The main additions: `protocol_binding` replaces `transport`, and `protocol_version` is now declared explicitly.

---

## Change 6: Executor Streaming Rules — Now Strictly Enforced

In 0.3.22, the server was lenient about what an executor could yield and in what order. In 1.0, the server strictly enforces the A2A specification.

**The new rules:**

An executor must emit events in one of two valid sequences:

**Sequence A — Single Message response:**
```
Message → (done)
```

**Sequence B — Task with updates:**
```
Task → TaskStatusUpdateEvent* → TaskArtifactUpdateEvent* → TaskStatusUpdateEvent(final)
```

The following are now explicitly invalid and will raise `InvalidAgentResponseError`:
- Emitting a `Message` after the initial one (multiple Messages not allowed)
- Emitting `TaskStatusUpdateEvent` or `TaskArtifactUpdateEvent` before the initial `Task`
- Mixing Message and Task modes in the same execution

**What this means for our workshop code:**

The current workshop's `BaseAgentExecutor` uses the `TaskUpdater` API (`updater.add_artifact()`, `updater.complete()`, `updater.failed()`). This is the high-level API that the SDK provides. If you use `TaskUpdater`, the SDK handles the event ordering for you — you don't need to change the executor logic.

If you wrote a custom executor that emits raw events, you will need to review the ordering.

---

## Change 7: Compatibility Mode (The Easy Migration Path)

The 1.0 SDK includes a compatibility flag specifically designed to help you migrate gradually.

When you set `enable_v0_3_compat=True` on the route factory, the server accepts both 0.3 and 1.0 clients:

```python
# server_factory.py — with compatibility mode

routes = [
    *create_agent_card_routes(agent_card),
    *create_jsonrpc_routes(handler, enable_v0_3_compat=True),   # ← backward compat
]
```

This lets you:
- Upgrade the server to 1.0 SDK immediately
- Keep existing 0.3 clients working while they migrate
- Remove `enable_v0_3_compat=True` once all clients are on 1.0

**Advertise both versions in the Agent Card** so clients know you support both:

```python
supported_interfaces=[
    AgentInterface(url='http://localhost:8091/', protocol_version=ProtocolVersion.V1_0),
    AgentInterface(url='http://localhost:8091/', protocol_version=ProtocolVersion.V0_3),
]
```

---

## Upgrading Step by Step

<!-- DIAGRAM D5.2: post5_migration_checklist.excalidraw — Checklist flowchart with file names and what to change -->

![Migration Checklist — see post5_migration_checklist.excalidraw](diagrams/post5_migration_checklist.png)

**Step 1 — Upgrade the dependency:**

```toml
# pyproject.toml

# Before:
# "a2a-sdk==0.3.22",

# After:
"a2a-sdk>=1.0",
```

```bash
pip install -e .   # or pip install a2a-sdk --upgrade
```

**Step 2 — Update `server_factory.py`:**

Replace `A2AStarletteApplication` with `create_jsonrpc_routes` + `create_agent_card_routes`. Use compatibility mode while migrating:

```python
# Remove:
from a2a.server.apps.jsonrpc.starlette_app import A2AStarletteApplication

# Add:
from a2a.server.apps import create_jsonrpc_routes, create_agent_card_routes
```

**Step 3 — Update `base_executor.py`:**

Fix the two import lines:

```python
# Before:
from a2a.utils.artifact import new_text_artifact
from a2a.utils.message import new_agent_text_message

# After:
from a2a.helpers import new_text_artifact, new_agent_text_message
```

**Step 4 — Update each `agent_card.py`:**

Add `protocol_version` to each `AgentInterface`:

```python
# Before:
AgentInterface(url='http://localhost:8091/', transport='JSONRPC')

# After:
AgentInterface(url='http://localhost:8091/', protocol_version=ProtocolVersion.V1_0)
```

**Step 5 — Update each `agent_logic.py` that reads message history:**

Replace `hasattr(part, 'text')` with `part.HasField('text')`, and update Role enum references:

```python
# Before:
if hasattr(part, 'text') and part.text:
    if msg.role == Role.ROLE_USER:

# After:
if part.HasField('text'):
    if msg.role == Role.USER:
```

**Step 6 — Update the orchestrator's message construction:**

```python
# Before:
parts=[TextPart(text=user_input)]

# After:
parts=[Part(text=user_input)]
```

**Step 7 — Run the test suite:**

```bash
# Start with MCP tests — no A2A SDK dependency, fast:
python tests/run_all_tests.py --only mcp

# Then agent tests:
python tests/run_all_tests.py
```

**Step 8 — Remove compatibility mode** once all clients have migrated:

```python
# Remove the flag:
*create_jsonrpc_routes(handler)   # no enable_v0_3_compat
```

---

## Summary: Full Change Matrix

| What changed | File(s) affected | Effort |
|---|---|---|
| `A2AStarletteApplication` → route factories | `server_factory.py` | Medium |
| `TextPart(text=x)` → `Part(text=x)` | `orchestrator/agent_logic.py` | Low |
| `hasattr(part, 'text')` → `part.HasField('text')` | All `agent_logic.py` with history | Low |
| `Role.ROLE_USER` → `Role.USER` | All `agent_logic.py` with history | Low (grep-and-replace) |
| `a2a.utils.message` → `a2a.helpers` | `base_executor.py` | Low |
| `a2a.utils.artifact` → `a2a.helpers` | `base_executor.py` | Low |
| `AgentInterface(transport=)` → `(protocol_version=)` | All `agent_card.py` | Low |
| TaskState enums | Only if you reference raw enum values | Low (grep-and-replace) |

Total estimate for the workshop codebase: **2–4 hours** for a careful, test-driven migration. Most changes are grep-and-replace with no logic change.

---

## One More Thing: The Compatibility Flag Buys You Time

If upgrading everything at once feels daunting, here is the minimal viable migration:

1. Upgrade the SDK: `pip install a2a-sdk>=1.0`
2. Fix the server factory (Change 3 above — this is required)
3. Add `enable_v0_3_compat=True`
4. Run your tests

Steps 5–7 in the checklist above can happen over time. The compatibility flag keeps your agents working while you migrate each piece.

The A2A team has committed to keeping compatibility mode available through the 1.x release cycle — so you have runway.

---

This is the last post in the **When Agents Talk** series.

If you've read all five posts, you now have:
- A shared vocabulary for multi-agent systems (Part 1)
- A working multi-agent system with zero LLM cost (Part 2)
- Three production-quality agent patterns (Part 3)
- A production readiness framework (Part 4)
- A complete migration guide for the protocol upgrade (Part 5)

The workshop repository is linked in Sources below. Every post in this series is documented there as well.

---

If this post helped you, please clap 👏 (you can clap up to 50 times!) — it's the main way Medium surfaces articles to new readers. The more people see this, the more developers can build without the gatekeeping. Thank you for helping spread it.

---

## Sources and Further Reading

**Official Migration Guide:**
- [a2a-python Migration Guide v1.0](https://github.com/a2aproject/a2a-python/blob/main/docs/migrations/v1_0/README.md)
- [A2A Protocol What's New in v1.0](https://a2a-protocol.org/latest/whats-new-v1/)
- [a2a-python SDK on GitHub](https://github.com/a2aproject/a2a-python)
- [a2a-sdk on PyPI](https://pypi.org/project/a2a-sdk/)

**Protobuf JSON Format (why the enums changed):**
- [ProtoJSON Specification](https://protobuf.dev/programming-guides/proto3/#json)

**Workshop Repository:**
- [When Agents Talk — Workshop Code](https://github.com/dinabavli/a2a_mcp_workshop) *(link to repo)*

**Related Posts in This Series:**
- **Part 1**: [The Language of Multi-Agent AI](post1_terminology.md)
- **Part 2**: [Your First Multi-Agent System — No LLM Tokens Required](post2_no_llm.md)
- **Part 3**: [Three Patterns for Agent Intelligence](post3_patterns.md)
- **Part 4**: [When Agents Talk in Production](post4_production.md)

---

*Written by Dina Bavli · Data Scientist | NLP | AI Systems · ❤ sharing knowledge and contributing to the community*
