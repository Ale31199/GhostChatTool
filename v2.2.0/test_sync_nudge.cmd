@echo off
setlocal
cd /d "%~dp0"
echo.
echo GhostChat Sync Fix v2.2.0 - safe sync nudge test
echo ===================================================
echo Keep the ChatGPT window in the foreground before continuing.
echo This test sends a normal Windows app activation only.
echo It does NOT type, send messages, or touch account credentials.
echo.
pause
where py >nul 2>&1
if %errorlevel%==0 (
  py "%~dp0test_sync_nudge.py"
) else (
  python "%~dp0test_sync_nudge.py"
)
echo.
pause
