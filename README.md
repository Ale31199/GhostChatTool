> **Looking for v3.0.1?** [Download the Windows package](https://github.com/Ale31199/GhostChatTool/releases/tag/v3.0.1) or open the [v3.0.1 source and guides](v3.0.1/README.md). English is the default, with Italian, Spanish, French and German guides. This is an experimental, browser-free local-log repair tool; quit and reopen the app yourself if its list stays stale. No qualifying deletion log event means no repair.
>
> **The documentation below and the root-level scripts describe the older v1.0.0 manual tool. Do not mix the two versions.**

# GhostChatTool

A small Windows command-line utility for removing **stale local ChatGPT Recents entries** ("Ghost chats") that remain visible in the ChatGPT Windows desktop app after the underlying conversation has already been deleted.

> [!IMPORTANT]
> GhostChatTool is an **unofficial community workaround**. It is not affiliated with or endorsed by OpenAI. Local app storage may change in future ChatGPT versions.

## What it does

GhostChatTool targets the local ChatGPT/Codex SQLite catalog at:

```text
%USERPROFILE%\.codex\sqlite\codex-dev.db
```

It:

- refuses to continue if `ChatGPT.exe` appears to be running;
- lists recent ChatGPT conversations while excluding Project chats;
- lets you select a conversation by number or exact `thread_id`;
- shows the title and ID before doing anything;
- requires typing `DELETE` as explicit confirmation;
- creates a timestamped SQLite backup automatically;
- deletes **only** the selected `thread_id` from `local_thread_catalog`;
- commits the change;
- verifies the row is gone;
- runs `PRAGMA integrity_check`.

It does **not** delete server-side conversations.

## Requirements

- Windows 10 or Windows 11
- The ChatGPT Windows desktop app using the local `.codex` database layout
- Python available as either `py` or `python`

No third-party Python packages are required.

## Install

1. Download the release ZIP.
2. Extract it.
3. Close ChatGPT completely.
4. Double-click:

```text
install_ghostchat.cmd
```

5. Open a **new** PowerShell or Windows Terminal window.
6. Run:

```powershell
ghostchat
```

## Usage

Interactive cleanup:

```powershell
ghostchat
```

List recent non-Project chats without changing anything:

```powershell
ghostchat --list
```

Show help:

```powershell
ghostchat --help
```

Show version:

```powershell
ghostchat --version
```

Show more than the default 30 chats:

```powershell
ghostchat --limit 60
```

Target a known ID:

```powershell
ghostchat --id 00000000-0000-0000-0000-000000000000
```

The tool still asks for `DELETE` before removal.

## Example

```text
GhostChatTool v1.0.0
Targeted cleanup for Ghost entries stuck in ChatGPT Windows Recents

Recent ChatGPT chats (Projects excluded)

 1. Working conversation
    6a99931b-...

 2. Deleted conversation still stuck in Recents
    6a99bf87-...

Select the Ghost chat NUMBER, or paste its thread_id: 2

Selected local Recents entry
Title:              Deleted conversation still stuck in Recents
thread_id:          6a99bf87-...
missing_candidate:  0

Type DELETE to remove ONLY this local entry: DELETE

Backup created:
C:\Users\...\ .codex\sqlite\ghostchat-backups\codex-dev-YYYYMMDD-HHMMSS.db

SUCCESS
Ghost Recents entry removed.
Database integrity: ok
```

## Safety

Use GhostChatTool only when:

1. the conversation has already been deleted;
2. it no longer exists in a working ChatGPT client/browser;
3. the Windows desktop app still shows it under Recents or errors when opening/deleting it;
4. you have verified the selected title and `thread_id`.

Do **not** use the tool as a general chat deletion utility.

The program intentionally does not delete:

- Project chats;
- Work/Codex sessions;
- `auth.json`;
- `sessions` or `archived_sessions`;
- credentials;
- unrelated app settings;
- every `missing_candidate=1` row automatically.

## Backups

Backups are stored under:

```text
%USERPROFILE%\.codex\sqlite\ghostchat-backups
```

A backup is created **before every confirmed deletion**.

## Uninstall

Run:

```text
uninstall_ghostchat.cmd
```

Then open a new terminal window.

## Why thread_id instead of title?

Different conversations can share the same title. `thread_id` is the safer, targeted identifier for the local catalog entry.

## Troubleshooting

### `ghostchat` is not recognized

Open a **new** terminal after running the installer. The installer adds:

```text
%USERPROFILE%\GhostChatTool
```

to your user PATH.

### `py` / `python` is not recognized

Install Python for Windows and make sure either `py` or `python` is available from PowerShell.

### ChatGPT is still running

Close ChatGPT completely, including any background instance visible in Task Manager, then run `ghostchat` again.

### Database not found

The local database layout may have changed, or your installed ChatGPT build may use a different storage location. Do not delete random files to compensate.

## Privacy

GhostChatTool runs locally. It does not make network requests and does not upload your chats, database, IDs, or backups anywhere.

## License

MIT. See [LICENSE](LICENSE).

## Disclaimer

This project modifies a local database used by a third-party application. Always keep backups. The ChatGPT Windows app may change its local schema at any time, so future versions of this utility may require updates.
