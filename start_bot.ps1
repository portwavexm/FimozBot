<#
PowerShell launcher for the Discord Music Bot
Features:
- optional creation/activation of virtualenv (.venv)
- logging to logs/start_bot_YYYYMMDD_HHMMSS.log
- options: --NoLavalink, --LavalinkOnly, --PlaylistStore
- optional auto-restart on non-zero exit
Usage (PowerShell):
  .\start_bot.ps1 -AutoRestart -PlaylistStore "config/playlists.json"
Run with execution policy bypass if needed:
  powershell -ExecutionPolicy Bypass -File .\start_bot.ps1
#>

param(
    [switch]$NoLavalink,
    [switch]$LavalinkOnly,
    [string]$PlaylistStore = $null,
    [switch]$AutoRestart,
    [switch]$CreateVenv
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Push-Location $scriptDir

# Ensure logs dir
$logsDir = Join-Path $scriptDir 'logs'
if (-not (Test-Path $logsDir)) { New-Item -ItemType Directory -Path $logsDir | Out-Null }

$timestamp = (Get-Date).ToString('yyyyMMdd_HHmmss')
$logFile = Join-Path $logsDir "start_bot_$timestamp.log"

# Start transcript for logging (suppresses if not supported)
try {
    Start-Transcript -Path $logFile -Force | Out-Null
} catch {
    Write-Host "Warning: Start-Transcript not available. Logging to $logFile may be incomplete." -ForegroundColor Yellow
}

function Write-Log { 
    param($m)
    Write-Host $m
    try {
        "$([DateTime]::Now) - $m" | Out-File -FilePath $logFile -Append -ErrorAction Stop
    } catch {
        Write-Host "Warning: failed to write to log file ($logFile)." -ForegroundColor Yellow
    }
}

# Create and/or activate virtualenv
$venvPath = Join-Path $scriptDir '.venv'
$activateScript = Join-Path $venvPath 'Scripts\Activate.ps1'
if ($CreateVenv) {
    if (-not (Test-Path $venvPath)) {
        Write-Log "Creating virtual environment at $venvPath..."
        & python -m venv $venvPath
        Write-Log "Virtualenv created."
        # try install requirements
        $req = Join-Path $scriptDir 'requirements.txt'
        if (Test-Path $req) {
            Write-Log "Installing requirements from requirements.txt..."
            & "$venvPath\Scripts\python.exe" -m pip install -r $req
            Write-Log "Requirements installed."
        }
    } else {
        Write-Log "Virtualenv already exists at $venvPath."
    }
}

if (Test-Path $activateScript) {
    Write-Log "Activating virtualenv..."
    . $activateScript
} else {
    Write-Log "No virtualenv activation script found; running system Python."
}

# Build run.py args
$runArgs = @()
if ($NoLavalink) { $runArgs += '--no-lavalink' }
if ($LavalinkOnly) { $runArgs += '--lavalink-only' }
if ($PlaylistStore) { $runArgs += '--playlist-store'; $runArgs += $PlaylistStore }

# Main loop (auto-restart if requested)
do {
    Write-Log "Launching run.py with args: $($runArgs -join ' ')"
    & python .\run.py @runArgs
    $exit = $LASTEXITCODE
    Write-Log "run.py exited with code $exit"
        if (-not $AutoRestart) { break }
        Write-Log "AutoRestart enabled - restarting in 3 seconds..."
    Start-Sleep -Seconds 3
} while ($true)

# Cleanup
try { Stop-Transcript } catch {}
Pop-Location

Write-Log "Launcher finished."

exit $exit
