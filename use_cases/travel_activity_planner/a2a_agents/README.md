# A2A Agents

Multi-agent trip-planning system: one orchestrator routes requests to three specialised remote agents.

## Architecture

```
                    User
                      |
              Orchestrator :8080
            (keyword-based routing)
           /           |            \
  Packing         Weather &       Local Tips
  Agent :8081   Activity :8082    Agent :8083
      |               |               |
      +---------------+---------------+
                      |
                 MCP Server :8003
```

## Agents

| Agent | Port | Skills | LLM | MCP |
|-------|------|--------|-----|-----|
| Orchestrator | 8080 | Routes requests to best-matching agent | — | — |
| Weather & Activity | 8082 | Weather forecast, activity suggestions | Azure OpenAI | yes |
| Packing List | 8081 | Packing lists, trip invitations | Azure OpenAI | — |
| Local Tips | 8083 | City-specific travel tips | — | yes |

## Running

```powershell
# Launch all agents + MCP server
.\start_all.ps1

# With Streamlit UIs
.\start_all.ps1 -UI

# Stop all
.\start_all.ps1 -Stop
```

Or start each agent individually:

```powershell
python -m a2a_agents.orchestrator_agent         # :8080
python -m a2a_agents.remote_agents.packing_list_agent     # :8081
python -m a2a_agents.remote_agents.weather_activity_agent # :8082
python -m a2a_agents.remote_agents.local_tips_agent       # :8083
```

## Directory Structure

```
a2a_agents/
├── base_executor.py              # Shared executor base class
├── server_factory.py             # Shared server bootstrap
├── client.py                     # CLI client for the orchestrator
│
├── orchestrator_agent/
│   ├── agent_card.py
│   ├── agent_executor.py         # Forwards A2A events from remote agents
│   ├── agent_logic.py            # Keyword routing + remote agent calls
│   ├── agents_registry.json      # Maps agent names to URLs
│   └── __main__.py
│
└── remote_agents/
    ├── weather_activity_agent/   # LLM + MCP agentic loop
    ├── packing_list_agent/       # LLM-only
    └── local_tips_agent/         # MCP-only (no LLM)
```

## Routing Logic

The orchestrator scores each agent by counting keyword overlaps between the user input and keywords extracted from the agent's card (skill names, tags, descriptions, examples). Agents within 50% of the top score are all called.
