@echo off
REM FimozBot Installer Wrapper
REM Simplified launcher for PowerShell install script

setlocal enabledelayedexpansion

echo.
echo ========================================
echo FimozBot Installation Wizard
echo ========================================
echo.
echo This will install FimozBot on your computer.
echo Press any key to continue...
pause >nul

REM Run PowerShell script
powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0install.ps1"

echo.
if %errorlevel% equ 0 (
    echo Installation completed successfully!
) else (
    echo Installation failed. Check the error messages above.
)

echo.
pause
