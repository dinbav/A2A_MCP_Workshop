# A2A Agents — Personalized Learning

This directory contains the orchestrator and all three specialist agents.

## Architecture

```
a2a_agents/
├── base_executor.py          # Shared executor with history forwarding
├── server_factory.py         # Starlette/uvicorn A2A bootstrap
├── client.py                 # Interactive CLI client (port 8090)
│
├── orchestrator_agent/       # Port 8090
│   ├── agent_card.py         # Routing skill
│   ├── agent_logic.py        # Keyword scoring + routing
│   ├── agent_executor.py     # Forwards context_id to remote agents
│   ├── agents_registry.json  # URLs for all 3 remote agents
│   └── __main__.py
│
└── remote_agents/
    ├── topic_explainer_agent/   # Port 8091 — rule-based MCP caller (topic/level parsing)
    ├── assessment_agent/        # Port 8092 — rule-based MCP caller (quiz/score/level flows)
    └── study_plan_agent/        # Port 8093 — rule-based MCP caller (study + career flows)
```

## Routing Logic

The orchestrator discovers each remote agent's Agent Card on startup and builds a keyword index from:
- Agent description
- Skill names, descriptions, tags
- Skill examples

For each user message, it scores agents by counting keyword overlaps. Agents within 50% of the top score are all called.

**Examples:**

| User input | Likely winner |
|-----------|--------------|
| "Explain MCP for a beginner" | Topic Explainer (explain, mcp, beginner) |
| "Quiz me on A2A" | Assessment Agent (quiz, a2a) |
| "Build me a study plan" | Study Plan Agent (study, plan) |
| "Assess my level and build a plan" | Assessment + Study Plan (both score high) |

## Multi-Turn Memory

All agents receive `history` from the A2A task store and concatenate prior message texts to build context for topic/intent parsing. The orchestrator forwards `context_id` to all remote agents. See `MULTI_TURN_GUIDE.md`.

## Ports

| Agent | Port |
|-------|------|
| Learning Orchestrator | 8090 |
| Topic Explainer Agent | 8091 |
| Assessment Agent | 8092 |
| Study Plan Agent | 8093 |
