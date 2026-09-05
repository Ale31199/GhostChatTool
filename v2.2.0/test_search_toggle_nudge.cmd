@echo off
setlocal
cd /d "%~dp0"
echo.
echo GhostChat Sync Fix v2.2.0 - MANUAL stronger nudge test
echo ======================================================
echo This test sends Ctrl+K then Escape to ChatGPT ONLY if ChatGPT is foreground.
echo It does not type text or send a message, but the shortcut is experimental.
echo Use this only if test_sync_nudge.cmd did not trigger the refetch.
echo.
pause
where py >nul 2>&1
if %errorlevel%==0 (
  py "%~dp0test_sync_nudge.py" --search-toggle
) else (
  python "%~dp0test_sync_nudge.py" --search-toggle
)
echo.
pause
