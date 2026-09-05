```md
> **Latest release: v2.2.0 - Sync & Fix**  
> [Download GhostChatTool v2.2.0](https://github.com/Ale31199/GhostChatTool/releases/tag/v2.2.0)
>
> GhostChatTool v2.2.0 is a Windows workaround for stale or deleted ChatGPT Desktop conversations that remain stuck under **Recents** after deletion from another device.
>
> This release includes **Smart Restart / Sync & Fix**, which safely restarts ChatGPT when needed, performs a local catalog reconciliation, creates automatic SQLite backups, excludes Project chats, and runs `PRAGMA integrity_check` after repairs.
>
> Automatic removal requires strong local evidence: the exact `thread_id` together with an explicit `conversation_deleted` event. `missing_candidate`, generic errors, or unavailable conversations alone are not treated as proof of deletion.
>
> GhostChatTool does **not** read `auth.json`, extract tokens or cookies, call private ChatGPT account APIs, modify `ChatGPT.exe`, inject code, or send messages.
>
> **v3.0.1 was an experimental branch and is no longer the recommended release. v2.2.0 is the currently recommended version.**

# GhostChatTool

GhostChatTool is an unofficial Windows utility designed to repair **stale local ChatGPT Recents entries**, commonly referred to as "Ghost chats".

The issue can occur when a conversation is deleted from another device, such as a phone, browser, or second PC, but remains visible in the new ChatGPT Windows desktop app.

The underlying conversation may already be gone from the server while the Windows app continues to keep a stale local reference.

> [!IMPORTANT]
> GhostChatTool is an **unofficial community workaround**. It is not affiliated with, endorsed by, or maintained by OpenAI. ChatGPT's local storage format may change in future versions.

## The problem

A typical affected scenario looks like this:

```text
Phone / Browser
    |
    | delete conversation
    v
ChatGPT server
    |
    | conversation removed
    v
Other clients
    |
    +-- Browser: removed
    +-- Mobile: removed
    +-- Desktop PC 1: removed
    |
    +-- Desktop PC 2: still visible
                         |
                         +-- cannot be opened
                         +-- cannot be archived
                         +-- cannot be deleted
                         +-- may show "Unable to load conversation"
```

GhostChatTool repairs the stale local Windows entry without attempting to delete the conversation from the server.

## Latest recommended version

### GhostChatTool v2.2.0 - Sync & Fix

v2.2.0 adds a safer workflow for cases where remote conversation deletions are not immediately reflected by the Windows Desktop client.

The installer provides:

```text
ChatGPT - Sync & Fix
```

This performs a controlled ChatGPT restart and reconciliation cycle so that deletion evidence can become visible locally before the repair logic acts.

## What v2.2.0 does

GhostChatTool works with the local ChatGPT/Codex SQLite catalog located at:

```text
%USERPROFILE%\.codex\sqlite\codex-dev.db
```

The v2.2.0 workflow can:

- monitor the local ChatGPT conversation catalog;
- detect strongly confirmed deleted conversations;
- exclude Project chats;
- create a timestamped SQLite backup before repair;
- remove only the exact matching `thread_id`;
- update the local catalog revision when supported;
- verify that the stale row has been removed;
- run `PRAGMA integrity_check`;
- save repair logs and manifests;
- safely relaunch the official ChatGPT Windows app through Sync & Fix.

## Strong deletion evidence

GhostChatTool does **not** automatically delete a local conversation merely because it appears suspicious.

Automatic repair requires strong local evidence:

```text
exact thread_id
+
explicit conversation_deleted event
```

The following conditions alone are **not enough**:

```text
missing_candidate = 1
generic 404 / unavailable error
conversation_not_loaded
Unable to load conversation
stale title
```

This conservative behavior is intentional.

## Smart Restart / Sync & Fix

Testing showed that remote deletions can remain invisible to the affected ChatGPT Windows Desktop client until it performs a stronger synchronization.

Two actions were observed to reliably trigger this synchronization:

```text
sending a normal message from Desktop
```

or:

```text
closing and reopening ChatGPT
```

GhostChatTool v2.2.0 therefore includes **Sync & Fix**, which automates the restart workflow without sending messages.

The process is:

```text
Sync & Fix
    |
    v
pre-scan confirmed Ghost entries
    |
    v
request normal ChatGPT close
    |
    v
safe local reconciliation
    |
    v
launch official ChatGPT app
    |
    v
post-launch reconciliation window
    |
    v
