# Changelog

## 2.2.0

- Added one-click **Smart Restart** workflow.
- Added desktop shortcut `ChatGPT - Sync & Fix`.
- Requests a graceful ChatGPT close first.
- Requires explicit user confirmation before forced termination if graceful close times out.
- Performs conservative reconcile before close, while closed, and briefly after relaunch.
- Does not send messages or call private ChatGPT APIs.
- Keeps strong-evidence-only deletion, backups, Project exclusion, and SQLite integrity checks.
- Keeps v2.1 nudge tools for diagnostics only; they are no longer presented as the primary fix.
