@echo off
setlocal
cd /d "%~dp0"
echo.
echo GhostChat Sync Patch - SAFE DRY RUN
echo Nothing will be modified and ChatGPT will not be launched.
echo.

where py >nul 2>&1
if %errorlevel%==0 (
    py "%~dp0ghostchat_patch.py" --dry-run --allow-running --no-launch --audit
    echo.
    pause
    exit /b %errorlevel%
)

where python >nul 2>&1
if %errorlevel%==0 (
    python "%~dp0ghostchat_patch.py" --dry-run --allow-running --no-launch --audit
    echo.
    pause
    exit /b %errorlevel%
)

echo Python was not found.
pause
exit /b 1
