@echo off
setlocal enabledelayedexpansion

cd /d "C:\Users\fizss\Documents\vs projects\FimozBot"

echo Adding changes...
git add -A
echo.

echo Checking status...
git status
echo.

echo Committing changes...
git commit -m "Initial project setup with example credentials" --no-verify

echo.
echo Pushing to repository...
git push -u origin main

echo.
echo Done!
pause
