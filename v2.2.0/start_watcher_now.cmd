@echo off
setlocal
cd /d "%~dp0"
wscript.exe "%~dp0run_watcher.vbs"
echo GhostChat Background Watcher start requested.
echo Use ghostchat_status.cmd to check it.
timeout /t 2 /nobreak >nul
call "%~dp0ghostchat_status.cmd"
