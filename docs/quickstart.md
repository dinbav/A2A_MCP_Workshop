# Quick Start Guide

This guide walks you from zero to a running multi-agent system. Choose the track that matches your situation.

---

## Choose Your Track

| | Personalized Learning | Travel Activity Planner |
|--|----------------------|------------------------|
| **API key needed?** | No — 100% offline for agents | Yes — Azure OpenAI required |
| **Internet required?** | No | Yes (Open-Meteo + Nominatim) |
| **Best for** | First-time workshop, exploring A2A+MCP | LLM + MCP integration, live data |
| **Recommended first** | Yes | After completing Learning track |

---

## Track A — Personalized Learning (No API Key)

### Step 1 — Prerequisites

- Python 3.11 or higher
- PowerShell (Windows) or PowerShell Core (macOS/Linux)
- Git

```powershell
python --version   # should print 3.11.x or higher
```

### Step 2 — Install

```powershell
cd use_cases/personalized_learning
pip install -e .
```

### Step 3 — Configure Environment

```powershell
cp .env.example .env
```

Open `.env`. For this track you only need credentials if you want to run the **Orchestrator Agent** (which uses Azure OpenAI for routing). The three remote agents and all MCP tests work without any credentials.

```env
# Required only to run the Orchestrator Agent:
AZURE_OPENAI_ENDPOINT=https://YOUR_RESOURCE.openai.azure.com
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
AZURE_OPENAI_API_VERSION=2024-02-01
OPENAI_API_KEY=your-api-key-here

# Leave as-is:
MCP_SERVER_URL=http://127.0.0.1:8004/mcp
```

### Step 4 — Start All Services

```powershell
.\start_all.ps1
```

This starts five processes in background windows:
1. MCP Server → port 8004
2. Topic Explainer Agent → port 8091
3. Assessment Agent → port 8092
4. Study Plan Agent → port 8093
5. Learning Orchestrator → port 8090

To also open the Streamlit MCP Playground:
```powershell
.\start_all.ps1 -UI
```

To stop everything:
```powershell
.\start_all.ps1 -Stop
```

### Step 5 — Verify Services Are Running

Open these URLs in your browser or run the curl commands. Each should return a JSON response.

```powershell
# MCP Server health
curl http://localhost:8004/health

# Agent Cards (one per agent)
curl http://localhost:8090/.well-known/agent-card.json
curl http://localhost:8091/.well-known/agent-card.json
curl http://localhost:8092/.well-known/agent-card.json
curl http://localhost:8093/.well-known/agent-card.json
```

### Step 6 — Run Tests

```powershell
# Fast: MCP tools only — no agents or API key needed
python tests/run_all_tests.py --skip-agents

# Full suite — all five services must be running
python tests/run_all_tests.py

# Individual groups
python tests/run_all_tests.py --only mcp
python tests/run_all_tests.py --only topic
python tests/run_all_tests.py --only assessment
python tests/run_all_tests.py --only study
python tests/run_all_tests.py --only e2e
python tests/run_all_tests.py --only memory

# Verbose output
python tests/run_all_tests.py --verbose
```

### Step 7 — Send Your First Message

Use the interactive CLI client to talk to the Orchestrator:

```powershell
python a2a_agents/client.py
```

Try these prompts:
```
Explain MCP for a beginner.
Give me a short quiz for A2A.
Build me a 2-hour study plan for MCP.
I want to learn RAG. Assess my level and build me a 1-day study plan.
```

### Step 8 — Explore the MCP Playground (Optional)

