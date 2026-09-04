# GhostChatTool v3.0.1 — Windows

**No browser required. Local repair, with a manual app close/reopen when needed.**

[English](GUIDE.en.md) · [Italiano](GUIDE.it.md) · [Español](GUIDE.es.md) · [Français](GUIDE.fr.md) · [Deutsch](GUIDE.de.md)

Open **GUIDE.html** for the offline multilingual guide. English is the default language.

This is an **unofficial, experimental community workaround**, not an OpenAI patch. It watches local app logs and removes matching stale entries from the local SQLite catalog. It does not connect to ChatGPT servers, inspect browser sessions, or delete server conversations.

## What to expect

1. Delete a disposable, non-Project chat on another device.
2. Keep the desktop app connected and the GhostChat watcher running.
3. Repair is possible **only if the desktop logs contain the thread ID and an explicit `conversation_deleted` / `conversation deleted` marker on the same line**.
4. Check **STATUS.cmd** for a new repair timestamp. Quit the desktop app completely and reopen it if its sidebar still displays the chat.

**Closing/reopening is not a guarantee of repair.** If there is no qualifying log event, v3.0.1 leaves the entry alone. A historical “last repair” does not prove that the current chat was repaired. No instant cross-device synchronization or fixed delay is promised.

## Quick start

- Windows 10/11; Python 3.10+ available as `py` or `python`; Windows PowerShell and the desktop app using `%USERPROFILE%\.codex\sqlite\codex-dev.db`. No additional Python packages.
- Extract the ZIP fully. Read the guide first.
- If an older GhostChat version is installed, **do not install a second watcher**. This installer refuses existing GhostChat startup entries or an active watcher. The source ZIP is still usable for sharing without reinstalling your existing v3.0.1.
- Run **DRY_RUN.cmd** to inspect candidates without this command changing the database. Stop any existing watcher first if you need a completely read-only test.
- Run **INSTALL.cmd**, read the warning and type `INSTALL`. This installs to `%LOCALAPPDATA%\GhostChatTool-v3.0.1`, creates a user-login startup shortcut, and starts the background watcher. No administrator rights, browser, login, or account credentials are needed.
- Run **STATUS.cmd** in the installed folder to check startup and repair status. Use **STOP.cmd** to pause and **START.cmd** to resume. Stopping does not remove login startup.
- **UNINSTALL.cmd** removes this package's login startup shortcut and stops its watcher. It intentionally preserves the installed files, database, logs and backups.

## Packaging scope

The four original runtime modules are preserved byte-for-byte: `ghostchat_patch.py`, `ghostchat_watch.py`, `ghostchat_refetch_bridge.py`, and `ghostchat_nudge.py`. Their hashes are recorded in `CORE_SHA256.json`.

This distribution adds English launchers, installation controls, guides and offline tests. The launchers disable the optional native-menu reload bridge (`--no-refetch-bridge`) and leave focus/keyboard nudges disabled. The watcher can still repair the local catalog while the app is open; **you control closing/reopening the app**. Launching the raw watcher without these flags uses its original defaults and is outside the documented workflow.

The old v1.0.0 manual selector, v2.2 smart-restart tool, v4 browser extension, private configuration, chat data, logs and backups are not bundled. Repository-root files from v1.0.0 remain historical; use this version's ZIP or folder, not a mixture.

## Safety and known limitations

- A SQLite snapshot is created before a repair; `PRAGMA integrity_check` runs after the committed change. This does not verify server state and is not an automatic rollback guarantee.
- Repairs target `source_kind='chatgpt'`. Project exclusion depends on the `project_id` column. The new launchers refuse a schema without required columns before starting; the unchanged legacy core is not universally fail-closed under future schema changes. Stop using it after an incompatible app update.
- `missing_candidate=1`, a generic 404, or `conversation_not_loaded` alone is not deletion evidence. This is **not** v4's browser-based two-check reconciliation.
- Logs can be absent, delayed, rotated, inaccessible, or outside the scan limits (normally recent seven days, up to 25 MiB per file and 80 MiB total). An app repair can be overwritten by the running app, and displayed lists can remain cached.
- Legacy process checks and post-commit integrity checks have limitations. Keep backups; use at your own risk. This has not been certified against every app build or Windows configuration.
- Backups keep up to 20 `codex-dev-*.db` snapshots after repair. This location is shared with older versions. Preserve important backups elsewhere before they age out.
- Restore replaces the **whole local database snapshot**, not just one chat. It can revert unrelated local changes. Stop GhostChat and quit the desktop app completely first; see the guide.
- Never upload runtime logs, manifests, databases or backups: they may contain chat titles, identifiers, excerpts and other private local data. The program makes no direct network requests and does not read `auth.json`, export credentials or modify/inject into the app executable.

## Tests and license

Run `py -3 -m unittest -v test_release.py` from this folder. The tests use temporary synthetic databases and logs, not your ChatGPT database. See `TEST_REPORT.md` for the recorded checks and their limits.

MIT — see [LICENSE](LICENSE). Report issues with the tool version, Windows/app version, and a **redacted** error. Do not attach private databases or logs.
