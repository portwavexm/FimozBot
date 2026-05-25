<#
Build script: creates a single-file executable with PyInstaller and optionally
builds an Inno Setup installer if `ISCC.exe` is available.

Usage (developer machine):
  powershell -ExecutionPolicy Bypass -File .\build_installer.ps1 [-NoInno]
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

param(
    [switch]$NoInno
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Push-Location $scriptDir

function Write-Log { param($m) Write-Host $m }

Write-Log "Checking Python and PyInstaller..."
try {
    python -c "import PyInstaller" 2>$null
} catch {
    Write-Log "PyInstaller not found. Installing..."
    python -m pip install --upgrade pip
    python -m pip install pyinstaller
}

# Build options - adjust add-data if you need extra folders
$distName = 'run'
$specArgs = @(
    '--onefile',
    '--noconsole',
    "--name=$distName",
    "--add-data=config;config",
    "--add-data=cogs;cogs",
    "--add-data=utils;utils",
    "--add-data=tokens.txt;."
)

Write-Log "Running PyInstaller..."
& pyinstaller @specArgs run.py

if ($LASTEXITCODE -ne 0) {
    Write-Log "PyInstaller failed with exit code $LASTEXITCODE"
    Pop-Location
    exit $LASTEXITCODE
}

Write-Log "PyInstaller finished. Output: dist\$distName.exe"

if (-not $NoInno) {
    # Try to find Inno Setup compiler (ISCC.exe)
    $iscc = "C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe"
    if (Test-Path $iscc) {
        Write-Log "Found Inno Setup. Building installer..."
        & "$iscc" installer.iss
        Write-Log "Installer build finished."
    } else {
        Write-Log "Inno Setup (ISCC.exe) not found at $iscc. Skipping installer build."
    }
}

Pop-Location

Write-Log "Done."
