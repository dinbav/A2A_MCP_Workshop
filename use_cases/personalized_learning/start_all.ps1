# start_all.ps1 — Start or stop all Personalized Learning services.
#
# Usage:
#   .\start_all.ps1           # Start MCP server + all agents + orchestrator
#   .\start_all.ps1 -UI       # Also start Streamlit MCP Playground
#   .\start_all.ps1 -Stop     # Kill all service ports
#
# Ports:
#   8004  MCP Server
#   8090  Learning Orchestrator Agent
#   8091  Topic Explainer Agent
#   8092  Assessment Agent
#   8093  Study Plan Agent
#   8504  Streamlit MCP Playground (optional, -UI flag)

param(
    [switch]$Stop,
    [switch]$UI
)

$PORTS = @(8004, 8090, 8091, 8092, 8093)
$UI_PORT = 8504

function Kill-Port($port) {
    $pids = netstat -ano | Select-String ":$port\s" | ForEach-Object {
        ($_ -split '\s+')[-1]
    } | Sort-Object -Unique
    foreach ($p in $pids) {
        if ($p -match '^\d+$' -and $p -ne '0') {
            try { Stop-Process -Id $p -Force -ErrorAction SilentlyContinue } catch {}
        }
    }
}

if ($Stop) {
    Write-Host "Stopping all Personalized Learning services..." -ForegroundColor Yellow
    foreach ($port in ($PORTS + $UI_PORT)) {
        Kill-Port $port
        Write-Host "  Killed port $port"
    }
    Write-Host "Done." -ForegroundColor Green
    exit 0
}

# ---- Kill any stale processes on our ports ----
Write-Host "Cleaning up stale processes..." -ForegroundColor Cyan
foreach ($port in ($PORTS + $UI_PORT)) {
    Kill-Port $port
}
Start-Sleep -Seconds 1

$ROOT = $PSScriptRoot

# ---- MCP Server (:8004) ----
Write-Host "Starting MCP Server on port 8004..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList `
    "-NoExit", "-Command", `
    "cd '$ROOT'; python mcp/fastmcp_server.py" `
    -WindowStyle Normal

Start-Sleep -Seconds 3

# ---- Topic Explainer Agent (:8091) ----
Write-Host "Starting Topic Explainer Agent on port 8091..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList `
    "-NoExit", "-Command", `
    "cd '$ROOT'; python -m a2a_agents.remote_agents.topic_explainer_agent" `
    -WindowStyle Normal

Start-Sleep -Seconds 2

# ---- Assessment Agent (:8092) ----
Write-Host "Starting Assessment Agent on port 8092..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList `
    "-NoExit", "-Command", `
    "cd '$ROOT'; python -m a2a_agents.remote_agents.assessment_agent" `
    -WindowStyle Normal

Start-Sleep -Seconds 2

# ---- Study Plan Agent (:8093) ----
Write-Host "Starting Study Plan Agent on port 8093..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList `
    "-NoExit", "-Command", `
    "cd '$ROOT'; python -m a2a_agents.remote_agents.study_plan_agent" `
    -WindowStyle Normal

Start-Sleep -Seconds 2

# ---- Orchestrator (:8090) ----
Write-Host "Starting Learning Orchestrator on port 8090..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList `
    "-NoExit", "-Command", `
    "cd '$ROOT'; python -m a2a_agents.orchestrator_agent" `
    -WindowStyle Normal

Start-Sleep -Seconds 3

# ---- Optional Streamlit UI ----
if ($UI) {
    Write-Host "Starting Streamlit MCP Playground on port $UI_PORT..." -ForegroundColor Cyan
    Start-Process powershell -ArgumentList `
        "-NoExit", "-Command", `
        "cd '$ROOT'; streamlit run ui/mcp_playground.py --server.port $UI_PORT" `
        -WindowStyle Normal
    Start-Sleep -Seconds 2
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host " Personalized Learning Services Running" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host "  MCP Server              http://localhost:8004/mcp"
Write-Host "  Orchestrator            http://localhost:8090"
Write-Host "  Topic Explainer Agent   http://localhost:8091"
Write-Host "  Assessment Agent        http://localhost:8092"
Write-Host "  Study Plan Agent        http://localhost:8093"
if ($UI) {
    Write-Host "  MCP Playground (UI)     http://localhost:$UI_PORT"
}
Write-Host ""
Write-Host "Quick tests:"
Write-Host "  python tests/run_all_tests.py --skip-agents   # MCP tools only (fast)"
Write-Host "  python tests/run_all_tests.py                 # Full test suite"
Write-Host ""
Write-Host "Interactive client:"
Write-Host "  python a2a_agents/client.py"
Write-Host ""
Write-Host "Stop all: .\start_all.ps1 -Stop" -ForegroundColor Yellow
