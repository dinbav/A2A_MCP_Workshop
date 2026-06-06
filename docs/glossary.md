# Glossary — A2A and MCP Concepts

This guide explains every term used in this workshop in plain language. Each entry includes an analogy, a precise definition, and a pointer to the relevant code.

No prior knowledge of A2A or MCP is assumed.

---

## A2A Protocol

**What it is:** A standardized HTTP protocol for agents to send tasks to each other and stream back responses.

**Analogy:** Like a REST API between microservices, but designed specifically for AI agents — it defines how to send a message, how to receive a streaming response, how to identify a conversation, and how each agent advertises its capabilities.

**Key ideas:**
- Every agent exposes an HTTP server.
- Clients send a `Task` (a message + optional history) to an agent's endpoint.
- The agent responds with a stream of events (`working`, `completed`, `failed`, `input_required`).
- Agents discover each other through **Agent Cards**.

**Spec:** [google.github.io/A2A](https://google.github.io/A2A/)  
**SDK used in this repo:** `a2a-sdk==0.3.22`  
**How it starts:** [`a2a_agents/server_factory.py`](../use_cases/travel_activity_planner/a2a_agents/server_factory.py)

---

## MCP — Model Context Protocol

**What it is:** A standardized protocol for agents to call named tools on a server, instead of making raw API calls.

**Analogy:** Like a plugin system. The MCP server exposes a menu of named functions ("tools"). Any agent that speaks MCP can discover and call those tools without knowing how they are implemented.

**Key ideas:**
- The MCP server is a separate process that exposes tools over HTTP (at `/mcp`).
- Agents call `call_tool(name, arguments)` and receive structured JSON back.
- Tools are tagged (e.g. `weather`, `assessment`, `career`) so agents can filter by topic.
- This repo uses [FastMCP](https://github.com/jlowin/fastmcp) to define tools as plain Python functions.

**Spec:** [modelcontextprotocol.io](https://modelcontextprotocol.io/)  
**Travel tools:** [`use_cases/travel_activity_planner/mcp/fastmcp_server.py`](../use_cases/travel_activity_planner/mcp/fastmcp_server.py)  
**Learning tools:** [`use_cases/personalized_learning/mcp/fastmcp_server.py`](../use_cases/personalized_learning/mcp/fastmcp_server.py)

---

## Agent Card

**What it is:** A JSON document at `/.well-known/agent-card.json` that describes what an agent can do.

**Analogy:** A business card. Before the Orchestrator routes a message to an agent, it reads the card to understand that agent's name, skills, and keywords.

**Key fields:**
```json
{
  "name": "Weather & Activity Agent",
  "description": "Provides weather forecasts and activity suggestions",
  "skills": [
    {
      "id": "weather_forecast",
      "name": "Weather Forecast",
      "tags": ["weather", "forecast", "temperature"]
    }
  ]
}
```

**How routing works:** The Orchestrator extracts tags and example phrases from every card, builds a keyword index, and scores incoming messages against it.

**Where defined:** `a2a_agents/*/agent_card.py` in each use case  
**How the Orchestrator loads them:** [`a2a_agents/orchestrator_agent/agent_logic.py`](../use_cases/travel_activity_planner/a2a_agents/orchestrator_agent/agent_logic.py) — `_ensure_initialized()`  
**Registry of agent URLs:** [`a2a_agents/orchestrator_agent/agents_registry.json`](../use_cases/travel_activity_planner/a2a_agents/orchestrator_agent/agents_registry.json)

---

## Orchestrator Agent

**What it is:** The entry-point agent. It receives every user message, reads all Agent Cards, scores keyword matches, and forwards the request to the best-matching specialist agent(s).

**Analogy:** A dispatcher or router. It does not answer domain questions itself — it decides *who* should answer.

**Routing algorithm:**
1. On startup, fetch the Agent Card from each URL in `agents_registry.json`.
2. Build a keyword index from skills, tags, and description phrases.
3. For each incoming message, score every agent by keyword overlap.
4. Call all agents whose score is within 50% of the top score (allows multi-agent responses).
5. Stream each response back to the user.

**Uses LLM:** Yes — for the Orchestrator in both use cases.

**Where defined:**
- Travel: [`use_cases/travel_activity_planner/a2a_agents/orchestrator_agent/`](../use_cases/travel_activity_planner/a2a_agents/orchestrator_agent/)
- Learning: [`use_cases/personalized_learning/a2a_agents/orchestrator_agent/`](../use_cases/personalized_learning/a2a_agents/orchestrator_agent/)

---

## Remote Agent

**What it is:** A specialist agent that handles one domain. It receives a forwarded A2A task from the Orchestrator, does its work (calling MCP tools, querying an LLM, etc.), and streams back a response.

**Analogy:** A specialist consultant. The Orchestrator is the generalist who decides who to call; remote agents are the experts who actually answer.

**Two implementation styles in this repo:**

| Style | Description | Examples |
|-------|-------------|---------|
| **LLM + MCP loop** | Binds MCP tools to an LLM (LangChain); the model decides which tools to call | Weather & Activity Agent, Packing List Agent |
| **Rule-based MCP caller** | Parses the input with regex/keywords, calls the right MCP tool directly, formats output | Local Tips Agent, all three Learning agents |

> **Note on Personalized Learning:** all three remote agents (Topic Explainer, Assessment, Study Plan) are rule-based. They make **zero LLM calls** and run completely offline.

**Standard file layout per agent:**
```
remote_agents/my_agent/
├── __init__.py
├── __main__.py        # entry point — calls server_factory.run()
├── agent_card.py      # Agent Card JSON
├── agent_executor.py  # thin A2A executor
└── agent_logic.py     # business logic — implements stream()
```

---

## Skill

**What it is:** A named capability declared in an Agent Card. Each skill has an `id`, a `name`, a description, and a list of `tags` used for routing.

**Analogy:** A line item on a consultant's CV. The Orchestrator reads skill tags to decide whether an agent is relevant to a given message.

**Example:**
```json
{
  "id": "local_tips",
  "name": "Local Tips",
  "tags": ["local", "tips", "city", "restaurant", "culture"]
}
```

**Where defined:** In every `agent_card.py` file, under the `skills` list.

---

## Tool

**What it is:** A Python function exposed by an MCP server. Agents call tools by name and receive structured JSON back.

**Analogy:** A named endpoint on a REST API, but discoverable and typed — the MCP client can list available tools and their input schemas before calling them.

**How to define a tool (FastMCP):**
```python
@mcp.tool(tags=["weather"])
def get_weather_for_location_and_date_string(location: str, date_str: str) -> dict:
    ...
```

**Travel tools:** `greet`, `get_weather_for_location_and_date_string`, `suggest_activities_for_location_and_date`, `get_local_tips_by_city`  
**Learning tools:** `get_topic_summary`, `get_assessment_questions_by_topic`, `get_learning_state`, `update_learning_state`, `get_study_path`, `get_job_description`, `get_resume_profile`, `get_skill_gap_analysis`

**Where defined:** `mcp/fastmcp_server.py` in each use case.

---

## Context ID

**What it is:** A UUID that identifies a conversation session. All messages in the same conversation carry the same context ID so agents can retrieve and append to the conversation history.

**Analogy:** A session ID in a web application. Without it, every message would be treated as a new conversation.

**How it works:**
1. The A2A client creates a `context_id` on the first message.
2. The Orchestrator forwards the same `context_id` when calling remote agents.
3. `BaseAgentExecutor` reads the task history (all previous messages in the context) and passes it to `AgentLogic.stream()`.
4. The agent includes history when calling the LLM or MCP tool, producing context-aware responses.

**Multi-turn workshop:** See `MULTI_TURN_GUIDE.md` in each use case for a step-by-step exercise.

**Where implemented:** [`a2a_agents/base_executor.py`](../use_cases/travel_activity_planner/a2a_agents/base_executor.py)

---

## Task

**What it is:** The A2A unit of work. A Task contains the current user message, the conversation history, a context ID, and metadata. Agents receive a Task and respond with a stream of events.

**Task event types:**

| Event type | Meaning |
|-----------|---------|
| `working` | Agent is processing; may include partial output |
| `completed` | Agent has finished; contains the final response |
| `failed` | Agent encountered an error |
| `input_required` | Agent needs more information from the user |

**Where used:** `a2a_agents/base_executor.py` — the `execute()` method receives a Task context and yields events.

---

## BaseAgentExecutor

**What it is:** A shared base class that handles all A2A protocol plumbing. It reads the incoming Task, extracts the message and history, calls `AgentLogic.stream()`, and maps the yielded dicts back to A2A streaming events.

**Why it exists:** Every agent needs the same boilerplate to unpack A2A tasks and emit events. `BaseAgentExecutor` provides this once so each agent only needs to implement its own `stream()` logic.

**What each agent adds:** A concrete `AgentExecutor` subclass that overrides `_make_logic()` to return the domain-specific `AgentLogic` instance.

**Where defined:** `a2a_agents/base_executor.py` in each use case.

---

## server_factory

**What it is:** A shared helper module that bootstraps a Starlette + uvicorn HTTP server for any agent. Called from each agent's `__main__.py`.

**Why it exists:** All agents share the same server setup — CORS middleware, A2A request handler, health check endpoint, port configuration. `server_factory.py` provides this once.

**Where defined:** `a2a_agents/server_factory.py` in each use case.

---

## agents_registry.json

**What it is:** A JSON file that lists the URLs of all remote agents. The Orchestrator reads this on startup to know which agents exist and where to find their Agent Cards.

**Format:**
```json
[
  { "name": "Packing List Agent",       "url": "http://localhost:8081" },
  { "name": "Weather & Activity Agent", "url": "http://localhost:8082" },
  { "name": "Local Tips Agent",         "url": "http://localhost:8083" }
]
```

**Where defined:** `a2a_agents/orchestrator_agent/agents_registry.json` in each use case.
