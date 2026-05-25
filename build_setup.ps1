<#
Build Inno Setup Installer
Requires Inno Setup to be installed: https://jrsoftware.org/isdl.php

Usage:
  powershell -ExecutionPolicy Bypass -File build_setup.ps1
#>

param(
    [switch]$SkipValidation
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Push-Location $scriptDir

function Write-Info { Write-Host "[INFO] $_" -ForegroundColor Cyan }
function Write-Success { Write-Host "[OK]   $_" -ForegroundColor Green }
function Write-Error { Write-Host "[ERROR] $_" -ForegroundColor Red }
function Write-Header { Write-Host ""; Write-Host "== $_ ==" -ForegroundColor Magenta }

Write-Header "FimozBot Inno Setup Builder"

# Check if Inno Setup is installed
Write-Info "Checking for Inno Setup..."

$innoSetupPaths = @(
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe",
    "C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
    "C:\Program Files\Inno Setup 5\ISCC.exe"
)

$isccPath = $null
foreach ($path in $innoSetupPaths) {
    if (Test-Path $path) {
        $isccPath = $path
        Write-Success "Found Inno Setup at: $isccPath"
        break
    }
}

if (-not $isccPath) {
    Write-Error "Inno Setup not found!"
    Write-Host ""
    Write-Host "Please install Inno Setup from: https://jrsoftware.org/isdl.php" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "After installation, run this script again."
    Pop-Location
    exit 1
}

# Create dist directory
Write-Info "Preparing dist directory..."
if (-not (Test-Path "dist")) {
    New-Item -ItemType Directory -Path "dist" | Out-Null
    Write-Success "Created dist directory"
} else {
    Write-Info "dist directory already exists"
}

# Build installer
Write-Header "Building Installer"

Write-Info "Running Inno Setup compiler..."
& $isccPath "installer.iss"

$exitCode = $LASTEXITCODE
if ($exitCode -eq 0) {
    Write-Success "Installer built successfully!"
    Write-Host ""
    Write-Host "Output file:" -ForegroundColor Green
    Get-Item "dist\FimozBot-Setup.exe" | ForEach-Object {
        Write-Host "  $($_.FullName)"
        Write-Host "  Size: $([math]::Round($_.Length / 1MB, 2)) MB"
    }
} else {
    Write-Error "Inno Setup compiler failed with exit code: $exitCode"
    Pop-Location
    exit $exitCode
}

Pop-Location
Write-Host ""
Write-Success "Done!"
