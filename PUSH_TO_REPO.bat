@echo off
REM Script to push changes to FimozBot repository
REM This script adds changes, commits with proper message, and pushes to remote

setlocal enabledelayedexpansion
cls

echo ========================================
echo FimozBot Repository Push Script
echo ========================================
echo.

REM Change to project directory
cd /d "C:\Users\fizss\Documents\vs projects\FimozBot" || (
    echo ERROR: Could not navigate to project directory
    pause
    exit /b 1
)

echo Current Directory: !CD!
echo.

REM Configure git user if needed
git config user.email "bot@example.com" >nul 2>&1
git config user.name "Copilot Bot" >nul 2>&1

echo Step 1: Adding all changes...
git add -A
echo Status after add:
git status --short
echo.

echo Step 2: Creating commit...
git commit -m "Initial project setup with example credentials

- Replaced sensitive tokens and passwords with examples
- Protected Discord token, Lavalink password, and Spotify credentials
- Ready for public repository

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"

if !errorlevel! neq 0 (
    echo No changes to commit or commit failed
)
echo.

echo Step 3: Checking git status...
git status
echo.

echo Step 4: Pushing to repository...
git push origin main

if !errorlevel! equ 0 (
    echo.
    echo ✓ Push completed successfully!
) else (
    echo.
    echo ✗ Push failed - check error messages above
)

echo.
echo ========================================
pause