repair confirmed Ghost entries
```

If ChatGPT does not close normally, GhostChatTool asks before attempting a forced termination.

> [!WARNING]
> Do not run Sync & Fix while you have unsent text in the ChatGPT composer. Unsaved text could be lost if the app must be terminated.

## Safety

GhostChatTool intentionally avoids broad or destructive cleanup operations.

It does **not**:

```text
delete every missing_candidate row
delete Project chats
delete server-side conversations
read auth.json
extract account tokens
extract cookies
call private ChatGPT account APIs
modify ChatGPT.exe
inject DLLs or code
send messages
upload conversation data
```

Repairs target the exact conversation `thread_id`.

## Projects

Project conversations are excluded from the cleanup logic.

The supported catalog query filters for normal ChatGPT conversations and avoids Project-associated rows whenever the required schema is available.

## Backups

Before every confirmed database repair, GhostChatTool creates a backup under:

```text
%USERPROFILE%\.codex\sqlite\ghostchat-backups
```

Example:

```text
codex-dev-20260905-221500.db
```

Repair manifests and logs are also stored locally.

## Database integrity

After a repair, GhostChatTool runs:

```sql
PRAGMA integrity_check;
```

The expected result is:

```text
ok
```

If integrity verification fails, the tool reports the problem instead of pretending that the repair succeeded.

## Restore

The package includes restore functionality for reverting to a previous GhostChatTool backup.

Restoring a database snapshot replaces the local SQLite state with the selected backup.

> [!WARNING]
> A restore can also revert unrelated local ChatGPT changes made after that backup was created. Use restore only when necessary.

## Requirements

- Windows 10 or Windows 11
- New ChatGPT Windows Desktop app using the `.codex` SQLite catalog
- Python available through `py` or `python`

No third-party Python packages are required for the core tool.

## Installation

Download the latest release:

[GhostChatTool v2.2.0](https://github.com/Ale31199/GhostChatTool/releases/tag/v2.2.0)

Extract the ZIP completely.

Run:

```text
install_ghostchat_patch.cmd
```

The installer sets up the background watcher and creates the Sync & Fix shortcut.

## Main commands

Depending on the package build, the main helper scripts include:

```text
install_ghostchat_patch.cmd
sync_fix_now.cmd
smart_restart_status.cmd
ghostchat_status.cmd
restore_latest_backup.cmd
```

The desktop shortcut:

```text
ChatGPT - Sync & Fix
```

is the recommended way to manually trigger a full synchronization and cleanup cycle.

## Manual legacy tool

The repository also contains the original GhostChatTool v1.0.0 workflow.

That version allows manual selection of a stale conversation by number or exact `thread_id` and requires typing:

```text
DELETE
```

before removing the selected local catalog row.

The original manual tool remains useful as a fallback and for targeted troubleshooting.

## Why thread_id instead of title?

Different conversations can have identical titles.

For example:

```text
Test
Test
Test
```

A title is therefore not a safe unique identifier.

GhostChatTool uses the exact:

```text
thread_id
```

to target the intended local conversation entry.

## Privacy

GhostChatTool is designed to operate locally.

It does not intentionally transmit:

```text
conversation text
thread IDs
SQLite databases
backup files
authentication files
cookies
tokens
repair manifests
```

to external services.

## Troubleshooting

### The Ghost chat is still visible

The ChatGPT Windows app can temporarily keep its sidebar state in memory.

If a repair has already succeeded but the entry remains visible, use:

```text
ChatGPT - Sync & Fix
```

to force the normal restart/reconciliation workflow.

### ChatGPT will not close

The tool first requests a normal Windows close.

If that fails, it can ask for permission before forcing termination.

### Database not found

The installed ChatGPT version may use a different local storage layout.

Do not delete random SQLite files or folders.

### Python not found

Make sure either:

```text
py
```

or:

```text
python
```

works from PowerShell or Windows Terminal.

### A Project conversation appears

Do not repair it manually.

Stop and verify the schema and filtering before proceeding.

## Version history

### v2.2.0

Recommended release.

Introduced:

```text
Smart Restart / Sync & Fix
background watcher
safe pre-scan
post-launch reconciliation
automatic backups
repair manifests
restore support
strong conversation_deleted evidence requirement
```

### v1.0.0

Original manual GhostChatTool release.

Manual `thread_id` selection with explicit `DELETE` confirmation.

### v3.0.1

Experimental branch.

It explored early refetch/reload approaches intended to avoid restarting the ChatGPT Desktop app.

Those approaches were not reliable enough on the affected Windows build and v3.0.1 is **not the recommended release**.

## Disclaimer

GhostChatTool modifies local data used by a third-party application.

Always keep backups.

The ChatGPT Windows application, its SQLite schema, process behavior, and synchronization logic may change at any time.

Future ChatGPT updates may require changes to GhostChatTool.

## License

MIT. See [LICENSE](LICENSE).
```

Poi clicca **Commit changes...**.

Nel campo **Commit message** metti soltanto:

```text
Update README for GhostChatTool v2.2.0
```
