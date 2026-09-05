@echo off
setlocal
set "STOPDIR=%USERPROFILE%\.codex\sqlite\ghostchat-patch"
if not exist "%STOPDIR%" mkdir "%STOPDIR%"
>"%STOPDIR%\watcher.stop" echo stop
echo Stop requested. The watcher will exit on its next poll.
timeout /t 4 /nobreak >nul
