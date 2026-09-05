@echo off
setlocal EnableExtensions
set "INSTALLDIR=%USERPROFILE%\GhostChatTool"
set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"

echo.
echo GhostChat Sync Fix v2.2.0
echo Background watcher installer
echo.

where py >nul 2>&1
if not errorlevel 1 goto :python_ok
where python >nul 2>&1
if not errorlevel 1 goto :python_ok
echo Python was not found. Install Python or make sure py/python is available in PATH.
pause
exit /b 1

:python_ok

if not exist "%INSTALLDIR%" mkdir "%INSTALLDIR%"

for %%F in (ghostchat.py ghostchat.cmd ghostchat_patch.py ghostchat_watch.py ghostchat_nudge.py ghostchat_smart_restart.py test_sync_nudge.py test_sync_nudge.cmd test_search_toggle_nudge.cmd start_ghostchat_watcher_hidden.cmd run_watcher.vbs run_sync_fix_hidden.vbs sync_fix_now.cmd smart_restart_status.cmd start_watcher_now.cmd stop_watcher.cmd ghostchat_status.cmd hot_repair_now.cmd restore_latest_backup.cmd) do (
  copy /Y "%~dp0%%F" "%INSTALLDIR%\%%F" >nul
)

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ws=New-Object -ComObject WScript.Shell;" ^
  "$s=$ws.CreateShortcut((Join-Path '%STARTUP%' 'GhostChat Sync Fix.lnk'));" ^
  "$s.TargetPath=(Join-Path $env:WINDIR 'System32\wscript.exe');" ^
  "$s.Arguments=[char]34+'%INSTALLDIR%\run_watcher.vbs'+[char]34;" ^
  "$s.WorkingDirectory='%INSTALLDIR%';" ^
  "$s.Description='GhostChat Sync Fix background watcher';" ^
  "$s.Save();" ^
  "$desktop=[Environment]::GetFolderPath('Desktop');" ^
  "$old=Join-Path $desktop 'ChatGPT (Ghost Fix).lnk'; if(Test-Path $old){Remove-Item -LiteralPath $old -Force};" ^
  "$fix=$ws.CreateShortcut((Join-Path $desktop 'ChatGPT - Sync & Fix.lnk'));" ^
  "$fix.TargetPath=(Join-Path $env:WINDIR 'System32\wscript.exe');" ^
  "$fix.Arguments=[char]34+'%INSTALLDIR%\run_sync_fix_hidden.vbs'+[char]34;" ^
  "$fix.WorkingDirectory='%INSTALLDIR%';" ^
  "$fix.Description='Restart ChatGPT, force a fresh sync, then run GhostChat conservative repair';" ^
  "$fix.Save()"

rem Stop any old watcher, then start the newly installed one hidden.
if not exist "%USERPROFILE%\.codex\sqlite\ghostchat-patch" mkdir "%USERPROFILE%\.codex\sqlite\ghostchat-patch"
>"%USERPROFILE%\.codex\sqlite\ghostchat-patch\watcher.stop" echo stop
timeout /t 4 /nobreak >nul
del /Q "%USERPROFILE%\.codex\sqlite\ghostchat-patch\watcher.stop" >nul 2>&1
wscript.exe "%INSTALLDIR%\run_watcher.vbs"

echo.
echo Installed to: %INSTALLDIR%
echo Starts automatically with Windows: YES
echo Started now: YES
echo.
echo You can keep using the NORMAL ChatGPT icon.
echo The watcher runs hidden in the background.
echo.
echo Desktop shortcut added: ChatGPT - Sync ^& Fix
echo Use it only when a deleted chat remains stuck in Recents.
echo.
echo Useful controls:
echo   %INSTALLDIR%\ghostchat_status.cmd
echo   %INSTALLDIR%\stop_watcher.cmd
echo   %INSTALLDIR%\start_watcher_now.cmd
echo   %INSTALLDIR%\hot_repair_now.cmd
echo   %INSTALLDIR%\test_sync_nudge.cmd
echo   %INSTALLDIR%\test_search_toggle_nudge.cmd
echo   %INSTALLDIR%\sync_fix_now.cmd
echo   %INSTALLDIR%\smart_restart_status.cmd
echo.
pause
