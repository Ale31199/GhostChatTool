@echo off
setlocal
cd /d "%~dp0"
echo.
echo GhostChat HOT REPAIR - one conservative pass
echo ChatGPT may remain open. Only exact conversation_deleted evidence is eligible.
echo.
where py >nul 2>&1
if %errorlevel%==0 (
    py "%~dp0ghostchat_patch.py" --allow-running --no-launch --audit
    echo.
    pause
    exit /b %errorlevel%
)
where python >nul 2>&1
if %errorlevel%==0 (
    python "%~dp0ghostchat_patch.py" --allow-running --no-launch --audit
    echo.
    pause
    exit /b %errorlevel%
)
echo Python was not found.
pause
exit /b 1
