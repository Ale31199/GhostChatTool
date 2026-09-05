@echo off
setlocal
set "PATCHDIR=%USERPROFILE%\.codex\sqlite\ghostchat-patch"
echo.
echo GhostChat Sync Fix - status
echo ===========================
if exist "%PATCHDIR%\watcher-status.json" (
  type "%PATCHDIR%\watcher-status.json"
) else (
  echo No watcher status found yet.
)
echo.
echo Recent watcher log:
echo -------------------
if exist "%PATCHDIR%\watcher.log" (
  powershell -NoProfile -Command "Get-Content -LiteralPath '%PATCHDIR%\watcher.log' -Tail 20"
) else (
  echo No watcher log found yet.
)
echo.
pause
