# Troubleshooting

## Service Won't Start

### Port already in use

```
ERROR: [Errno 10048] Only one usage of each socket address is permitted
```

**Fix:**
```powershell
.\start_all.ps1 -Stop
.\start_all.ps1
```

Or kill a specific port manually:
```powershell
netstat -ano | findstr ":8004"
# Find the PID and kill it:
taskkill /PID <pid> /F
```

### ImportError on startup

```
ImportError: No module named 'fastmcp'
```

**Fix:**
```powershell
cd use_cases/personalized_learning
pip install -e .
```

---

## MCP Server Issues

### MCP server not reachable at http://127.0.0.1:8004/mcp

1. Check if the MCP server process is running:
   ```powershell
   netstat -ano | findstr ":8004"
   ```
2. Check the MCP server terminal window for error messages.
3. Try restarting just the MCP server:
   ```powershell
   python mcp/fastmcp_server.py
   ```
4. Verify the data files exist:
   ```powershell
   ls mcp/data/learning/
   ls mcp/data/career/
   ```

### Tool returns "not found" for a valid topic

The tool normalizes topics by replacing spaces with underscores and lowercasing. Make sure you use `mcp`, `a2a`, `rag`, `prompt_engineering`, or `python_async` (with underscore, not space).

**Valid:** `prompt_engineering`
**Invalid:** `Prompt Engineering`

### update_learning_state not persisting between server restarts

This is expected — the current implementation uses an in-memory dict seeded from `user_learning_state.json`. The state resets on every server restart. See `docs/extending.md` for how to add persistence.

---

## Agent Issues

### Agent returns "No MCP tools available"

The agent cannot reach the MCP server.

1. Verify MCP server is running: `python tests/run_all_tests.py --only mcp`
2. Check `MCP_SERVER_URL` in your `.env` file — it should be `http://127.0.0.1:8004/mcp`.
3. Check `NO_PROXY` environment variable if you are behind a proxy.

### Orchestrator returns Azure OpenAI error

```
openai.AuthenticationError: 401 Unauthorized
```

The three remote agents (Topic Explainer, Assessment, Study Plan) do **not** use an LLM — only the Orchestrator does.

**Fix:** Check your `.env` file has valid credentials for the Orchestrator:
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_DEPLOYMENT_NAME`
- `AZURE_OPENAI_API_VERSION`
- `OPENAI_API_KEY`

You can still run all agent tests and MCP tests without valid credentials by talking directly to a remote agent (bypassing the Orchestrator).

### Agent or Orchestrator times out

The default test timeout is 90 seconds.

- If Orchestrator tests time out: check your Azure OpenAI quota and rate limits.
- If remote agent tests time out: verify the MCP server is running at port 8004.

---

## Orchestrator Issues

### Orchestrator routes to wrong agent

The keyword routing uses the agent card skills. If you add new skills or examples, restart all services to reload the agent cards.

Check the orchestrator log — it prints `[Orchestrator] Could not discover agent ...` if an agent is unreachable.

### Orchestrator returns "No suitable agent found"

The user input had no keyword overlap with any agent's skills. Try adding more descriptive words or check that all 3 remote agents are running.

### context_id not threading through

If follow-up questions lose context, check that the orchestrator is forwarding `context_id`:

In `a2a_agents/orchestrator_agent/agent_logic.py`:
```python
msg.context_id = context_id
```

This line must be present and `context_id` must be passed from the executor.

---

## Test Issues

### Tests fail with "Server not reachable"

Run `.\start_all.ps1` first. All tests require the services to be running.

### MCP tests pass but agent tests fail

Agent tests require both MCP server and the A2A agents to be running. MCP-only tests just need the MCP server.

### test_memory.py exits without printing responses

The multi-turn test requires the orchestrator to be running. Verify:
```powershell
python tests/run_all_tests.py --only orchestrator
```

---

## Windows-Specific Issues

### PowerShell execution policy

```
.\start_all.ps1 cannot be loaded because running scripts is disabled
```

**Fix:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Encoding errors in terminal output

Add at the top of any Python script:
```python
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
```

This is already done in `server_factory.py` and `client.py`.

---

## Checking Service Health

```powershell
# Check all ports
netstat -ano | findstr ":809"
netstat -ano | findstr ":8004"

# Quick HTTP check for each agent card
curl http://localhost:8091/.well-known/agent-card.json
curl http://localhost:8092/.well-known/agent-card.json
curl http://localhost:8093/.well-known/agent-card.json
curl http://localhost:8090/.well-known/agent-card.json
```

Or use the test suite:
```powershell
python tests/run_all_tests.py --skip-agents  # MCP only, fastest
python tests/run_all_tests.py --only mcp     # Same thing
```
