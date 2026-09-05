# GhostChat Sync Fix v2.2.0

v2.2 keeps the conservative background repair from v2.0/v2.1 and adds a **Smart Restart** command for the behavior observed on the affected ChatGPT Windows build.

## What testing established

A remote deletion can remain invisible to the Desktop client until the app performs a stronger sync. In testing, two actions reliably caused that sync:

- sending a normal message from Desktop;
- closing and reopening ChatGPT.

The v2.1 activation/search nudges were not reliable enough. v2.2 therefore does **not** pretend they are a fix.

## New: `ChatGPT - Sync & Fix`

The installer creates this desktop shortcut:

```text
ChatGPT - Sync & Fix
```

Use it only when a deleted conversation is stuck in Desktop Recents.

One click performs:

1. a conservative pre-scan for already-confirmed ghosts;
2. a normal `WM_CLOSE` request to ChatGPT;
3. if ChatGPT refuses to close, an explicit confirmation is shown before any forced termination;
4. one safe reconcile while ChatGPT is closed;
5. launch of the official Microsoft Store ChatGPT app;
6. a short post-launch reconcile window so newly emitted `conversation_deleted` evidence can be repaired;
7. normal background watcher continues afterward.

The command never sends a chat message and never modifies ChatGPT.exe.

## Important

Do not run **Sync & Fix** while you have unsent text in the composer. A normal app close is requested first, but if ChatGPT cannot close, the tool may offer a force-close confirmation.

## Conservative repair rules

The SQLite repair still requires strong local evidence:

```text
exact thread_id + explicit conversation_deleted marker
```

`missing_candidate=1`, a generic 404, or `conversation_not_loaded` alone are not enough.

Projects remain excluded. A database backup is created before every removal and `PRAGMA integrity_check` must remain `ok`.

## Install / upgrade

Run:

```text
install_ghostchat_patch.cmd
```

The watcher starts automatically and the desktop shortcut is created.

## Manual commands

```text
sync_fix_now.cmd
smart_restart_status.cmd
ghostchat_status.cmd
restore_latest_backup.cmd
```

## Why this is manual rather than fully automatic

The affected Desktop client may not expose the remote delete locally until a strong sync occurs. Before that sync the watcher has no trustworthy deletion evidence, so automatically restarting ChatGPT whenever a remote delete *might* exist would require blind periodic restarts. v2.2 deliberately avoids that behavior.
