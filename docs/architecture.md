# System Architecture

This document covers the architecture shared by both use cases, with three levels of detail:
1. High-level component model
2. Message flow for a single request
3. Internal anatomy of a single agent

For use-case-specific diagrams see:
- [Travel Activity Planner — Architecture](../use_cases/travel_activity_planner/docs/architecture.md)
- [Personalized Learning — Architecture](../use_cases/personalized_learning/docs/architecture.md)

---

## 1. High-Level Component Model

Every system in this repo follows the same pattern regardless of use case.

```mermaid
flowchart LR
    User["User\n(CLI / Tests / Streamlit UI)"]

    subgraph a2a [A2A Layer]
        Orch["Orchestrator Agent\n(keyword routing via Agent Cards)"]
        RA1["Remote Agent A"]
        RA2["Remote Agent B"]
        RA3["Remote Agent C"]
    end

    subgraph mcp [MCP Layer]
        MCP["MCP Server\n(FastMCP — tools + data)"]
    end

    User -->|"A2A send_message"| Orch
    Orch -->|"reads Agent Cards\nat startup"| Orch
    Orch -->|"A2A send_message"| RA1
    Orch -->|"A2A send_message"| RA2
    Orch -->|"A2A send_message"| RA3
    RA1 -->|"MCP call_tool"| MCP
    RA2 -->|"MCP call_tool"| MCP
    RA3 -->|"MCP call_tool"| MCP
```

**A2A layer** — agents communicate over HTTP using the A2A protocol. Each agent is a separate process with its own port.  
**MCP layer** — the MCP server is a single FastMCP process. Agents call it to access tools and data.

---

## 2. Message Flow — Single Request

What happens from the moment a user sends a message to the moment they receive a response.

```mermaid
sequenceDiagram
    participant U as User / Client
    participant O as Orchestrator Agent
    participant R as Remote Agent
    participant M as MCP Server

    U->>O: A2A Task {message, context_id, history}
    O->>O: fetch Agent Cards from agents_registry.json
    O->>O: score keywords → select best agent(s)
    O->>R: A2A Task {forwarded message, context_id}
    alt Rule-based agent
        R->>R: parse input (regex / keywords)
        R->>M: call_tool(name, arguments)
        M-->>R: JSON result
        R->>R: format response
    else LLM + MCP agent
        R->>R: bind MCP tools to LLM
        loop tool-call iterations (up to 5)
            R->>M: call_tool(name, arguments)
            M-->>R: JSON result
        end
    end
    R-->>O: streaming A2A events {working → completed}
    O-->>U: streaming response
```

**context_id** — forwarded at every step so all agents share the same conversation session. This is how multi-turn memory works.

---

## 3. Internal Anatomy of an Agent

Every agent (Orchestrator or Remote) is structured the same way internally.

```mermaid
flowchart TB
    subgraph process [Agent Process]
        main["__main__.py\nEntry point — calls server_factory.run()"]
        factory["server_factory.py\nBootstraps Starlette + uvicorn server"]
        card["agent_card.py\nAgent Card JSON\n(served at /.well-known/agent-card.json)"]
        executor["agent_executor.py\nA2A executor — creates AgentLogic instance"]
        base["base_executor.py\nShared A2A bridge:\n• unpacks Task\n• reads history\n• maps events to A2A stream"]
        logic["agent_logic.py\nBusiness logic — implements stream()\n• calls MCP tools\n• calls LLM (if applicable)\n• yields result dicts"]
    end

    main --> factory
    factory --> card
    factory --> executor
    executor --> base
    executor --> logic
    base --> logic
```

**What you implement** when adding a new agent: only `agent_card.py` and `agent_logic.py`. Everything else is shared infrastructure.

---

## 4. Orchestrator Routing Logic

```mermaid
flowchart TD
    Start["Incoming user message"]
    Init["First message?\nFetch all Agent Cards\nBuild keyword index"]
    Score["Score each agent\nby keyword overlap\nwith message tokens"]
    Threshold["Select agents with score\n≥ 50% of top score"]
    Multi{"Multiple agents\nselected?"}
    Single["Call one agent\nstream response"]
    Parallel["Call agents in parallel\nmerge streams"]
    Response["Return response to user"]

    Start --> Init
    Init --> Score
    Score --> Threshold
    Threshold --> Multi
    Multi -->|No| Single
    Multi -->|Yes| Parallel
    Single --> Response
    Parallel --> Response
```

The 50% threshold intentionally allows multi-agent responses for queries that span domains (e.g. "What should I pack and what is the weather like?").

---

## 5. Port Reference

### Travel Activity Planner

| Service | Port | File |
|---------|------|------|
| MCP Server | 8003 | `mcp/fastmcp_server.py` |
| Orchestrator Agent | 8080 | `a2a_agents/orchestrator_agent/__main__.py` |
| Packing List Agent | 8081 | `a2a_agents/remote_agents/packing_list_agent/__main__.py` |
| Weather & Activity Agent | 8082 | `a2a_agents/remote_agents/weather_activity_agent/__main__.py` |
| Local Tips Agent | 8083 | `a2a_agents/remote_agents/local_tips_agent/__main__.py` |
| Streamlit UI (optional) | 8504 | `ui/mcp_playground.py` |

### Personalized Learning

| Service | Port | File |
|---------|------|------|
| MCP Server | 8004 | `mcp/fastmcp_server.py` |
| Learning Orchestrator | 8090 | `a2a_agents/orchestrator_agent/__main__.py` |
| Topic Explainer Agent | 8091 | `a2a_agents/remote_agents/topic_explainer_agent/__main__.py` |
| Assessment Agent | 8092 | `a2a_agents/remote_agents/assessment_agent/__main__.py` |
| Study Plan Agent | 8093 | `a2a_agents/remote_agents/study_plan_agent/__main__.py` |
| Streamlit UI (optional) | 8504 | `ui/mcp_playground.py` |
