@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>&1
if %errorlevel%==0 (
    py "%~dp0ghostchat.py" %*
    exit /b %errorlevel%
)

where python >nul 2>&1
if %errorlevel%==0 (
    python "%~dp0ghostchat.py" %*
    exit /b %errorlevel%
)

echo.
echo Python was not found.
echo Install Python or make sure py/python is available in PATH.
exit /b 1
