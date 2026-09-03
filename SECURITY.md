# Security Policy

## Supported version

| Version | Supported |
|---|---|
| 1.0.x | Yes |

## Reporting a problem

If you discover a bug that could:

- delete the wrong local conversation entry;
- modify unrelated ChatGPT/Codex state;
- expose local conversation data;
- overwrite or corrupt the SQLite database;
- execute unintended commands;

please do not encourage other users to reproduce it on their real database.

Open a GitHub issue with:

- the GhostChatTool version;
- Windows version;
- Python version;
- a description of the problem;
- sanitized output with personal chat titles and thread IDs removed.

Do not upload `codex-dev.db`, authentication files, backups, or private conversation data.

## Local data

GhostChatTool does not make network requests. It operates only on the user's local ChatGPT/Codex SQLite catalog and its own local backup directory.
