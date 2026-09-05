## [2.2.0] - 2026-09-05

### Added

- Smart Restart / Sync & Fix workflow.
- Conservative background watcher.
- Automatic SQLite backup before confirmed repairs.
- Automatic relaunch of the official ChatGPT Windows app after Sync & Fix.
- Post-launch reconciliation window.
- Repair logs and manifests.
- Restore support.

### Safety

- Project chats remain excluded.
- Automatic removal requires an exact `thread_id` together with explicit `conversation_deleted` evidence.
- `missing_candidate=1` alone is never considered sufficient proof of deletion.
- `PRAGMA integrity_check` is executed after database changes.
- No access to `auth.json`, account tokens, or browser cookies.
- No private ChatGPT account APIs.
- No modification or code injection into `ChatGPT.exe`.

### Notes

- v2.2.0 is the recommended release.
- v3.0.1 was an experimental branch and is not recommended for normal use.
