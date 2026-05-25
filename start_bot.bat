@echo off
chcp 65001 >nul
setlocal

set "PYRUN=%~dp0run.py"
if exist "%PYRUN%" (
    if exist "%~systemroot%\py.exe" (
        py "%PYRUN%" %*
    ) else (
        python "%PYRUN%" %*
    )
) else (
    echo run.py not found in %~dp0
    pause
    exit /b 1
)