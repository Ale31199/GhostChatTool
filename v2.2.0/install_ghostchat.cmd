@echo off
setlocal
set "INSTALLDIR=%USERPROFILE%\GhostChatTool"

echo.
echo GhostChatTool v1.0.0
echo Installing to:
echo   %INSTALLDIR%
echo.

if not exist "%INSTALLDIR%" mkdir "%INSTALLDIR%"

copy /Y "%~dp0ghostchat.py" "%INSTALLDIR%\ghostchat.py" >nul
copy /Y "%~dp0ghostchat.cmd" "%INSTALLDIR%\ghostchat.cmd" >nul

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$dir=[IO.Path]::GetFullPath('%INSTALLDIR%').TrimEnd('\');" ^
  "$p=[Environment]::GetEnvironmentVariable('Path','User');" ^
  "$parts=@(); if($p){$parts=$p -split ';' | Where-Object { $_ -and $_.Trim() }};" ^
  "$exists=$false; foreach($x in $parts){try{if([IO.Path]::GetFullPath($x).TrimEnd('\') -ieq $dir){$exists=$true}}catch{}};" ^
  "if(-not $exists){[Environment]::SetEnvironmentVariable('Path',(($parts + $dir) -join ';'),'User')}"

echo Installation complete.
echo.
echo Open a NEW PowerShell or Windows Terminal window and run:
echo.
echo   ghostchat
echo.
echo Other useful commands:
echo   ghostchat --help
echo   ghostchat --version
echo   ghostchat --list
echo.
pause
