@echo off
setlocal
set "PATCHDIR=%USERPROFILE%\.codex\sqlite\ghostchat-patch"
echo.
echo GhostChat Smart Restart - status
echo =================================
if exist "%PATCHDIR%\smart-restart-status.json" (
  type "%PATCHDIR%\smart-restart-status.json"
) else (
  echo No smart-restart status found yet.
)
echo.
echo Recent smart-restart log:
echo -------------------------
if exist "%PATCHDIR%\smart-restart.log" (
  powershell -NoProfile -Command "Get-Content -LiteralPath '%PATCHDIR%\smart-restart.log' -Tail 30"
) else (
  echo No smart-restart log found yet.
)
echo.
pause
