param([ValidateSet('install','start','stop','status','dry-run','repair','restore','uninstall')][string]$Action = 'status')
$ErrorActionPreference = 'Stop'
$gcBase = [IO.Path]::GetFullPath($PSScriptRoot)
$gcDb = Join-Path $env:USERPROFILE '.codex\sqlite\codex-dev.db'
$gcStateDir = Join-Path $env:USERPROFILE '.codex\sqlite\ghostchat-patch'
$gcStatusFile = Join-Path $gcStateDir 'watcher-status.json'
$gcStartup = [Environment]::GetFolderPath('Startup')
$gcShortcut = Join-Path $gcStartup 'GhostChatTool v3.0.1.lnk'
$gcTarget = Join-Path $env:LOCALAPPDATA 'GhostChatTool-v3.0.1'

function Get-GcPython {
    foreach ($candidate in @('py', 'python')) {
        if (Get-Command $candidate -ErrorAction SilentlyContinue) {
            $gcArgs = @('-c', 'import sys; assert sys.version_info >= (3,10), "Python 3.10+ required"; print(sys.executable)')
            if ($candidate -eq 'py') { $gcArgs = @('-3') + $gcArgs }
            $gcResult = & $candidate @gcArgs 2>$null
            if ($LASTEXITCODE -eq 0 -and $gcResult -and (Test-Path -LiteralPath ([string]$gcResult))) { return [string]$gcResult }
        }
    }
    throw 'Python 3.10+ was not found. Install Python for Windows, then try again.'
}

function Get-GcProcesses {
    # Read command lines only for Python hosts; never inspect process memory or credentials.
    @(Get-CimInstance Win32_Process -Filter "Name = 'python.exe' OR Name = 'pythonw.exe'" |
        Where-Object { $_.CommandLine -match 'ghostchat_watch\.py' })
}

function Assert-GcNoOtherWatcher {
    $gcForeign = @(Get-GcProcesses | Where-Object { $_.CommandLine.IndexOf((Join-Path $gcBase 'ghostchat_watch.py'), [StringComparison]::OrdinalIgnoreCase) -lt 0 })
    if ($gcForeign.Count) { throw 'Another GhostChat watcher is active. Stop that version first. Nothing was changed.' }
}

function Assert-GcSchema([string]$Python) {
    $gcCheck = 'import pathlib,sqlite3,sys; p=pathlib.Path(sys.argv[1]); assert p.is_file(), "Local database not found"; c=sqlite3.connect(p.as_uri()+"?mode=ro",uri=True); cols={r[1] for r in c.execute("PRAGMA table_info(local_thread_catalog)")}; c.close(); assert {"thread_id","source_kind","project_id","display_title"} <= cols, "Unsupported catalog schema: no repair started"'
    & $Python -c $gcCheck $gcDb
    if ($LASTEXITCODE -ne 0) { throw 'Database/schema check failed. No watcher or repair was started.' }
}

function Stop-GcWatcher {
    Assert-GcNoOtherWatcher
    if (@(Get-GcProcesses).Count -eq 0) { Write-Host 'Watcher is stopped.'; return }
    New-Item -ItemType Directory -Path $gcStateDir -Force | Out-Null
    Set-Content -LiteralPath (Join-Path $gcStateDir 'watcher.stop') -Value 'stop' -Encoding ASCII
    $gcDeadline = (Get-Date).AddSeconds(45)
    do {
        Start-Sleep -Milliseconds 500
        if (@(Get-GcProcesses).Count -eq 0) { Write-Host 'Watcher stopped.'; return }
    } while ((Get-Date) -lt $gcDeadline)
    throw 'Watcher has not stopped yet. Wait and retry; no process was force-terminated.'
}

function Start-GcWatcher {
    Assert-GcNoOtherWatcher
    if (@(Get-GcProcesses).Count) { Write-Host 'Watcher is already running.'; return }
    $gcPython = Get-GcPython
    Assert-GcSchema $gcPython
    $gcPythonW = Join-Path (Split-Path $gcPython) 'pythonw.exe'
    if (-not (Test-Path -LiteralPath $gcPythonW)) { throw 'pythonw.exe is missing; use a complete Python for Windows installation.' }
    $gcScript = Join-Path $gcBase 'ghostchat_watch.py'
    Start-Process -FilePath $gcPythonW -ArgumentList @(('"' + $gcScript + '"'), '--no-refetch-bridge') -WorkingDirectory $gcBase -WindowStyle Hidden | Out-Null
    Start-Sleep -Seconds 2
    if (@(Get-GcProcesses).Count -eq 0) { throw 'Watcher did not stay running. Check the local watcher log; no success is assumed.' }
    Write-Host 'Background watcher started. No browser or automatic app restart is used.'
}

function Assert-GcAppClosed {
    # Errors are not treated as proof that the app is closed.
    if (@(Get-CimInstance Win32_Process -Filter "Name = 'ChatGPT.exe'").Count) { throw 'Quit ChatGPT completely first, including any background process. Nothing was force-closed.' }
}

