# Security and safety

GhostChat Sync Fix 2.2.0 is an external local workaround. It does not patch, inject into, or replace the official ChatGPT executable.

The Smart Restart path:

- requests a normal Windows close first;
- asks before any forced close;
- warns that unsent composer text can be lost if a forced close is chosen;
- launches the official installed ChatGPT app through its AppsFolder identity;
- only deletes catalog rows with exact `thread_id` plus explicit `conversation_deleted` evidence;
- excludes Projects;
- creates backups before repair;
- checks SQLite integrity after repair.

It does not read `auth.json`, steal tokens, call private account APIs, or send chat messages.
