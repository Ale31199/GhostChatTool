@echo off
setlocal
set "INSTALLDIR=%USERPROFILE%\GhostChatTool"

echo Removing GhostChatTool...

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$dir=[IO.Path]::GetFullPath('%INSTALLDIR%').TrimEnd('\');" ^
  "$p=[Environment]::GetEnvironmentVariable('Path','User');" ^
  "if($p){$parts=$p -split ';' | Where-Object { $_ -and $_.Trim() }; $new=@(); foreach($x in $parts){try{if([IO.Path]::GetFullPath($x).TrimEnd('\') -ine $dir){$new += $x}}catch{$new += $x}}; [Environment]::SetEnvironmentVariable('Path',($new -join ';'),'User')}"

if exist "%INSTALLDIR%" rmdir /S /Q "%INSTALLDIR%"

echo Done.
echo Open a new terminal for PATH changes to take effect.
pause
