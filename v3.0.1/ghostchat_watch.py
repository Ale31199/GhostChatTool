from __future__ import annotations

import argparse
import ctypes
import json
import os
import signal
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import ghostchat_patch as patch
import ghostchat_nudge as nudge
import ghostchat_refetch_bridge as refetch_bridge

APP_NAME = "GhostChat Background Watcher"
VERSION = "3.0.1"
POLL_SECONDS = 3.0
RESCAN_LOGS_SECONDS = 15.0
DEFAULT_NUDGE_SECONDS = 8.0
REFETCH_RELOAD_COOLDOWN_SECONDS = 20.0
STATUS_DIR = patch.PATCH_DIR
STATUS_FILE = STATUS_DIR / "watcher-status.json"
WATCH_LOG = STATUS_DIR / "watcher.log"
STOP_FILE = STATUS_DIR / "watcher.stop"
MUTEX_NAME = r"Local\GhostChatSyncFixWatcher"


def log(message: str) -> None:
    STATUS_DIR.mkdir(parents=True, exist_ok=True)
    line = f"{datetime.now().isoformat(timespec='seconds')} {message}"
    with WATCH_LOG.open("a", encoding="utf-8", errors="replace") as fh:
        fh.write(line + "\n")
    write_status(last_message=message)


def write_status(**updates) -> None:
    STATUS_DIR.mkdir(parents=True, exist_ok=True)
    state = {
        "version": VERSION,
        "pid": os.getpid(),
        "running": True,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }
    if STATUS_FILE.exists():
        try:
            state.update(json.loads(STATUS_FILE.read_text(encoding="utf-8")))
        except Exception:
            pass
    state.update(updates)
    # Always stamp the running binary version after loading an older status file.
    state["version"] = VERSION
    state["pid"] = os.getpid()
    state["running"] = True
    state["updated_at"] = datetime.now().isoformat(timespec="seconds")
    tmp = STATUS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(STATUS_FILE)


def mark_stopped(reason: str) -> None:
    STATUS_DIR.mkdir(parents=True, exist_ok=True)
    state = {}
    if STATUS_FILE.exists():
        try:
            state = json.loads(STATUS_FILE.read_text(encoding="utf-8"))
        except Exception:
            state = {}
    state.update(
        {
            "version": VERSION,
            "pid": os.getpid(),
            "running": False,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "last_message": reason,
        }
    )
    STATUS_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def acquire_single_instance():
    if os.name != "nt":
        return None
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.CreateMutexW(None, False, MUTEX_NAME)
    if not handle:
        raise RuntimeError("Could not create watcher mutex")
    ERROR_ALREADY_EXISTS = 183
    if kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
        kernel32.CloseHandle(handle)
        return False
    return handle


def release_single_instance(handle) -> None:
    if os.name == "nt" and handle not in (None, False):
        try:
            ctypes.windll.kernel32.ReleaseMutex(handle)
        except Exception:
            pass
        try:
            ctypes.windll.kernel32.CloseHandle(handle)
        except Exception:
            pass


def load_catalog() -> dict[str, patch.CatalogRow]:
    if not patch.DB_PATH.exists():
        return {}
    con = sqlite3.connect(f"file:{patch.DB_PATH}?mode=ro", uri=True, timeout=1.5)
    try:
        if not patch.table_exists(con, "local_thread_catalog"):
            return {}
        return {r.thread_id: r for r in patch.fetch_cloud_catalog(con)}
    finally:
        con.close()


def discover_files() -> list[Path]:
    roots = patch.discover_log_roots([])
    return patch.recent_log_files(roots, patch.DEFAULT_LOG_DAYS)