If you started with `-UI`, open [http://localhost:8504](http://localhost:8504) in your browser to call MCP tools directly without going through the agents.

---

## Track B — Travel Activity Planner (Azure OpenAI Required)

### Step 1 — Prerequisites

- Python 3.11 or higher
- PowerShell
- Git
- An Azure OpenAI resource with a deployment named (or renamed to) `gpt-4o`
- Internet access (the Weather agent calls Open-Meteo and Nominatim)

### Step 2 — Install

```powershell
cd use_cases/travel_activity_planner
pip install -e .
```

### Step 3 — Configure Environment

```powershell
cp .env.example .env
```

Fill in your Azure OpenAI credentials:

```env
AZURE_OPENAI_ENDPOINT=https://YOUR_RESOURCE.openai.azure.com
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
AZURE_OPENAI_API_VERSION=2024-02-01
OPENAI_API_KEY=your-api-key-here

# Leave as-is:
MCP_SERVER_URL=http://127.0.0.1:8003/mcp
```

| Variable | Description |
|----------|-------------|
| `AZURE_OPENAI_ENDPOINT` | Your Azure resource URL — find it in Azure Portal under "Keys and Endpoint" |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | The name of your deployed model (must be a GPT-4 class model) |
| `AZURE_OPENAI_API_VERSION` | API version — keep the default value unless you have a specific reason to change it |
| `OPENAI_API_KEY` | Your API key from Azure Portal |
| `MCP_SERVER_URL` | URL of the MCP server — keep as-is for local development |

### Step 4 — Start All Services

```powershell
.\start_all.ps1
```

This starts:
1. MCP Server → port 8003
2. Packing List Agent → port 8081
3. Weather & Activity Agent → port 8082
4. Local Tips Agent → port 8083
5. Orchestrator Agent → port 8080

```powershell
.\start_all.ps1 -UI      # also opens Streamlit MCP Playground on :8504
.\start_all.ps1 -Stop    # stop everything
```

### Step 5 — Verify Services Are Running

```powershell
curl http://localhost:8003/health
curl http://localhost:8080/.well-known/agent-card.json
curl http://localhost:8081/.well-known/agent-card.json
curl http://localhost:8082/.well-known/agent-card.json
curl http://localhost:8083/.well-known/agent-card.json
```

### Step 6 — Run Tests

```powershell
# Fast: MCP tools only (no agents or API key needed)
python tests/run_all_tests.py --skip-agents

# Full suite
python tests/run_all_tests.py

# Individual groups
python tests/run_all_tests.py --only mcp
python tests/run_all_tests.py --only agents
python tests/run_all_tests.py --only local-tips
```

### Step 7 — Send Your First Message

```powershell
python a2a_agents/client.py
```

Try these prompts:
```
What is the weather in Tel Aviv next Friday?
What activities do you recommend in Paris in December?
I am going to Barcelona for a week. What should I pack?
Give me local tips for Rome.
```

### Step 8 — MCP Playground (Optional)

Open [http://localhost:8504](http://localhost:8504) to call MCP tools directly.

---

## Google Colab

If you do not want to install anything locally, the Personalized Learning use case has a Colab notebook:

[`use_cases/personalized_learning/workshop_colab.ipynb`](../use_cases/personalized_learning/workshop_colab.ipynb)

Open it in Google Colab and follow the cells — everything runs in the cloud.

---

## Multi-Turn Conversations

Both use cases support multi-turn memory — agents remember what was said earlier in the same conversation. This feature ships as a workshop exercise with commented-out code.

See `MULTI_TURN_GUIDE.md` in each use case for step-by-step instructions:
- [Travel — Multi-Turn Guide](../use_cases/travel_activity_planner/MULTI_TURN_GUIDE.md)
- [Learning — Multi-Turn Guide](../use_cases/personalized_learning/MULTI_TURN_GUIDE.md)

---

## What to Read Next

| Goal | Document |
|------|----------|
| Understand the terminology | [`docs/glossary.md`](glossary.md) |
| Understand the architecture | [`docs/architecture.md`](architecture.md) |
| Run workshop exercises | [`use_cases/personalized_learning/docs/exercises.md`](../use_cases/personalized_learning/docs/exercises.md) |
| Add a new topic or agent | [`use_cases/personalized_learning/docs/extending.md`](../use_cases/personalized_learning/docs/extending.md) |
| Fix a problem | [Travel troubleshooting](../use_cases/travel_activity_planner/docs/troubleshooting.md) · [Learning troubleshooting](../use_cases/personalized_learning/docs/troubleshooting.md) |
