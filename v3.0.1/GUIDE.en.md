# GhostChatTool v3.0.1 — User guide

English (default) · [Italiano](GUIDE.it.md) · [Español](GUIDE.es.md) · [Français](GUIDE.fr.md) · [Deutsch](GUIDE.de.md)

## 1. Which version is this?

The browser-free v3.0.1 local-log watcher. It is not v1's manual selector or v4's browser extension. The runtime is unchanged; this package adds installation controls and multilingual documentation. The optional automatic reload bridge and nudges are disabled by the supplied launchers. You close and reopen the desktop app yourself when its list stays stale.

This is an unofficial, experimental workaround. It cannot promise that every remotely deleted chat disappears, even after reopening. It repairs only when local app logs contain the chat ID and `conversation_deleted` or `conversation deleted` on the same line. No usable event means no repair. It does not independently verify the server or perform two server checks.

## 2. Before installing

Use Windows 10/11, Python 3.10+ (`py` or `python`), and Windows PowerShell. The app must use `%USERPROFILE%\.codex\sqlite\codex-dev.db`. No Python packages, browser or credentials are required. Extract the complete ZIP; do not run files inside the compressed-folder preview.

Already have a working v3.0.1? You do not need to install a second copy. To migrate, stop the old watcher and disable its login startup using its own uninstall instructions first. Inspect startup entries with Windows + R, `shell:startup`. Do not delete unfamiliar entries or your `.codex` directory. The installer refuses any existing GhostChat startup entry, active watcher, or existing destination folder. It does not silently remove older versions or v4 browser extensions.

## 3. Install and start

Open `GUIDE.html` locally if you prefer the language selector. Run `DRY_RUN.cmd` to inspect without that command writing to the database. A separate active watcher may still write: stop it first for a fully read-only check.

Double-click `INSTALL.cmd`, read the warning and type `INSTALL`. Installation goes to `%LOCALAPPDATA%\GhostChatTool-v3.0.1`. It adds `GhostChatTool v3.0.1.lnk` to your Windows login Startup folder and starts the hidden watcher. No administrator rights are needed. Startup is at user login, not a Windows service; Windows and the logged-in session must be running.

Use `STATUS.cmd`, `STOP.cmd` and `START.cmd` in the **installed folder**. Stop pauses now but keeps login startup. If installation reports an error, do not assume the watcher is active. Check status and the error first. Do not bypass an organizational security policy to run this tool.

## 4. Test with one disposable chat

1. Create a clearly named test conversation outside Projects and confirm it appears on desktop.
2. Delete that test conversation from the phone. Keep the desktop app online; deleting a real conversation is permanent server-side, so use disposable content only.
3. After the desktop receives the event, check `STATUS.cmd`. A **new** repair timestamp, matching repair details in the private manifest, and count greater than zero indicate a local repair. A previous repair is not evidence for this test.
4. If the chat remains visible, quit the desktop app completely, including its background process, and reopen it from Start. There is no required Reload button and GhostChat does not force-close the app.
5. If there is no new repair, stop the watcher, quit the app and run `DRY_RUN.cmd`. No matching event means the tool leaves the entry untouched. Optionally run `REPAIR_ONCE.cmd` while both watcher and app are closed to repair confirmed candidates; then reopen the app and use `START.cmd`.

Polling is normally three seconds, with log rediscovery about every fifteen seconds, but this is **not a delivery-time guarantee**. The app may never log the required event. Do not repeatedly delete other chats to test a failure.

## 5. Backups, logs and recovery

Backups: `%USERPROFILE%\.codex\sqlite\ghostchat-backups`. Private status, logs and repair manifests: `%USERPROFILE%\.codex\sqlite\ghostchat-patch`. Up to 20 timestamped snapshots are kept after repairs, shared with older GhostChat versions. Copy important snapshots to a safe private location before they age out.

`RESTORE.cmd` stops this package's watcher, requires the app to be fully closed and asks you to type `RESTORE`. It restores the newest backup of the **whole local database**, not one selected chat, and creates a pre-restore backup. This may revert unrelated local state. The watcher stays stopped afterwards, but login startup remains enabled and starting again can reapply the same repair. Use `UNINSTALL.cmd` first if you want startup disabled during recovery, then run restore from the preserved files.

`UNINSTALL.cmd` stops the watcher and removes only this package's login shortcut. Program files, chat database, logs and backups are preserved. It does not uninstall v1/v4 or remove browser extensions. It does not undo past repairs.

## 6. Limits and privacy

The supplied launchers check required database columns before starting; Project exclusion in the legacy core relies on `project_id` being available. Future schema changes are not universally fail-closed. Repair uses a pre-change SQLite backup and a post-commit `PRAGMA integrity_check`; integrity checking does not prove server deletion and does not automatically roll back a bad committed result. Stop using the tool if an app update breaks compatibility.

No cookies, tokens or `auth.json` are read or exported. No private API requests or executable injection are used. However, local logs/backups/manifests may contain sensitive data. Never share them unredacted. The downloadable release contains only code, guides and synthetic tests. See `README.md` for full technical limitations and `TEST_REPORT.md` for what was actually tested.