def read_new_lines(path: Path, offsets: dict[str, int]) -> list[str]:
    key = str(path)
    try:
        size = path.stat().st_size
    except OSError:
        return []

    pos = offsets.get(key)
    if pos is None:
        # A file discovered after startup may already contain a fresh delete event
        # (for example after log rotation), so read it from the beginning. Startup
        # files are explicitly seeded to EOF by watcher_loop.
        pos = 0
    if size < pos:
        pos = 0

    if size == pos:
        return []

    lines: list[str] = []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            fh.seek(pos)
            lines = fh.readlines()
            offsets[key] = fh.tell()
    except OSError:
        return []
    return lines


def evidence_from_lines(
    rows: dict[str, patch.CatalogRow],
    path: Path,
    lines: list[str],
) -> dict[str, patch.Evidence]:
    evidence: dict[str, patch.Evidence] = {}
    if not rows:
        return evidence
    for raw in lines:
        line = raw.strip()
        low = line.lower()
        if "conversation_deleted" not in low and "conversation deleted" not in low:
            continue
        for thread_id in rows:
            if thread_id in line:
                evidence[thread_id] = patch.Evidence(
                    thread_id=thread_id,
                    path=str(path),
                    reason="watcher saw exact thread_id and conversation_deleted in the same new log event",
                    excerpt=patch.compact_excerpt(line),
                )
    return evidence


def repair_detected(
    rows: dict[str, patch.CatalogRow],
    evidence: dict[str, patch.Evidence],
    *,
    hot: bool,
) -> int:
    confirmed = [rows[tid] for tid in evidence if tid in rows]
    if not confirmed:
        return 0
    titles = ", ".join((r.display_title or "(untitled)") for r in confirmed)
    log(f"confirmed ghost(s): {len(confirmed)} [{titles}]")
    try:
        count, backup, manifest, bumped = patch.repair_rows(
            confirmed,
            evidence,
            allow_running=hot,
            lock_retries=10,
            retry_delay=0.7,
        )
    except Exception as exc:
        log(f"repair deferred/failed safely: {exc}")
        return 0
    log(
        f"repair success removed={count} revision_bumped={bumped} "
        f"backup={backup.name} manifest={manifest.name}"
    )
    write_status(
        last_repair_at=datetime.now().isoformat(timespec="seconds"),
        last_repair_count=count,
        last_repair_titles=[r.display_title for r in confirmed],
        last_backup=str(backup),
        last_manifest=str(manifest),
    )
    return count


def initial_reconcile(*, hot: bool) -> int:
    try:
        result = patch.repair_once(allow_running=hot, dry_run=False)
    except Exception as exc:
        log(f"initial reconcile skipped safely: {exc}")
        return 0
    count = int(result.get("removed") or 0)
    if count:
        rows = result["confirmed"]
        write_status(
            last_repair_at=datetime.now().isoformat(timespec="seconds"),
            last_repair_count=count,
            last_repair_titles=[r.display_title for r in rows],
            last_backup=str(result.get("backup")),
            last_manifest=str(result.get("manifest")),
        )
        log(f"initial reconcile repaired {count} confirmed ghost(s)")
    else:
        log("initial reconcile: no confirmed ghost")
    return count


