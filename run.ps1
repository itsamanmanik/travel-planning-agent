# run.ps1  --  one-command start for Windows (PowerShell)
# Usage:  right-click > Run with PowerShell,  OR  in a terminal:  ./run.ps1

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here

# Create the virtual environment on first run.
if (-not (Test-Path ".\.venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Cyan
    python -m venv .venv
    .\.venv\Scripts\python.exe -m pip install --upgrade pip
    .\.venv\Scripts\python.exe -m pip install -r requirements.txt
}

# Warn if the key is missing (the app still starts).
if (-not (Test-Path ".\.env")) {
    Write-Host "No .env found. Copy .env.example to .env and add your free GROQ_API_KEY." -ForegroundColor Yellow
}

Write-Host "Starting the Travel Agent at http://localhost:8000 ..." -ForegroundColor Green
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
