# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| 2.2.x | Yes |
| 1.0.x | Legacy |
| 3.0.x | No - experimental / retired |

GhostChatTool v2.2.x is the currently recommended release.

v1.0.x remains available as the original manual fallback tool.

v3.0.x was an experimental branch and is not recommended for normal use.

## Reporting a security problem

If you discover a bug that could:

- delete the wrong local conversation entry;
- modify unrelated ChatGPT/Codex state;
- affect Project conversations;
- expose local conversation data;
- overwrite or corrupt the SQLite database;
- restore an incorrect backup;
- execute unintended commands;
- access authentication data or credentials;

please avoid encouraging other users to reproduce it on their real ChatGPT database.

Open a GitHub issue with:

- the GhostChatTool version;
- Windows version;
- Python version;
- ChatGPT Desktop version if known;
- a clear description of the problem;
- steps to reproduce when safe;
- sanitized logs or output.

Remove personal conversation titles, thread IDs, usernames, paths, and other private information before posting logs publicly.

## Sensitive files

Do **not** upload or publish:

- `codex-dev.db`;
- SQLite backups;
- `auth.json`;
- cookies;
- authentication tokens;
- session data;
- private conversation contents;
- unsanitized repair logs or manifests.

## Repair safety

Automatic repair in v2.2.x requires strong local deletion evidence.

The intended condition is:

```text
exact thread_id
+
explicit conversation_deleted event
```

The following alone must not be treated as sufficient proof of deletion:

```text
missing_candidate = 1
conversation_not_loaded
generic 404
Unable to load conversation
stale conversation title
```

Project conversations must remain excluded.

## Local data

GhostChatTool is designed to operate on the user's local ChatGPT/Codex SQLite catalog and its own local backup, manifest, and log files.

The tool does not intentionally:

- read `auth.json`;
- extract cookies or authentication tokens;
- call private ChatGPT account APIs;
- upload conversation data;
- modify `ChatGPT.exe`;
- inject code or DLLs into ChatGPT;
- send ChatGPT messages.

The Sync & Fix workflow may close and relaunch the official ChatGPT Windows application, but GhostChatTool does not replace or modify the application executable.

## Backups

GhostChatTool creates SQLite backups before confirmed repairs.

Backups are typically stored under:

```text
%USERPROFILE%\.codex\sqlite\ghostchat-backups
```

A restored backup may revert unrelated local ChatGPT state created after that backup.

Use restore functionality only when necessary.

## Database integrity

After database modifications, GhostChatTool should run:

```sql
PRAGMA integrity_check;
```

The expected result is:

```text
ok
```

If database integrity verification fails, stop using the modified database and restore a known-good backup when appropriate.

## Disclaimer

GhostChatTool is an unofficial community workaround.

It is not affiliated with or endorsed by OpenAI.

The ChatGPT Windows application's storage schema and synchronization behavior may change at any time.
```

Poi fai **Commit changes** con:

```text
Update security policy for GhostChatTool v2.2.0
```
