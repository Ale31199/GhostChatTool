@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0controls.ps1" -Action stop
set "GC_EXIT=%ERRORLEVEL%"
echo.
pause
exit /b %GC_EXIT%
