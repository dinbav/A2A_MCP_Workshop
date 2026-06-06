# ============================================================
#  start_all.ps1  -  A2A MCP Workshop - Start All Servers
# ============================================================
# Starts (each in its own PowerShell window):
#   1. MCP FastMCP Server          -> port 8003
#   2. Packing List Agent          -> port 8081
#   3. Weather & Activity Agent    -> port 8082
#   4. Orchestrator Agent          -> port 8080
#
# Optional (with -UI flag):
#   5. Streamlit - MCP Playground  -> port 8504
#
# Usage:
#   .\start_all.ps1           # agents + MCP only
#   .\start_all.ps1 -UI       # agents + MCP + all Streamlit UIs
#   .\start_all.ps1 -Stop     # kill all processes on workshop ports
# ============================================================

param(
    [switch]$UI,
    [switch]$Stop
)

$WorkshopRoot = $PSScriptRoot

# helper: kill processes listening on a given port
function Stop-Port {
    param([int]$Port)
    $pids = netstat -ano | Select-String ":$Port\s" |
            ForEach-Object { ($_ -split '\s+')[-1] } |
            Sort-Object -Unique
    foreach ($p in $pids) {
        if ($p -match '^\d+$' -and $p -ne '0') {
            try { Stop-Process -Id $p -Force -ErrorAction SilentlyContinue } catch {}
        }
    }
}

# -Stop mode
if ($Stop) {
    Write-Host ""
    Write-Host "  Stopping all workshop servers..." -ForegroundColor Yellow
    8003, 8080, 8081, 8082, 8083, 8504 | ForEach-Object {
        Stop-Port $_
        Write-Host "  Cleared port $_" -ForegroundColor DarkGray
    }
    Write-Host ""
    Write-Host "  All ports cleared." -ForegroundColor Green
    Write-Host ""
    exit
}

# helper: open a new PowerShell window
function Start-Server {
    param(
        [string]$Title,
        [string]$Command,
        [string]$WorkDir
    )
    $escapedCmd = $Command -replace '"', '\"'
    $args = "-NoExit -Command `"" +
            "`$host.UI.RawUI.WindowTitle = '$Title'; " +
            "Set-Location '$WorkDir'; " +
            "$escapedCmd`""

    Start-Process powershell -ArgumentList $args -WindowStyle Normal
}

# banner
Write-Host ""
Write-Host "  =================================================" -ForegroundColor Cyan
Write-Host "   A2A MCP Workshop - Starting All Servers" -ForegroundColor Cyan
Write-Host "  =================================================" -ForegroundColor Cyan
Write-Host ""

# 1. MCP FastMCP Server (port 8003)
Write-Host "  [1/5] MCP FastMCP Server        -> http://127.0.0.1:8003/mcp" -ForegroundColor Green
Start-Server `
    -Title   "MCP Server :8003" `
    -Command "python fastmcp_server.py" `
    -WorkDir "$WorkshopRoot\mcp"

Start-Sleep -Seconds 2

# 2. Packing List Agent (port 8081)
Write-Host "  [2/5] Packing List Agent        -> http://localhost:8081" -ForegroundColor Green
Start-Server `
    -Title   "Packing List Agent :8081" `
    -Command "python -m a2a_agents.remote_agents.packing_list_agent" `
    -WorkDir "$WorkshopRoot"

Start-Sleep -Seconds 1

# 3. Weather & Activity Agent (port 8082)
Write-Host "  [3/5] Weather & Activity Agent  -> http://localhost:8082" -ForegroundColor Green
Start-Server `
    -Title   "Weather Activity Agent :8082" `
    -Command "python -m a2a_agents.remote_agents.weather_activity_agent" `
    -WorkDir "$WorkshopRoot"

Start-Sleep -Seconds 1

# 4. Local Tips Agent (port 8083)
Write-Host "  [4/5] Local Tips Agent          -> http://localhost:8083" -ForegroundColor Green
Start-Server `
    -Title   "Local Tips Agent :8083" `
    -Command "python -m a2a_agents.remote_agents.local_tips_agent" `
    -WorkDir "$WorkshopRoot"

Start-Sleep -Seconds 1

# 5. Orchestrator Agent (port 8080)
Write-Host "  [5/5] Orchestrator Agent        -> http://localhost:8080" -ForegroundColor Green
Start-Server `
    -Title   "Orchestrator Agent :8080" `
    -Command "python -m a2a_agents.orchestrator_agent" `
    -WorkDir "$WorkshopRoot"

# Optional Streamlit UIs
if ($UI) {
    Write-Host ""
    Write-Host "  -- Streamlit UIs --" -ForegroundColor Magenta

    Start-Sleep -Seconds 3

    Write-Host "  [UI] MCP Playground      -> http://localhost:8504" -ForegroundColor Magenta
    Start-Server `
        -Title   "UI - MCP Playground :8504" `
        -Command "streamlit run ui/mcp_playground.py --server.port 8504" `
        -WorkDir "$WorkshopRoot"
}

# summary
Write-Host ""
Write-Host "  =================================================" -ForegroundColor Cyan
Write-Host "   All servers started. Ports in use:" -ForegroundColor Cyan
Write-Host "  =================================================" -ForegroundColor Cyan
Write-Host "   MCP Server          http://127.0.0.1:8003/mcp" -ForegroundColor White
Write-Host "   Packing List Agent  http://localhost:8081" -ForegroundColor White
Write-Host "   Weather Agent       http://localhost:8082" -ForegroundColor White
Write-Host "   Local Tips Agent    http://localhost:8083" -ForegroundColor White
Write-Host "   Orchestrator        http://localhost:8080" -ForegroundColor White
if ($UI) {
    Write-Host "   MCP Playground      http://localhost:8504" -ForegroundColor Magenta
}
Write-Host ""
Write-Host "   To stop all:  .\start_all.ps1 -Stop" -ForegroundColor Yellow
Write-Host "  =================================================" -ForegroundColor Cyan
Write-Host ""
