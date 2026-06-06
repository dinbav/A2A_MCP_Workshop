# Troubleshooting — Travel Activity Planner

---

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
# Find which process holds a port (example: 8082)
netstat -ano | findstr ":8082"
# Kill by PID:
taskkill /PID <pid> /F
```

Ports used by this use case: **8003, 8080, 8081, 8082, 8083, 8504** (optional).

### ImportError on startup

```
ImportError: No module named 'fastmcp'
```

**Fix:**
```powershell
cd use_cases/travel_activity_planner
pip install -e .
```

---

## Azure OpenAI Issues

### Authentication error

```
openai.AuthenticationError: 401 Unauthorized
openai.NotFoundError: 404 The API deployment 'gpt-4o' does not exist
```

**Check your `.env` file:**
```env
AZURE_OPENAI_ENDPOINT=https://YOUR_RESOURCE.openai.azure.com   # no trailing slash
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o                            # must match your deployment name exactly
AZURE_OPENAI_API_VERSION=2024-02-01
OPENAI_API_KEY=your-api-key-here
```

Find these values in the Azure Portal → your OpenAI resource → **Keys and Endpoint**.

### Rate limit / quota exceeded

```
openai.RateLimitError: 429 Too Many Requests
```

**Fix:** Wait 60 seconds and retry. If it persists, check your Azure OpenAI quota in the Azure Portal under **Quotas**.

### `.env` file not found

```
python-dotenv: .env file not found
```

**Fix:**
```powershell
cp .env.example .env
# Then edit .env with your credentials
```

---

## MCP Server Issues

### MCP server not reachable at `http://127.0.0.1:8003/mcp`

1. Check if the MCP server process is running:
   ```powershell
   netstat -ano | findstr ":8003"
   ```
2. Check the MCP server terminal window for error messages.
3. Try starting the MCP server manually:
   ```powershell
   python mcp/fastmcp_server.py
   ```
4. Verify the data files exist:
   ```powershell
   ls mcp/data/
   ```

### Agent returns "No MCP tools available"

The agent cannot reach the MCP server.

1. Verify MCP server is running: `python tests/run_all_tests.py --only mcp`
2. Check `MCP_SERVER_URL` in `.env` — should be `http://127.0.0.1:8003/mcp`.
3. If you are behind a corporate proxy, set `NO_PROXY=127.0.0.1,localhost` in your environment.

---

## Geocoding and Weather Issues

### Location not found

```
GeocoderUnavailable: HTTPSConnectionPool: Max retries exceeded
GeocoderTimedOut
```

**Cause:** The Weather & Activity Agent uses [Nominatim](https://nominatim.org/) to geocode location names. Nominatim requires internet access and may rate-limit requests.

**Fix:**
- Verify you have internet access.
- Use specific city names (e.g. `"Paris, France"` instead of just `"Paris"`).
- Wait 1–2 seconds between requests if running many tests.

### Open-Meteo API error

```
requests.exceptions.ConnectionError
```

**Cause:** The weather data comes from [Open-Meteo](https://open-meteo.com/) — a free, no-key weather API. It requires internet.

**Fix:** Check your internet connection. The API has no authentication — if you can reach `open-meteo.com` in a browser, the agent will work.

### Invalid date format

The weather tool accepts natural-language dates (`"next Friday"`, `"December 25"`, `"2024-12-25"`). If you see a date parsing error, try a more explicit format like `YYYY-MM-DD`.

---

## Agent Issues

### Orchestrator routes to wrong agent

The keyword routing uses the skill tags in each Agent Card. Try adding more descriptive words to your message. Example:

- Too vague: `"Plan something for Rome"` → may not match
- Better: `"Local tips and restaurants in Rome"` → matches Local Tips Agent

If you modify skill tags, restart all services to reload the cards.

### Orchestrator returns "No suitable agent found"

No keyword overlap with any agent's skills. Try rephrasing the message or check that all three remote agents are running:

```powershell
curl http://localhost:8081/.well-known/agent-card.json
curl http://localhost:8082/.well-known/agent-card.json
curl http://localhost:8083/.well-known/agent-card.json
```

### Packing List Agent returns generic list

The Packing List Agent is an LLM-only agent (no MCP calls). If it returns very generic output, check that your Azure OpenAI credentials are valid and the deployment is a GPT-4 class model.

---

## Test Issues

### Tests fail with "Server not reachable"

Run `.\start_all.ps1` before running tests. All tests require the services to be running.

### MCP tests pass but agent tests fail

Agent tests require both the MCP server and the A2A agents. Start all services first:
```powershell
.\start_all.ps1
python tests/run_all_tests.py
```

### Agent tests time out

Default timeout is 90 seconds. Possible causes:
- Azure OpenAI quota exhausted → check Portal
- Geocoding API timeout → check internet connection
- Agent process crashed → check its terminal window

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

This is handled automatically by `server_factory.py` and `client.py`. If you see encoding errors in a custom script, add:
```python
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
```

---

## Checking Service Health

```powershell
# Check all ports at once
netstat -ano | findstr ":800"

# Agent card for each service
curl http://localhost:8080/.well-known/agent-card.json
curl http://localhost:8081/.well-known/agent-card.json
curl http://localhost:8082/.well-known/agent-card.json
curl http://localhost:8083/.well-known/agent-card.json

# MCP server health
curl http://localhost:8003/health
```

Or run the fast test suite (MCP only, no agents needed):
```powershell
python tests/run_all_tests.py --skip-agents
```
