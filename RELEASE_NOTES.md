# GhostChatTool v1.0.0

First public release.

GhostChatTool is a targeted Windows workaround for ChatGPT conversations that have already been deleted but remain stuck as stale entries under **Recents** in the Windows desktop app.

## Highlights

- Automatic local SQLite backup
- Lists recent ChatGPT chats while excluding Projects
- Select by number or exact `thread_id`
- Explicit `DELETE` confirmation
- Deletes only the selected local catalog entry
- SQLite integrity verification
- Refuses to run while ChatGPT appears to be open
- No network requests
- No third-party Python dependencies
- Installer adds a simple `ghostchat` command

## Install

1. Download `GhostChatTool-v1.0.0.zip`.
2. Extract it.
3. Close ChatGPT.
4. Run `install_ghostchat.cmd`.
5. Open a new PowerShell window.
6. Run:

```powershell
ghostchat
```

## Important

This is an unofficial community workaround and is not affiliated with OpenAI. Use it only for conversations you have already deleted and personally verified as Ghost entries.
