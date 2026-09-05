```md
# GhostChatTool v2.2.0 - Sync & Fix

GhostChatTool v2.2.0 is the currently recommended release.

It is an unofficial Windows workaround for ChatGPT Desktop conversations that have already been deleted from another device but remain stuck under **Recents** in the Windows app.

## What changed

v2.2.0 introduces **Smart Restart / Sync & Fix**.

Testing showed that some remote deletions are not immediately reflected by the affected ChatGPT Windows Desktop client. A stronger synchronization can occur after closing and reopening the app.

Sync & Fix automates that workflow.

## Main features

- Smart Restart / Sync & Fix
- Conservative background watcher
- Automatic SQLite backup before repairs
- Exact `thread_id` targeting
- Project conversations excluded
- Post-launch reconciliation window
- Repair logs and manifests
- Restore support
- SQLite integrity verification with `PRAGMA integrity_check`

## Repair safety

Automatic removal requires strong local evidence:

```text
exact thread_id
+
explicit conversation_deleted event
```

The following alone are not considered sufficient evidence:

```text
missing_candidate = 1
conversation_not_loaded
generic 404
Unable to load conversation
stale conversation title
```

GhostChatTool does not blindly delete suspicious catalog entries.

## Privacy

GhostChatTool does not:

- read `auth.json`
- extract account tokens
- extract browser cookies
- call private ChatGPT account APIs
- upload conversation data
- modify `ChatGPT.exe`
- inject code or DLLs
- send ChatGPT messages

## Database

The affected local catalog is typically stored at:

```text
%USERPROFILE%\.codex\sqlite\codex-dev.db
```

Backups are created before confirmed repairs under:

```text
%USERPROFILE%\.codex\sqlite\ghostchat-backups
```

After a repair, GhostChatTool runs:

```sql
PRAGMA integrity_check;
```

The expected result is:

```text
ok
```

## Installation

Download the Windows ZIP from the GitHub release:

https://github.com/Ale31199/GhostChatTool/releases/tag/v2.2.0

Extract it completely and run:

```text
install_ghostchat_patch.cmd
```

The installer creates the:

```text
ChatGPT - Sync & Fix
```

shortcut.

## Important

Do not run Sync & Fix while you have unsent text in the ChatGPT composer, because a forced application close could cause that unsent text to be lost.

This project is an unofficial community workaround and is not affiliated with or endorsed by OpenAI.

## Previous versions

### v1.0.0

Original manual GhostChatTool.

It allowed targeted removal by exact `thread_id` with explicit `DELETE` confirmation.

### v3.0.1

Experimental branch that explored automatic refetch/reload approaches.

Those approaches were not reliable enough on the affected Windows build.

**v3.0.1 is retired and is not the recommended release.**

## Recommended version

**GhostChatTool v2.2.0 - Sync & Fix**
```

Poi **Commit changes** con:

```text
Update release notes for GhostChatTool v2.2.0
```
