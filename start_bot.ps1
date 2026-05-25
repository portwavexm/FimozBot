# PowerShell launcher for the Discord Music Bot
# Features:
# - optional creation/activation of virtualenv (.venv)
# - logging to logs/start_bot_YYYYMMDD_HHMMSS.log
# - options: --NoLavalink, --LavalinkOnly, --PlaylistStore
# - optional auto-restart on non-zero exit
# - First run: option to add to Windows startup

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

$logsDir = Join-Path $scriptDir 'logs'
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir | Out-Null
}

$timestamp = (Get-Date).ToString('yyyyMMdd_HHmmss')
$logFile = Join-Path $logsDir ('start_bot_' + $timestamp + '.log')

try {
    Start-Transcript -Path $logFile -Force | Out-Null
} catch {
    Write-Host 'Warning: Start-Transcript not available. Logging may be incomplete.' -ForegroundColor Yellow
}

function Write-Log {
    param($m)

    Write-Host $m
    try {
        ($([DateTime]::Now).ToString('yyyy-MM-dd HH:mm:ss') + ' - ' + $m) | Out-File -FilePath $logFile -Append -ErrorAction Stop
    } catch {
        Write-Host ('Warning: failed to write to log file (' + $logFile + ').') -ForegroundColor Yellow
    }
}

$firstRunMarker = Join-Path $scriptDir '.first_run_done'

if (-not (Test-Path $firstRunMarker)) {
    Write-Log '===== FIRST RUN SETUP ====='
    Write-Host ''
    Write-Host 'FimozBot - First Run Setup' -ForegroundColor Cyan
    Write-Host ('=' * 40)
    Write-Host ''

    $response = Read-Host 'Would you like to add FimozBot to Windows startup? (Y/N)'

    if ($response -match '^[Yy]$') {
        try {
            $startupFolder = [System.IO.Path]::Combine([System.Environment]::GetFolderPath('Startup'))
            $shortcutPath = Join-Path $startupFolder 'FimozBot.lnk'

            $shell = New-Object -ComObject WScript.Shell
            $shortcut = $shell.CreateShortcut($shortcutPath)
            $shortcut.TargetPath = 'powershell.exe'
            $shortcut.Arguments = '-ExecutionPolicy Bypass -NoProfile -WindowStyle Hidden -File "' + $PSCommandPath + '"'
            $shortcut.WorkingDirectory = $scriptDir
            $shortcut.IconLocation = 'powershell.exe,0'
            $shortcut.Description = 'FimozBot - Discord Music Bot'
            $shortcut.Save()

            Write-Log ('Autostart shortcut created at: ' + $shortcutPath)
            Write-Host '✓ Autostart enabled! Bot will start with Windows.' -ForegroundColor Green
        } catch {
            Write-Log ('ERROR: Failed to create autostart shortcut: ' + $_)
            Write-Host ('✗ Failed to enable autostart: ' + $_) -ForegroundColor Red
        }
    } else {
        Write-Log 'User declined autostart setup.'
        Write-Host '✓ Autostart skipped.' -ForegroundColor Yellow
    }

    try {
        New-Item -ItemType File -Path $firstRunMarker -Force | Out-Null
        Write-Log 'First run setup completed.'
    } catch {
        Write-Log ('Warning: Could not create first run marker: ' + $_)
    }

    Write-Host ''
    Write-Host 'Setup complete. Starting bot...' -ForegroundColor Green
    Write-Host ''
    Start-Sleep -Seconds 2
}

$venvPath = Join-Path $scriptDir '.venv'
$activateScript = Join-Path $venvPath 'Scripts\Activate.ps1'

if ($CreateVenv) {
    if (-not (Test-Path $venvPath)) {
        Write-Log ('Creating virtual environment at ' + $venvPath + '...')
        & python -m venv $venvPath
        Write-Log 'Virtualenv created.'

        $req = Join-Path $scriptDir 'requirements.txt'
        if (Test-Path $req) {
            Write-Log 'Installing requirements from requirements.txt...'
            & ($venvPath + '\Scripts\python.exe') -m pip install -r $req
            Write-Log 'Requirements installed.'
        }
    } else {
        Write-Log ('Virtualenv already exists at ' + $venvPath + '.')
    }
}

if (Test-Path $activateScript) {
    Write-Log 'Activating virtualenv...'
    . $activateScript
} else {
    Write-Log 'No virtualenv activation script found; running system Python.'
}

$runArgs = @()
if ($NoLavalink) { $runArgs += '--no-lavalink' }
if ($LavalinkOnly) { $runArgs += '--lavalink-only' }
if ($PlaylistStore) { $runArgs += '--playlist-store'; $runArgs += $PlaylistStore }

$exit = 0

do {
    Write-Log ('Launching run.py with args: ' + ($runArgs -join ' '))
    & python .\run.py @runArgs
    $exit = $LASTEXITCODE
    Write-Log ('run.py exited with code ' + $exit)

    if (-not $AutoRestart) {
        break
    }

    Write-Log 'AutoRestart enabled - restarting in 3 seconds...'
    Start-Sleep -Seconds 3
} while ($true)

try {
    Stop-Transcript
} catch {}

Pop-Location
Write-Log 'Launcher finished.'

exit $exit
