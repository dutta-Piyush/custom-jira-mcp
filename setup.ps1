param(
    [string]$Url,
    [string]$Pat
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== Jira MCP Server Setup ===" -ForegroundColor Cyan
Write-Host ""

# ── Step 1: Check Python ──────────────────────────────────────────────────────
Write-Host "[1/7] Checking Python..." -ForegroundColor Yellow
try {
    $pyVersion = python --version 2>&1
    Write-Host "      Found: $pyVersion" -ForegroundColor Green
} catch {
    Write-Host "      ERROR: Python not found. Install Python 3.11+ and try again." -ForegroundColor Red
    exit 1
}

# ── Step 2: Create virtual environment ────────────────────────────────────────
Write-Host "[2/7] Creating virtual environment..." -ForegroundColor Yellow
$venvPath = Join-Path $PSScriptRoot ".venv"
if (-not (Test-Path $venvPath)) {
    python -m venv $venvPath
    Write-Host "      Created .venv" -ForegroundColor Green
} else {
    Write-Host "      .venv already exists, skipping" -ForegroundColor Gray
}

# ── Step 3: Install dependencies ─────────────────────────────────────────────
Write-Host "[3/7] Installing dependencies..." -ForegroundColor Yellow
$pip = Join-Path $venvPath "Scripts\pip.exe"
& $pip install -r (Join-Path $PSScriptRoot "requirements.txt") --quiet
Write-Host "      Dependencies installed" -ForegroundColor Green

# ── Step 4: Collect configuration ────────────────────────────────────────────
Write-Host "[4/7] Collecting configuration..." -ForegroundColor Yellow

if (-not $Url) {
    $Url = Read-Host "      Enter your Jira base URL (e.g. https://your-jira.company.com)"
}
if (-not $Url) {
    Write-Host "      ERROR: JIRA_URL is required." -ForegroundColor Red
    exit 1
}

if (-not $Pat) {
    $securePat = Read-Host "      Enter your Jira Personal Access Token (PAT)" -AsSecureString
    $Pat = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePat)
    )
}
if (-not $Pat) {
    Write-Host "      ERROR: JIRA_PAT is required." -ForegroundColor Red
    exit 1
}

# ── Step 5: Validate connectivity ────────────────────────────────────────────
Write-Host "[5/7] Validating connection to Jira..." -ForegroundColor Yellow
$python = Join-Path $venvPath "Scripts\python.exe"
$testScript = @"
import httpx, sys
url = "$Url".rstrip("/") + "/rest/api/2/myself"
try:
    r = httpx.get(url, headers={"Authorization": "Bearer $Pat"}, verify=False, timeout=10)
    if r.status_code == 200:
        user = r.json()
        print(f"Connected as: {user.get('displayName','?')} ({user.get('name','?')})")
    else:
        print(f"HTTP {r.status_code}: check your URL and PAT", file=sys.stderr)
        sys.exit(1)
except Exception as e:
    print(f"Connection failed: {e}", file=sys.stderr)
    sys.exit(1)
"@
$result = & $python -c $testScript 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "      WARNING: Could not validate connection: $result" -ForegroundColor Yellow
    Write-Host "      Continuing setup anyway..." -ForegroundColor Yellow
} else {
    Write-Host "      $result" -ForegroundColor Green
}

# ── Step 6: Verify tools are registered ──────────────────────────────────────
Write-Host "[6/7] Verifying tools..." -ForegroundColor Yellow
$toolCount = 0
$toolFiles = Get-ChildItem -Path (Join-Path $PSScriptRoot "jira_mcp") -Recurse -Filter "*.py" | Select-Object -ExpandProperty FullName
foreach ($file in $toolFiles) {
    $content = Get-Content $file -Raw
    $matches = [regex]::Matches($content, '@mcp\.tool\(\)')
    $toolCount += $matches.Count
}
Write-Host "      Found $toolCount @mcp.tool() registrations in jira_mcp/" -ForegroundColor Green

# ── Step 7: Write mcp.json ───────────────────────────────────────────────────
Write-Host "[7/7] Writing .vscode/mcp.json..." -ForegroundColor Yellow
$vscodeDir = Join-Path $PSScriptRoot ".vscode"
if (-not (Test-Path $vscodeDir)) {
    New-Item -ItemType Directory -Path $vscodeDir | Out-Null
}

$pythonExe = (Join-Path $venvPath "Scripts\python.exe") -replace "\\", "\\\\"
$serverPath = (Join-Path $PSScriptRoot "server.py") -replace "\\", "\\\\"

$mcpJson = @"
{
  "servers": {
    "jira-mcp": {
      "type": "stdio",
      "command": "$pythonExe",
      "args": ["$serverPath"],
      "env": {
        "JIRA_URL": "$Url",
        "JIRA_PAT": "$Pat"
      }
    }
  }
}
"@

$mcpJson | Set-Content (Join-Path $vscodeDir "mcp.json") -Encoding UTF8
Write-Host "      Written to .vscode/mcp.json" -ForegroundColor Green

Write-Host ""
Write-Host "=== Setup complete! ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Reload VS Code or restart GitHub Copilot to pick up the new MCP server." -ForegroundColor White
Write-Host "The server exposes $toolCount Jira tools to GitHub Copilot." -ForegroundColor White
Write-Host ""
