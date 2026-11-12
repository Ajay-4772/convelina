<#
.SYNOPSIS
    CONVELINA Local Reproducible Security Scanner Suite
    Executes Bandit, Ruff, pip-audit, npm audit, Trivy, Gitleaks, and Semgrep (when installed).
#>

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Py = Join-Path $Root "backend\.venv\Scripts\python.exe"
$Trivy = Get-ChildItem "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" -Recurse -Filter "trivy.exe" -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName
$Gitleaks = Get-ChildItem "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" -Recurse -Filter "gitleaks.exe" -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName

Write-Host "=== [1/6] Ruff Security & Undefined-Name Checks ===" -ForegroundColor Cyan
& $Py -m ruff check backend/app --select F821,S105,S108,S110,S112,S310,S324

Write-Host "`n=== [2/6] Bandit Python SAST ===" -ForegroundColor Cyan
& $Py -m bandit -r backend/app -ll -q

Write-Host "`n=== [3/6] pip-audit (Installed Environment) ===" -ForegroundColor Cyan
& $Py -m pip_audit --progress-spinner off

Write-Host "`n=== [4/6] npm audit (Frontend) ===" -ForegroundColor Cyan
npm --prefix frontend audit --audit-level=high

if ($Trivy) {
    Write-Host "`n=== [5/6] Trivy (Manifests & Dockerfiles) ===" -ForegroundColor Cyan
    foreach ($Target in @("backend/requirements.txt", "frontend/package-lock.json", "backend/Dockerfile", "frontend/Dockerfile")) {
        & $Trivy fs --scanners vuln,misconfig --misconfig-scanners dockerfile --severity MEDIUM,HIGH,CRITICAL --quiet $Target
    }
} else {
    Write-Host "`n=== [5/6] Trivy not installed locally ===" -ForegroundColor Yellow
}

if ($Gitleaks) {
    Write-Host "`n=== [6/6] Gitleaks Secret Detection ===" -ForegroundColor Cyan
    & $Gitleaks detect --source . --no-banner --redact
} else {
    Write-Host "`n=== [6/6] Gitleaks not installed locally ===" -ForegroundColor Yellow
}