try {
    switch ($Action) {
        'install' {
            $gcPython = Get-GcPython
            Assert-GcSchema $gcPython
            $gcOldLinks = @(Get-ChildItem -LiteralPath $gcStartup -File | Where-Object { $_.Name -like '*GhostChat*' })
            if ($gcOldLinks.Count -or @(Get-GcProcesses).Count) { throw 'An existing GhostChat startup entry or watcher was found. Keep your existing v3.0.1 or disable/uninstall the older installation before installing this package. See the guide.' }
            if (Test-Path -LiteralPath $gcTarget) { throw "Target already exists: $gcTarget. No files were overwritten. Use that installation or rename the inactive folder yourself." }
            Write-Host 'This experimental tool can modify the local ChatGPT database automatically when explicit deletion evidence exists in local logs.'
            Write-Host 'It adds a login-startup shortcut. It does not guarantee server synchronization. Read GUIDE.html first.'
            if ((Read-Host 'Type INSTALL to continue') -cne 'INSTALL') { Write-Host 'Cancelled.'; break }
            New-Item -ItemType Directory -Path $gcTarget | Out-Null
            $gcFiles = @('ghostchat_patch.py','ghostchat_watch.py','ghostchat_nudge.py','ghostchat_refetch_bridge.py','controls.ps1','INSTALL.cmd','START.cmd','STOP.cmd','STATUS.cmd','DRY_RUN.cmd','REPAIR_ONCE.cmd','RESTORE.cmd','UNINSTALL.cmd','README.md','GUIDE.html','GUIDE.en.md','GUIDE.it.md','GUIDE.es.md','GUIDE.fr.md','GUIDE.de.md','LICENSE','CORE_SHA256.json','TEST_REPORT.md','test_release.py')
            foreach ($gcName in $gcFiles) { Copy-Item -LiteralPath (Join-Path $gcBase $gcName) -Destination (Join-Path $gcTarget $gcName) }
            $gcShell = New-Object -ComObject WScript.Shell
            $gcLink = $gcShell.CreateShortcut($gcShortcut)
            $gcLink.TargetPath = Join-Path $PSHOME 'powershell.exe'
            $gcLink.Arguments = '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + (Join-Path $gcTarget 'controls.ps1') + '" -Action start'
            $gcLink.WorkingDirectory = $gcTarget
            $gcLink.WindowStyle = 7
            $gcLink.Description = 'GhostChatTool v3.0.1 local log watcher; no browser'
            $gcLink.Save()
            Write-Host "Installed: $gcTarget"
            & (Join-Path $gcTarget 'controls.ps1') -Action start
            if ($LASTEXITCODE -ne 0) { throw 'Installed, but startup failed. Run STATUS.cmd in the installed folder.' }
        }
        'start' { Start-GcWatcher }
        'stop' { Stop-GcWatcher }
        'status' {
            Write-Host 'GhostChatTool v3.0.1 (local-log repair; no browser)'
            Write-Host ('Watcher processes: ' + @(Get-GcProcesses).Count)
            Write-Host ('This package login startup: ' + (Test-Path -LiteralPath $gcShortcut))
            if (Test-Path -LiteralPath $gcStatusFile) {
                $gcState = Get-Content -LiteralPath $gcStatusFile -Raw | ConvertFrom-Json
                Write-Host ('Reported version: ' + $gcState.version)
                Write-Host ('Status updated: ' + $gcState.updated_at)
                Write-Host ('Last repair: ' + $gcState.last_repair_at)
                Write-Host ('Entries in last repair: ' + $gcState.last_repair_count)
                Write-Host ('Last message: ' + $gcState.last_message)
                Write-Host 'A previous repair/status is history, not proof that the current chat was repaired.'
            } else { Write-Host 'No status file yet.' }
            Write-Host ('Private logs: ' + $gcStateDir)
        }
        'dry-run' {
            $gcPython = Get-GcPython
            Assert-GcSchema $gcPython
            Write-Host 'This command does not modify the database. An already-running watcher remains independent; stop it for a fully read-only test.'
            & $gcPython (Join-Path $gcBase 'ghostchat_patch.py') --dry-run --allow-running --no-launch --audit
            if ($LASTEXITCODE -ne 0) { throw 'Dry-run could not complete. Read the error above.' }
        }
        'repair' {
            Assert-GcNoOtherWatcher
            if (@(Get-GcProcesses).Count) { throw 'Run STOP.cmd first to avoid concurrent repairs.' }
            Assert-GcAppClosed
            $gcPython = Get-GcPython
            Assert-GcSchema $gcPython
            & $gcPython (Join-Path $gcBase 'ghostchat_patch.py') --no-launch
            if ($LASTEXITCODE -ne 0) { throw 'Repair command failed. Read the output and logs.' }
            Write-Host 'Check the result above. Reopen the app yourself; use START.cmd to resume the watcher.'
        }
        'restore' {
            Stop-GcWatcher
            Assert-GcAppClosed
            $gcPython = Get-GcPython
            Assert-GcSchema $gcPython
            Write-Host 'WARNING: this restores the newest GhostChat snapshot of the ENTIRE local database, potentially reverting unrelated local changes.'
            if ((Read-Host 'Type RESTORE to continue') -cne 'RESTORE') { Write-Host 'Restore cancelled. Watcher remains stopped.'; break }
            & $gcPython (Join-Path $gcBase 'ghostchat_patch.py') --restore-latest --no-launch
            if ($LASTEXITCODE -ne 0) { throw 'Restore did not complete. Preserve backups and check the error.' }
            Write-Host 'Watcher remains stopped. Login startup is unchanged; START.cmd resumes it and can reapply deletion evidence.'
        }
        'uninstall' {
            Stop-GcWatcher
            if (Test-Path -LiteralPath $gcShortcut) {
                $gcShell = New-Object -ComObject WScript.Shell
                $gcLink = $gcShell.CreateShortcut($gcShortcut)
                $gcExpected = Join-Path $gcTarget 'controls.ps1'
                if ($gcLink.Arguments -notlike ('*"' + $gcExpected + '"*')) { throw 'Startup shortcut points somewhere unexpected; it was not removed.' }
                Remove-Item -LiteralPath $gcShortcut
            }
            Write-Host 'This package login startup removed; watcher stopped. Program files, database, logs and backups were preserved. Delete the inactive installation folder yourself only if desired.'
        }
    }
    exit 0
} catch {
    Write-Host ('ERROR: ' + $_.Exception.Message) -ForegroundColor Red
    exit 1
}
