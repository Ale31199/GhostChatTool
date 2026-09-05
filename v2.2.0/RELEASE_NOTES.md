# GhostChat Sync Fix 2.2.0

This release changes strategy after real-device testing showed that remote deletions may not be exposed to the Desktop client until a strong sync occurs. Sending a Desktop message or restarting ChatGPT caused the stale deletion to reconcile; passive activation/search nudges did not reliably do so.

v2.2 adds `ChatGPT - Sync & Fix`, a one-click controlled restart followed by the existing conservative repair logic. It does not modify ChatGPT.exe, inject code, send messages, or trust `missing_candidate` by itself.
