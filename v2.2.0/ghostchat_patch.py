from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable

APP_NAME = "GhostChat Sync Patch"
VERSION = "2.2.0"

DB_DIR = Path.home() / ".codex" / "sqlite"
DB_PATH = DB_DIR / "codex-dev.db"
BACKUP_DIR = DB_DIR / "ghostchat-backups"
PATCH_DIR = DB_DIR / "ghostchat-patch"
PATCH_LOG = PATCH_DIR / "patch.log"
MANIFEST_DIR = PATCH_DIR / "manifests"

CHATGPT_AUMID = r"OpenAI.Codex_2p2nqsd0c76g0!App"
MAX_LOG_FILE_SIZE = 25 * 1024 * 1024
MAX_TOTAL_LOG_BYTES = 80 * 1024 * 1024
DEFAULT_LOG_DAYS = 7
MAX_BACKUPS = 20

TEXT_SUFFIXES = {".log", ".txt", ".jsonl", ".ndjson", ".json"}


@dataclass
class CatalogRow:
    host_id: str
    thread_id: str
    display_title: str
    missing_candidate: int
    source_recency_at: float


@dataclass
class Evidence:
    thread_id: str
    path: str
    reason: str
    excerpt: str


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def write_patch_log(message: str) -> None:
    PATCH_DIR.mkdir(parents=True, exist_ok=True)
    with PATCH_LOG.open("a", encoding="utf-8", errors="replace") as fh:
        fh.write(f"{datetime.now().isoformat(timespec='seconds')} {message}\n")


def chatgpt_running() -> bool:
    if os.name != "nt":
        return False
    try:
        proc = subprocess.run(
            ["tasklist", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            errors="ignore",
            timeout=5,
        )
        return '"chatgpt.exe"' in (proc.stdout or "").lower()
    except Exception:
        return False


def ensure_database_exists() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"ChatGPT local catalog not found: {DB_PATH}")


def table_exists(con: sqlite3.Connection, table: str) -> bool:
    row = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    return row is not None


def column_names(con: sqlite3.Connection, table: str) -> set[str]:
    return {str(row[1]) for row in con.execute(f"PRAGMA table_info({table})")}


def fetch_cloud_catalog(con: sqlite3.Connection) -> list[CatalogRow]:
    cols = column_names(con, "local_thread_catalog")
    project_clause = "AND project_id IS NULL" if "project_id" in cols else ""
    host_expr = "host_id" if "host_id" in cols else "'chatgpt'"
    missing_expr = "COALESCE(missing_candidate,0)" if "missing_candidate" in cols else "0"
    recency_expr = "COALESCE(source_recency_at,0)" if "source_recency_at" in cols else "0"

    sql = f"""
        SELECT {host_expr}, thread_id, display_title, {missing_expr}, {recency_expr}
        FROM local_thread_catalog
        WHERE source_kind='chatgpt'
          {project_clause}
        ORDER BY {recency_expr} DESC
    """
    return [CatalogRow(*row) for row in con.execute(sql).fetchall()]


def create_backup() -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = now_stamp()
    backup_db = BACKUP_DIR / f"codex-dev-{stamp}.db"

    src = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    dst = sqlite3.connect(backup_db)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()

    for suffix in ("-wal", "-shm"):
        sidecar = Path(str(DB_PATH) + suffix)
        if sidecar.exists():
            shutil.copy2(sidecar, BACKUP_DIR / f"{backup_db.name}{suffix}")

    return backup_db




def prune_backups(max_count: int = MAX_BACKUPS) -> int:
    """Keep backup growth bounded. Returns number of backup sets removed."""
    if not BACKUP_DIR.exists():
        return 0
    dbs = sorted(
        BACKUP_DIR.glob("codex-dev-*.db"),
        key=lambda p: p.stat().st_mtime if p.exists() else 0,
        reverse=True,
    )
    removed = 0
    for db in dbs[max_count:]:
        try:
            db.unlink(missing_ok=True)
            for suffix in ("-wal", "-shm"):
                Path(str(db) + suffix).unlink(missing_ok=True)
            removed += 1
        except OSError:
            pass
    return removed

