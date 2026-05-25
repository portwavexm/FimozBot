<#
FimozBot Installation Script
Автоматическая установка бота на новый ПК

Использование:
  powershell -ExecutionPolicy Bypass -File install.ps1

Требования:
  - Windows 7+
  - PowerShell 5.0+
  - Интернет соединение
#>

param(
    [switch]$Silent,
    [switch]$SkipPython,
    [switch]$SkipJava,
    [string]$InstallPath = $null
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Colors
$colors = @{
    Success = 'Green'
    Error   = 'Red'
    Warning = 'Yellow'
    Info    = 'Cyan'
    Header  = 'Magenta'
}

function Write-Header {
    param([string]$text)
    Write-Host ""
    Write-Host ("=" * 60) -ForegroundColor $colors.Header
    Write-Host $text -ForegroundColor $colors.Header
    Write-Host ("=" * 60) -ForegroundColor $colors.Header
    Write-Host ""
}

function Write-Success {
    param([string]$text)
    Write-Host "[OK]     $text" -ForegroundColor $colors.Success
}

function Write-Error {
    param([string]$text)
    Write-Host "[ERROR]  $text" -ForegroundColor $colors.Error
}

function Write-Warning {
    param([string]$text)
    Write-Host "[WARN]   $text" -ForegroundColor $colors.Warning
}

function Write-Info {
    param([string]$text)
    Write-Host "[INFO]   $text" -ForegroundColor $colors.Info
}

function Check-Command {
    param([string]$cmd)
    $null = (Get-Command $cmd -ErrorAction SilentlyContinue)
    return $?
}

function Check-Python {
    Write-Info "Checking Python installation..."
    
    if (Check-Command python) {
        $version = python --version 2>&1
        Write-Success "Found: $version"
        return $true
    }
    
    Write-Warning "Python not found"
    return $false
}

function Check-Java {
    Write-Info "Checking Java installation..."
    
    if (Check-Command java) {
        $version = java -version 2>&1 | Select-Object -First 1
        Write-Success "Found: $version"
        return $true
    }
    
    Write-Warning "Java not found"
    return $false
}

function Install-Python {
    Write-Header "Installing Python 3.11"
    
    $pythonUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
    $pythonInstaller = "$env:TEMP\python-installer.exe"
    
    try {
        Write-Info "Downloading Python 3.11..."
        (New-Object Net.WebClient).DownloadFile($pythonUrl, $pythonInstaller)
        Write-Success "Downloaded"
        
        Write-Info "Running Python installer..."
        Start-Process $pythonInstaller -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait -NoNewWindow
        Write-Success "Python installed"
        
        Remove-Item $pythonInstaller -Force -ErrorAction SilentlyContinue
        
        # Refresh PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        
        return $true
    } catch {
        Write-Error "Failed to install Python: $_"
        return $false
    }
}

function Install-Java {
    Write-Header "Installing Java Runtime Environment"
    
    Write-Info "Java installation requires manual download from:"
    Write-Host "https://www.java.com/en/download/" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Press Enter when Java is installed, or type 'skip' to continue without Java"
    
    $response = Read-Host
    if ($response -eq 'skip') {
        Write-Warning "Java skipped - Lavalink will not work"
        return $false
    }
    
    if (Check-Java) {
        Write-Success "Java verification successful"
        return $true
    } else {
        Write-Error "Java installation not detected"
        return $false
    }
}

function Setup-BotDirectory {
    param([string]$path)
    
    if (-not $InstallPath) {
        Write-Header "Installation Path"
        Write-Info "Default path: C:\FimozBot"
        $path = Read-Host "Enter installation path (press Enter for default)"
        if (-not $path) {
            $path = "C:\FimozBot"
        }
    }
    
    if (Test-Path $path) {
        Write-Warning "Directory already exists: $path"
        $response = Read-Host "Continue anyway? (y/n)"
        if ($response -ne 'y') {
            return $null
        }
    } else {
        Write-Info "Creating directory: $path"
        New-Item -ItemType Directory -Path $path -Force | Out-Null
        Write-Success "Directory created"
    }
    
    return $path
}

function Clone-Repository {
    param([string]$path)
    
    Write-Header "Cloning FimozBot Repository"
    
    try {
        Write-Info "Cloning from GitHub..."
        Push-Location $path
        & git clone https://github.com/portwavexm/FimozBot.git $path
        Write-Success "Repository cloned"
        return $true
    } catch {
        Write-Error "Failed to clone repository: $_"
        return $false
    } finally {
        Pop-Location
    }
}

function Setup-VirtualEnv {
    param([string]$path)
    
    Write-Header "Setting up Python Virtual Environment"
    
    try {
        Push-Location $path
        
        Write-Info "Creating virtual environment..."
        & python -m venv .venv
        Write-Success "Virtual environment created"
        
        Write-Info "Activating virtual environment..."
        & .\.venv\Scripts\Activate.ps1
        
        Write-Info "Installing dependencies..."
        & python -m pip install --upgrade pip
        & pip install -r requirements.txt
        Write-Success "Dependencies installed"
        
        return $true
    } catch {
        Write-Error "Failed to setup virtual environment: $_"
        return $false
    } finally {
        Pop-Location
    }
}

function Setup-Configuration {
    param([string]$path)
    
    Write-Header "Configuring FimozBot"
    
    $envFile = Join-Path $path ".env"
    
    Write-Info "Edit the following configuration file:"
    Write-Host $envFile -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Required settings:"
    Write-Host "  1. DISCORD_TOKEN - Get from https://discord.com/developers/applications"
    Write-Host "  2. SPOTIFY_CLIENT_ID - Get from https://developer.spotify.com/dashboard"
    Write-Host "  3. SPOTIFY_CLIENT_SECRET - Get from https://developer.spotify.com/dashboard"
    Write-Host "  4. LAVALINK_PASSWORD - Keep as is or change"
    Write-Host ""
    
    $response = Read-Host "Open .env file now? (y/n)"
    if ($response -eq 'y') {
        Start-Process notepad $envFile
        Read-Host "Press Enter when done editing"
    }
    
    Write-Success "Configuration setup complete"
}

function Create-Shortcuts {
    param([string]$path)
    
    Write-Header "Creating Shortcuts"
    
    try {
        $startMenuPath = [System.IO.Path]::Combine([System.Environment]::GetFolderPath('StartMenu'))
        $desktopPath = [System.Environment]::GetFolderPath('Desktop')
        
        # PowerShell script path
        $startScript = Join-Path $path "start_bot.ps1"
        
        # Create WScript.Shell COM object
        $shell = New-Object -ComObject WScript.Shell
        
        # Desktop shortcut
        $desktopShortcut = Join-Path $desktopPath "FimozBot.lnk"
        $shortcut = $shell.CreateShortcut($desktopShortcut)
        $shortcut.TargetPath = "powershell.exe"
        $shortcut.Arguments = "-ExecutionPolicy Bypass -NoProfile -File `"$startScript`""
        $shortcut.WorkingDirectory = $path
        $shortcut.IconLocation = "powershell.exe,0"
        $shortcut.Description = "FimozBot - Discord Music Bot"
        $shortcut.Save()
        
        Write-Success "Desktop shortcut created"
        
        # Start Menu shortcut
        $startMenuShortcut = Join-Path $startMenuPath "FimozBot.lnk"
        $shortcut = $shell.CreateShortcut($startMenuShortcut)
        $shortcut.TargetPath = "powershell.exe"
        $shortcut.Arguments = "-ExecutionPolicy Bypass -NoProfile -File `"$startScript`""
        $shortcut.WorkingDirectory = $path
        $shortcut.IconLocation = "powershell.exe,0"
        $shortcut.Description = "FimozBot - Discord Music Bot"
        $shortcut.Save()
        
        Write-Success "Start Menu shortcut created"
        
        return $true
    } catch {
        Write-Error "Failed to create shortcuts: $_"
        return $false
    }
}

# Main installation flow
function Main {
    Clear-Host
    Write-Header "FimozBot Installation Wizard"
    
    Write-Info "This script will install FimozBot on your computer"
    Write-Info "Installation time: ~5-10 minutes (depending on internet speed)"
    Write-Host ""
    
    # Check requirements
    Write-Header "Checking Requirements"
    
    $pythonOk = Check-Python
    if (-not $pythonOk -and -not $SkipPython) {
        if (-not $Silent) {
            $response = Read-Host "Install Python? (y/n)"
            if ($response -eq 'y') {
                if (-not (Install-Python)) {
                    Write-Error "Installation aborted"
                    exit 1
                }
            }
        }
    }
    
    $javaOk = Check-Java
    if (-not $javaOk -and -not $SkipJava) {
        if (-not $Silent) {
            Install-Java
        }
    }
    
    # Git check
    Write-Info "Checking Git..."
    if (-not (Check-Command git)) {
        Write-Error "Git not found. Please install Git from https://git-scm.com"
        exit 1
    }
    Write-Success "Git found"
    
    Write-Host ""
    
    # Setup
    $installPath = Setup-BotDirectory $InstallPath
    if (-not $installPath) {
        Write-Error "Installation cancelled"
        exit 1
    }
    
    if (-not (Clone-Repository $installPath)) {
        Write-Error "Failed to clone repository"
        exit 1
    }
    
    if (-not (Setup-VirtualEnv $installPath)) {
        Write-Error "Failed to setup virtual environment"
        exit 1
    }
    
    Setup-Configuration $installPath
    
    if (-not $Silent) {
        $response = Read-Host "Create desktop and Start Menu shortcuts? (y/n)"
        if ($response -eq 'y') {
            Create-Shortcuts $installPath
        }
    }
    
    # Done
    Write-Header "Installation Complete!"
    
    Write-Host "FimozBot is now installed at: $installPath" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host "  1. Edit .env file with your Discord token and Spotify credentials"
    Write-Host "  2. Start Lavalink server (if Java installed): cd $installPath\lavalink-server && java -jar Lavalink.jar"
    Write-Host "  3. Run the bot: powershell -ExecutionPolicy Bypass -File $installPath\start_bot.ps1"
    Write-Host ""
    Write-Host "More info: $installPath\README.md" -ForegroundColor Cyan
    Write-Host ""
    
    Read-Host "Press Enter to exit"
}

# Run main
Main
