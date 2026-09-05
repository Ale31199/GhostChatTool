@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>&1
if %errorlevel%==0 (
    py "%~dp0ghostchat_smart_restart.py" %*
    exit /b %errorlevel%
)

where python >nul 2>&1
if %errorlevel%==0 (
    python "%~dp0ghostchat_smart_restart.py" %*
    exit /b %errorlevel%
)

exit /b 1
