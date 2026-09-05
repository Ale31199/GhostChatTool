@echo off
setlocal
set "INSTALLDIR=%USERPROFILE%\GhostChatTool"
set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\GhostChat Sync Fix.lnk"
set "STOPDIR=%USERPROFILE%\.codex\sqlite\ghostchat-patch"

echo Removing GhostChat Sync Fix v2.2 background watcher...
if not exist "%STOPDIR%" mkdir "%STOPDIR%"
>"%STOPDIR%\watcher.stop" echo stop
timeout /t 4 /nobreak >nul
if exist "%STARTUP%" del /Q "%STARTUP%"

for %%F in (ghostchat_patch.py ghostchat_watch.py ghostchat_nudge.py ghostchat_smart_restart.py test_sync_nudge.py test_sync_nudge.cmd test_search_toggle_nudge.cmd start_ghostchat_watcher_hidden.cmd run_watcher.vbs run_sync_fix_hidden.vbs sync_fix_now.cmd smart_restart_status.cmd start_watcher_now.cmd stop_watcher.cmd ghostchat_status.cmd hot_repair_now.cmd launch_chatgpt_with_patch.cmd) do (
  if exist "%INSTALLDIR%\%%F" del /Q "%INSTALLDIR%\%%F"
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "$desktop=[Environment]::GetFolderPath('Desktop'); $p=Join-Path $desktop 'ChatGPT - Sync & Fix.lnk'; if(Test-Path $p){Remove-Item -LiteralPath $p -Force}"

echo Done. ChatGPT itself was never modified.
echo Backups/logs under .codex were intentionally kept for safety.
pause
