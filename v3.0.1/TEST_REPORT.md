# v3.0.1 distribution — verification report

Date: 2026-09-05. Environment: Windows, Python 3.13, Windows PowerShell.

## Passed

- 15 offline regression tests (`py -3 -m unittest -v test_release.py`). Tests use temporary synthetic databases and logs with disposable test identifiers. No production chat database is modified by this test suite.
- Both core and watcher report 3.0.1; all four runtime files match the recovered installed sources byte-for-byte (SHA-256 inventory in `CORE_SHA256.json`).
- Supported-schema filtering excludes Project and non-ChatGPT rows.
- `missing_candidate`, generic 404 and `conversation_not_loaded` do not qualify by themselves; markers and IDs on different lines or unrelated IDs do not qualify.
- Both recognized deletion markers and the watcher's same-line evidence gate work in fixtures.
- Dry-run preserves database bytes and does not create a backup; absent evidence also causes no database change.
- Confirmed targeted removal preserves other fixture rows, creates a pre-change snapshot and manifest, increments the catalog revision and yields `PRAGMA integrity_check = ok`.
- Duplicate matching IDs cause transaction rollback; non-hot repair is refused when the process check reports the app running.
- Snapshot restore returns the fixture row and creates a distinct pre-restore backup in the test.
- The PowerShell management script parses without syntax errors.
- The HTML guide opens with English selected. English, Italian, Spanish, French and German sections render with matching headings; language navigation selects one visible section.

## Packaging checks

The release builder uses an explicit file allowlist and runs a ZIP CRC check. Runtime state, databases, log files, account configuration, credentials, browser profiles, bytecode caches and backup folders are not included. A SHA-256 checksum accompanies the ZIP.

## Not claimed or certified

- No fresh Windows installation/login-startup/uninstallation end-to-end run was performed on a clean machine. The installer and wrappers are new packaging additions, not part of the original runtime.
- No live cross-device deletion was initiated during this packaging task. The actual desktop app UI refresh, server-event delivery and future app builds are not covered by the offline tests.
- Python 3.10–3.12 and all Windows 10/11 configurations were not individually tested; 3.10+ is the source-level requirement.
- The legacy core is not universally fail-closed for arbitrary schema/process-detection failures. It has post-commit integrity checking, not guaranteed automatic rollback. Project filtering depends on schema support. See README before use.

Published as an **experimental pre-release** for these reasons. Keep private backups and test only with disposable conversations. The existing installation was not stopped, replaced or upgraded by this packaging task.