def watcher_loop(*, hot: bool, poll_seconds: float, sync_nudge: bool, nudge_seconds: float, refetch_bridge_enabled: bool) -> int:
    STATUS_DIR.mkdir(parents=True, exist_ok=True)
    STOP_FILE.unlink(missing_ok=True)
    write_status(
        started_at=datetime.now().isoformat(timespec="seconds"),
        mode="hot" if hot else "closed-only",
        sync_nudge_enabled=sync_nudge,
        sync_nudge_mode="foreground-activation" if sync_nudge else "off",
        nudge_interval_seconds=nudge_seconds if sync_nudge else None,
        refetch_bridge_enabled=refetch_bridge_enabled,
        refetch_bridge_strategy="native-menu-reload" if refetch_bridge_enabled else "off",
    )
    log(f"watcher started mode={'hot' if hot else 'closed-only'} poll={poll_seconds:.1f}s")

    # Snapshot current log sizes BEFORE the full startup reconciliation. If a delete
    # event is appended while that scan is running, the later tail starts from the
    # old size and cannot miss the event.
    files = discover_files()
    offsets: dict[str, int] = {}
    for f in files:
        try:
            offsets[str(f)] = f.stat().st_size
        except OSError:
            pass

    # Full startup reconciliation catches ghosts that existed before the watcher started.
    initial_reconcile(hot=hot)

    # Keep confirmed backend deletion evidence in memory. If ChatGPT keeps/recreates
    # the stale local row, the watcher can safely retry later without needing a new
    # delete event. Thread IDs are unique and evidence requires an explicit backend marker.
    evidence_cache: dict[str, patch.Evidence] = {}
    last_attempt: dict[str, float] = {}

    last_rescan = time.monotonic()
    last_heartbeat = 0.0
    last_nudge = 0.0
    nudge_count = 0
    last_nudge_detail = "not_started"
    last_refetch_reload = 0.0
    refetch_event_count = 0
    refetch_reload_attempts = 0
    refetch_reload_successes = 0

    while True:
        if STOP_FILE.exists():
            STOP_FILE.unlink(missing_ok=True)
            log("stop requested")
            return 0

        now = time.monotonic()

        # v2.1 experimental sync nudge. We only request a normal Windows app
        # activation while ChatGPT is ALREADY the foreground app, so this never
        # steals focus from another program. No keys/messages/auth data are used.
        # The goal is to exercise the app lifecycle/refetch path before scanning
        # for the explicit conversation_deleted event.
        if sync_nudge and now - last_nudge >= nudge_seconds:
            result = nudge.reactivate_chatgpt_if_foreground()
            if result.attempted:
                last_nudge = now
                nudge_count += 1
                last_nudge_detail = result.detail
                write_status(
                    last_nudge_at=datetime.now().isoformat(timespec="seconds"),
                    last_nudge_ok=result.ok,
                    last_nudge_mode=result.mode,
                    last_nudge_detail=result.detail,
                    nudge_count=nudge_count,
                )
                if not result.ok:
                    log(f"sync nudge failed safely: {result.detail}")

        if now - last_rescan >= RESCAN_LOGS_SECONDS:
            files = discover_files()
            last_rescan = now

        try:
            rows = load_catalog()
        except Exception as exc:
            if now - last_heartbeat >= 30:
                log(f"catalog read temporarily unavailable: {exc}")
                last_heartbeat = now
            time.sleep(poll_seconds)
            continue

        for path in files:
            lines = read_new_lines(path, offsets)
            if lines:
                # v3 early-sync bridge: conversation_not_loaded/refetch is NOT
                # deletion proof. It only asks ChatGPT to perform a benign native
                # Reload Window if this build exposes that command. The existing
                # conversation_deleted evidence gate remains mandatory for DELETE.
                if refetch_bridge_enabled:
                    for raw in lines:
                        if not refetch_bridge.is_refetch_ignored_event(raw):
                            continue
                        refetch_event_count += 1
                        event_excerpt = refetch_bridge.compact_event(raw)
                        write_status(
                            last_refetch_event_at=datetime.now().isoformat(timespec="seconds"),
                            last_refetch_event=event_excerpt,
                            refetch_event_count=refetch_event_count,
                        )
                        if now - last_refetch_reload >= REFETCH_RELOAD_COOLDOWN_SECONDS:
                            result = refetch_bridge.attempt_reload_window()
                            refetch_reload_attempts += 1
                            if result.ok:
                                last_refetch_reload = now
                                refetch_reload_successes += 1
                                log(
                                    "early refetch bridge: Reload Window requested "
                                    f"strategy={result.strategy} command={result.command_text!r} id={result.command_id}"
                                )
                            else:
                                # Fail closed. Do not fall back to simulated typing or
                                # message sending; those could interfere with the user.
                                log(f"early refetch bridge unavailable safely: {result.detail}")
                            write_status(
                                last_refetch_reload_at=datetime.now().isoformat(timespec="seconds"),
                                last_refetch_reload_ok=result.ok,
                                last_refetch_reload_strategy=result.strategy,
                                last_refetch_reload_detail=result.detail,
                                refetch_reload_attempts=refetch_reload_attempts,
                                refetch_reload_successes=refetch_reload_successes,
                            )
                evidence_cache.update(evidence_from_lines(rows, path, lines))

        # Any cached explicit delete evidence that still has a local catalog row is
        # eligible for repair. A short cooldown avoids write thrashing if ChatGPT is
        # concurrently holding/recreating its catalog entry.
        eligible: dict[str, patch.Evidence] = {}
        for tid, ev in evidence_cache.items():
            if tid not in rows:
                continue
            if now - last_attempt.get(tid, 0.0) < 12.0:
                continue
            eligible[tid] = ev

        if eligible:
            running = patch.chatgpt_running()
            if running and not hot:
                # Keep evidence cached; it will be retried when ChatGPT closes.
                if now - max((last_attempt.get(tid, 0.0) for tid in eligible), default=0.0) >= 30:
                    log(f"confirmed ghost pending until ChatGPT closes: {len(eligible)}")
                for tid in eligible:
                    last_attempt[tid] = now
            else:
                for tid in eligible:
                    last_attempt[tid] = now
                removed = repair_detected(rows, eligible, hot=hot)
                if removed:
                    # Keep evidence cached deliberately. If the running app writes the
                    # stale row back later, the same confirmed delete can be repaired again.
                    pass

        # Heartbeat lets status.cmd distinguish a live watcher from a stale status file.
        if now - last_heartbeat >= 30:
            write_status(
                catalog_rows=len(rows),
                tracked_logs=len(files),
                cached_delete_events=len(evidence_cache),
                heartbeat_at=datetime.now().isoformat(timespec="seconds"),
                sync_nudge_enabled=sync_nudge,
                nudge_count=nudge_count,
                last_nudge_detail=last_nudge_detail,
                refetch_bridge_enabled=refetch_bridge_enabled,
                refetch_event_count=refetch_event_count,
                refetch_reload_attempts=refetch_reload_attempts,
                refetch_reload_successes=refetch_reload_successes,
            )
            last_heartbeat = now

        time.sleep(poll_seconds)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Background sync repair watcher for GhostChatTool")
    p.add_argument("--version", action="version", version=f"{APP_NAME} {VERSION}")
    p.add_argument("--closed-only", action="store_true", help="never edit SQLite while ChatGPT.exe is running")
    p.add_argument("--poll", type=float, default=POLL_SECONDS, help="poll interval in seconds")
    p.add_argument("--once", action="store_true", help="run one reconcile pass and exit")
    p.add_argument("--sync-nudge", action="store_true", help="enable the experimental foreground app-activation nudge (diagnostic only)")
    p.add_argument("--nudge-interval", type=float, default=DEFAULT_NUDGE_SECONDS, help="minimum seconds between foreground activation nudges")
    p.add_argument("--no-refetch-bridge", action="store_true", help="disable v3 early refetch -> native Reload Window bridge")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    handle = acquire_single_instance()
    if handle is False:
        return 0

    def _stop_handler(signum, frame):
        raise KeyboardInterrupt

    try:
        signal.signal(signal.SIGTERM, _stop_handler)
    except Exception:
        pass

    try:
        hot = not args.closed_only
        if args.once:
            initial_reconcile(hot=hot)
            return 0
        return watcher_loop(
            hot=hot,
            poll_seconds=max(1.0, args.poll),
            sync_nudge=args.sync_nudge,
            nudge_seconds=max(4.0, args.nudge_interval),
            refetch_bridge_enabled=not args.no_refetch_bridge,
        )
    except KeyboardInterrupt:
        log("watcher stopped")
        return 0
    except Exception as exc:
        log(f"watcher fatal error: {exc}")
        return 1
    finally:
        mark_stopped("watcher stopped")
        release_single_instance(handle)


if __name__ == "__main__":
    raise SystemExit(main())