def create_pre_restore_backup() -> Path:
    return create_backup()


def restore_backup(backup_db: Path) -> None:
    if chatgpt_running():
        raise RuntimeError("ChatGPT is running. Close it before restoring a backup.")
    if not backup_db.exists():
        raise FileNotFoundError(str(backup_db))

    current_backup = create_pre_restore_backup()
    write_patch_log(f"pre-restore backup={current_backup}")

    # ChatGPT is closed here. Remove stale WAL/SHM sidecars so they cannot replay
    # pages from the pre-restore database over the restored snapshot.
    for suffix in ("-wal", "-shm"):
        try:
            Path(str(DB_PATH) + suffix).unlink(missing_ok=True)
        except OSError:
            pass

    src = sqlite3.connect(f"file:{backup_db}?mode=ro", uri=True)
    dst = sqlite3.connect(DB_PATH)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()

    con = sqlite3.connect(DB_PATH)
    try:
        integrity = con.execute("PRAGMA integrity_check").fetchone()
    finally:
        con.close()
    if not integrity or integrity[0] != "ok":
        raise RuntimeError(f"Integrity check after restore returned: {integrity}")


def latest_backup() -> Path | None:
    if not BACKUP_DIR.exists():
        return None
    backups = sorted(BACKUP_DIR.glob("codex-dev-*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
    return backups[0] if backups else None


def _add_existing_dir(out: list[Path], value: Path | None) -> None:
    if value and value.exists() and value.is_dir() and value not in out:
        out.append(value)


def discover_log_roots(extra_roots: list[str] | None = None) -> list[Path]:
    roots: list[Path] = []
    home = Path.home()
    local = Path(os.environ.get("LOCALAPPDATA", "")) if os.environ.get("LOCALAPPDATA") else None
    roaming = Path(os.environ.get("APPDATA", "")) if os.environ.get("APPDATA") else None

    _add_existing_dir(roots, home / ".codex" / "logs")
    _add_existing_dir(roots, home / ".codex" / "log")

    if local:
        for rel in (
            Path("OpenAI") / "ChatGPT" / "logs",
            Path("ChatGPT") / "logs",
            Path("OpenAI") / "Codex" / "logs",
        ):
            _add_existing_dir(roots, local / rel)

        packages = local / "Packages"
        if packages.exists():
            try:
                package_dirs = list(packages.glob("OpenAI.Codex_*")) + list(packages.glob("OpenAI.ChatGPT*"))
            except OSError:
                package_dirs = []
            for pkg in package_dirs:
                for rel in (
                    Path("LocalState") / "logs",
                    Path("LocalState") / "Logs",
                    Path("LocalCache") / "Roaming" / "ChatGPT" / "logs",
                    Path("LocalCache") / "Local" / "ChatGPT" / "logs",
                    Path("LocalCache") / "Roaming" / "Codex" / "logs",
                    Path("LocalCache") / "Local" / "Codex" / "logs",
                ):
                    _add_existing_dir(roots, pkg / rel)

    if roaming:
        for rel in (
            Path("ChatGPT") / "logs",
            Path("OpenAI") / "ChatGPT" / "logs",
            Path("Codex") / "logs",
        ):
            _add_existing_dir(roots, roaming / rel)

    for raw in extra_roots or []:
        try:
            _add_existing_dir(roots, Path(raw).expanduser())
        except Exception:
            pass

    return roots


def recent_log_files(roots: Iterable[Path], days: int) -> list[Path]:
    cutoff = datetime.now() - timedelta(days=max(1, days))
    candidates: list[Path] = []
    for root in roots:
        try:
            for path in root.rglob("*"):
                try:
                    if not path.is_file():
                        continue
                    if path.suffix.lower() not in TEXT_SUFFIXES:
                        continue
                    stat = path.stat()
                    if stat.st_size <= 0 or stat.st_size > MAX_LOG_FILE_SIZE:
                        continue
                    if datetime.fromtimestamp(stat.st_mtime) < cutoff:
                        continue
                    candidates.append(path)
                except OSError:
                    continue
        except OSError:
            continue

    candidates.sort(key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)

    chosen: list[Path] = []
    total = 0
    for path in candidates:
        try:
            size = path.stat().st_size
        except OSError:
            continue
        if total + size > MAX_TOTAL_LOG_BYTES:
            break
        chosen.append(path)
        total += size
    return chosen


def compact_excerpt(text: str, max_len: int = 360) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def find_deleted_evidence(rows: list[CatalogRow], files: list[Path]) -> dict[str, Evidence]:
    """Find only strong local evidence for a deleted cloud conversation.

    For plain-text logs we require the exact catalog thread_id and an explicit
    conversation_deleted marker in the SAME log line. This intentionally favors
    false negatives over associating two adjacent but unrelated log events.

    We deliberately do not treat missing_candidate=1, conversation_not_loaded,
    or a generic 404 as proof.
    """
    wanted = {r.thread_id: r for r in rows}
    if not wanted:
        return {}

    evidence: dict[str, Evidence] = {}

    for path in files:
        if len(evidence) == len(wanted):
            break
        try:
            with path.open("r", encoding="utf-8", errors="replace") as fh:
                for raw_line in fh:
                    line = raw_line.strip()
                    low = line.lower()
                    if "conversation_deleted" not in low and "conversation deleted" not in low:
                        continue
                    for thread_id in wanted:
                        if thread_id in evidence:
                            continue
                        if thread_id in line:
                            evidence[thread_id] = Evidence(
                                thread_id=thread_id,
                                path=str(path),
                                reason="exact thread_id and backend conversation_deleted occur in the same log event line",
                                excerpt=compact_excerpt(line),
                            )
        except (OSError, UnicodeError):
            continue
    return evidence


def bump_catalog_revision(con: sqlite3.Connection) -> bool:
    if not table_exists(con, "local_thread_catalog_metadata"):
        return False
    cols = column_names(con, "local_thread_catalog_metadata")
    if "catalog_revision" not in cols:
        return False
    cur = con.execute(
        "UPDATE local_thread_catalog_metadata "
        "SET catalog_revision = COALESCE(catalog_revision,0) + 1"
    )
    return cur.rowcount > 0


def delete_confirmed(con: sqlite3.Connection, ids: list[str]) -> tuple[int, bool]:
    if not ids:
        return 0, False

    cols = column_names(con, "local_thread_catalog")
    project_clause = "AND project_id IS NULL" if "project_id" in cols else ""

    con.execute("BEGIN IMMEDIATE")
    total = 0
    try:
        for thread_id in ids:
            cur = con.execute(
                f"""
                DELETE FROM local_thread_catalog
                WHERE source_kind='chatgpt'
                  {project_clause}
                  AND thread_id=?
                """,
                (thread_id,),
            )
            if cur.rowcount != 1:
                raise RuntimeError(
                    f"Safety stop: expected exactly 1 row for {thread_id}; got {cur.rowcount}"
                )
            total += 1
        bumped = bump_catalog_revision(con)
        con.commit()
        return total, bumped
    except Exception:
        con.rollback()
        raise


def save_manifest(backup: Path, rows: list[CatalogRow], evidence: dict[str, Evidence]) -> Path:
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    path = MANIFEST_DIR / f"repair-{now_stamp()}.json"
    payload = {
        "version": VERSION,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "database": str(DB_PATH),
        "backup": str(backup),
        "removed": [
            {
                "catalog": asdict(row),
                "evidence": asdict(evidence[row.thread_id]),
            }
            for row in rows
        ],
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path




def scan_confirmed_ghosts(
    *,
    log_days: int = DEFAULT_LOG_DAYS,
    extra_log_roots: list[str] | None = None,
) -> tuple[list[CatalogRow], dict[str, Evidence], int]:
    """Return catalog rows with strong deletion evidence plus evidence map and log count."""
    ensure_database_exists()
    ro = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, timeout=3)
    try:
        if not table_exists(ro, "local_thread_catalog"):
            raise RuntimeError("local_thread_catalog is missing; app schema changed")
        rows = fetch_cloud_catalog(ro)
    finally:
        ro.close()

    roots = discover_log_roots(extra_log_roots or [])
    log_files = recent_log_files(roots, log_days)
    evidence = find_deleted_evidence(rows, log_files)
    confirmed_rows = [r for r in rows if r.thread_id in evidence]
    return confirmed_rows, evidence, len(log_files)


def repair_rows(
    confirmed_rows: list[CatalogRow],
    evidence: dict[str, Evidence],
    *,
    allow_running: bool = False,
    lock_retries: int = 8,
    retry_delay: float = 0.75,
) -> tuple[int, Path, Path, bool]:
    """Safely remove exact confirmed IDs. Supports hot repair with bounded SQLite retries."""
    if not confirmed_rows:
        raise ValueError("No confirmed rows supplied")
    if chatgpt_running() and not allow_running:
        raise RuntimeError("ChatGPT is running. Hot repair is disabled for this operation.")

    backup = create_backup()
    ids = [r.thread_id for r in confirmed_rows]
    last_exc: Exception | None = None
    count = 0
    bumped = False

    for attempt in range(max(1, lock_retries)):
        con = None
        try:
            con = sqlite3.connect(DB_PATH, timeout=1.5)
            count, bumped = delete_confirmed(con, ids)
            integrity = con.execute("PRAGMA integrity_check").fetchone()
            if not integrity or integrity[0] != "ok":
                raise RuntimeError(f"PRAGMA integrity_check returned {integrity}")
            last_exc = None
            break
        except sqlite3.OperationalError as exc:
            last_exc = exc
            text = str(exc).lower()
            if "locked" not in text and "busy" not in text:
                raise
            if attempt + 1 < max(1, lock_retries):
                import time
                time.sleep(max(0.1, retry_delay))
        finally:
            if con is not None:
                con.close()

    if last_exc is not None:
        raise RuntimeError(f"Database stayed busy during hot repair: {last_exc}")

    manifest = save_manifest(backup, confirmed_rows, evidence)
    prune_backups()
    return count, backup, manifest, bumped


def repair_once(
    *,
    allow_running: bool = False,
    log_days: int = DEFAULT_LOG_DAYS,
    extra_log_roots: list[str] | None = None,
    dry_run: bool = False,
) -> dict:
    """Programmatic API used by the background watcher."""
    confirmed_rows, evidence, log_count = scan_confirmed_ghosts(
        log_days=log_days, extra_log_roots=extra_log_roots
    )
    result = {
        "confirmed": confirmed_rows,
        "evidence": evidence,
        "log_count": log_count,
        "removed": 0,
        "backup": None,
        "manifest": None,
        "revision_bumped": False,
    }
    if confirmed_rows and not dry_run:
        count, backup, manifest, bumped = repair_rows(
            confirmed_rows, evidence, allow_running=allow_running
        )
        result.update(
            removed=count,
            backup=backup,
            manifest=manifest,
            revision_bumped=bumped,
        )
    return result


def launch_chatgpt() -> bool:
    if os.name != "nt":
        print("Not running on Windows; ChatGPT launch skipped.")
        return False

    # The current Microsoft Store app is exposed through this AUMID. If it changes,
    # fall back to a Start-menu lookup instead of touching WindowsApps directly.
    try:
        subprocess.Popen(
            ["explorer.exe", f"shell:AppsFolder\\{CHATGPT_AUMID}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception:
        pass

    try:
        ps = (
            "$app=Get-StartApps | Where-Object {$_.Name -like '*ChatGPT*'} | Select-Object -First 1;"
            "if($app){Start-Process ('shell:AppsFolder\\'+$app.AppID); exit 0}else{exit 1}"
        )
        rc = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            timeout=10,
        ).returncode
        return rc == 0
    except Exception:
        return False


def print_rows(title: str, rows: list[CatalogRow]) -> None:
    if not rows:
        return
    print(title)
    for row in rows:
        marker = " missing_candidate=1" if row.missing_candidate else ""
        print(f"  - {row.display_title or '(untitled)'}")
        print(f"    {row.thread_id}{marker}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Conservative launcher/repair patch for stale ChatGPT Desktop Recents. "
            "It only auto-removes cloud rows when recent local logs contain the exact "
            "thread_id next to explicit conversation_deleted backend evidence."
        )
    )
    p.add_argument("--version", action="version", version=f"{APP_NAME} {VERSION}")
    p.add_argument("--dry-run", action="store_true", help="scan and report; do not change the DB")
    p.add_argument("--no-launch", action="store_true", help="do not launch ChatGPT after the scan")
    p.add_argument("--audit", action="store_true", help="show suspected missing_candidate rows too")
    p.add_argument("--log-days", type=int, default=DEFAULT_LOG_DAYS, help="days of recent logs to scan")
    p.add_argument("--log-root", action="append", default=[], help="additional log directory to scan")
    p.add_argument("--restore-latest", action="store_true", help="restore the newest GhostChat backup")
    p.add_argument("--allow-running", action="store_true", help="allow a conservative hot repair while ChatGPT is open")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    print(f"{APP_NAME} v{VERSION}")
    print("Safe pre-launch cleanup for stale ChatGPT Desktop Recents")
    print()

    if args.restore_latest:
        backup = latest_backup()
        if not backup:
            print("No GhostChat backup was found.")
            return 2
        print(f"Restoring: {backup}")
        try:
            restore_backup(backup)
        except Exception as exc:
            print(f"Restore failed: {exc}")
            return 3
        print("Restore complete. Database integrity: ok")
        return 0

    if chatgpt_running() and not args.allow_running:
        print("ChatGPT is already running, so the database will NOT be modified.")
        print("Use --allow-running only for the experimental conservative hot-repair mode.")
        write_patch_log("skip repair: ChatGPT already running")
        if not args.no_launch:
            launch_chatgpt()
        return 0

    try:
        ensure_database_exists()
        ro = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, timeout=3)
        try:
            if not table_exists(ro, "local_thread_catalog"):
                raise RuntimeError("local_thread_catalog is missing; app schema changed")
            rows = fetch_cloud_catalog(ro)
        finally:
            ro.close()
    except Exception as exc:
        print(f"Catalog scan unavailable: {exc}")
        write_patch_log(f"scan failed: {exc}")
        if not args.no_launch:
            launch_chatgpt()
        return 4

    roots = discover_log_roots(args.log_root)
    log_files = recent_log_files(roots, args.log_days)
    evidence = find_deleted_evidence(rows, log_files)
    confirmed_rows = [r for r in rows if r.thread_id in evidence]
    suspects = [r for r in rows if r.missing_candidate and r.thread_id not in evidence]

    print(f"Cloud Recents indexed locally: {len(rows)}")
    print(f"Recent log files scanned:      {len(log_files)}")
    print(f"Confirmed deleted ghosts:      {len(confirmed_rows)}")

    if confirmed_rows:
        print()
        print_rows("High-confidence ghost entries:", confirmed_rows)

    if args.audit and suspects:
        print()
        print_rows(
            "Suspects left untouched (missing_candidate alone is NOT treated as proof):",
            suspects,
        )

    if confirmed_rows and not args.dry_run:
        try:
            count, backup, manifest, bumped = repair_rows(
                confirmed_rows, evidence, allow_running=args.allow_running
            )
            print()
            print(f"Removed: {count}")
            print(f"Backup:  {backup}")
            print(f"Manifest:{manifest}")
            print(f"Catalog revision bumped: {'yes' if bumped else 'not available'}")
            print("Database integrity: ok")
            write_patch_log(
                f"repair success removed={count} backup={backup} manifest={manifest} revision_bumped={bumped}"
            )
        except Exception as exc:
            print(f"Repair failed: {exc}")
            write_patch_log(f"repair failed: {exc}")
            print("ChatGPT will still be launched without further database changes.")
    elif confirmed_rows and args.dry_run:
        print("\nDry run: nothing was changed.")
        write_patch_log(f"dry-run confirmed={len(confirmed_rows)}")
    else:
        print("No high-confidence ghost entry found; database left untouched.")
        write_patch_log(f"scan complete rows={len(rows)} logs={len(log_files)} confirmed=0")

    if not args.no_launch:
        print()
        print("Launching ChatGPT...")
        if not launch_chatgpt():
            print("Could not launch ChatGPT automatically. Open it from Start as usual.")
            return 5
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nCancelled.")
        raise SystemExit(130)
