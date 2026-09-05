@echo off
setlocal
cd /d "%~dp0"
echo.
echo GhostChat Sync Patch - RESTORE LATEST BACKUP
echo ChatGPT must be fully closed.
echo.

where py >nul 2>&1
if %errorlevel%==0 (
    py "%~dp0ghostchat_patch.py" --restore-latest --no-launch
    echo.
    pause
    exit /b %errorlevel%
)

where python >nul 2>&1
if %errorlevel%==0 (
    python "%~dp0ghostchat_patch.py" --restore-latest --no-launch
    echo.
    pause
    exit /b %errorlevel%
)

echo Python was not found.
pause
exit /b 1
