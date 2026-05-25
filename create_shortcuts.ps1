# Create desktop shortcuts for FimozBot launchers
try {
    $WshShell = New-Object -ComObject WScript.Shell
    $desktop = [Environment]::GetFolderPath('Desktop')
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

    $batPath = Join-Path $scriptDir 'start_bot.bat'
    $ps1Path = Join-Path $scriptDir 'start_bot.ps1'

    if (Test-Path $batPath) {
        $lnkPath = Join-Path $desktop 'Start FimozBot (bat).lnk'
        $shortcut = $WshShell.CreateShortcut($lnkPath)
        $shortcut.TargetPath = $batPath
        $shortcut.WorkingDirectory = $scriptDir
        $shortcut.IconLocation = "$batPath,0"
        $shortcut.Save()
        Write-Host "Created: $lnkPath"
    } else { Write-Host "start_bot.bat not found in $scriptDir" -ForegroundColor Yellow }

    if (Test-Path $ps1Path) {
        $lnkPath2 = Join-Path $desktop 'Start FimozBot (PowerShell).lnk'
        $shortcut2 = $WshShell.CreateShortcut($lnkPath2)
        $shortcut2.TargetPath = 'powershell.exe'
        $shortcut2.Arguments = "-ExecutionPolicy Bypass -NoProfile -File `"$ps1Path`""
        $shortcut2.WorkingDirectory = $scriptDir
        $shortcut2.IconLocation = "$ps1Path,0"
        $shortcut2.Save()
        Write-Host "Created: $lnkPath2"
    } else { Write-Host "start_bot.ps1 not found in $scriptDir" -ForegroundColor Yellow }

    Write-Host "Shortcut creation finished."
} catch {
    Write-Error "Failed to create shortcuts: $_"
}
