from __future__ import annotations

import argparse
import os
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path

APP_NAME = "GhostChatTool"
VERSION = "1.0.0"
DEFAULT_LIMIT = 30

DB_DIR = Path.home() / ".codex" / "sqlite"
DB_PATH = DB_DIR / "codex-dev.db"
BACKUP_DIR = DB_DIR / "ghostchat-backups"


class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    CYAN = "\033[36m"


def enable_ansi() -> None:
    if os.name == "nt":
        try:
            os.system("")
        except Exception:
            pass


def color(text: str, code: str, enabled: bool) -> str:
    return f"{code}{text}{C.RESET}" if enabled else text


def chatgpt_running() -> bool:
    """Best-effort check for the ChatGPT Windows desktop process."""
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
        out = (proc.stdout or "").lower()
        return '"chatgpt.exe"' in out
    except Exception:
        return False


def ensure_database_exists() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"ChatGPT/Codex local database not found:\n{DB_PATH}"
        )


def create_backup() -> Path:
    """Create a consistent SQLite backup and preserve WAL/SHM sidecars if present."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_db = BACKUP_DIR / f"codex-dev-{stamp}.db"

    src = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    dst = sqlite3.connect(backup_db)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()

    for suffix in ("-wal", "-shm"):
        src_sidecar = Path(str(DB_PATH) + suffix)
        if src_sidecar.exists():
            shutil.copy2(
                src_sidecar,
                BACKUP_DIR / f"codex-dev-{stamp}.db{suffix}",
            )

    return backup_db


def fetch_recent(con: sqlite3.Connection, limit: int):
    return con.execute(
        """
        SELECT
            thread_id,
            display_title,
            COALESCE(missing_candidate, 0)
        FROM local_thread_catalog
        WHERE source_kind='chatgpt'
          AND project_id IS NULL
        ORDER BY source_recency_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()


def fetch_by_id(con: sqlite3.Connection, thread_id: str):
    return con.execute(
        """
        SELECT
            thread_id,
            display_title,
            COALESCE(missing_candidate, 0)
        FROM local_thread_catalog
        WHERE source_kind='chatgpt'
          AND project_id IS NULL
          AND thread_id=?
        """,
        (thread_id,),
    ).fetchone()


def print_header(use_color: bool) -> None:
    print(color("=" * 64, C.CYAN, use_color))
    print(color(f" {APP_NAME} v{VERSION}", C.BOLD, use_color))
    print(" Targeted cleanup for Ghost entries stuck in ChatGPT Windows Recents")
    print(color("=" * 64, C.CYAN, use_color))


def print_recent(rows, use_color: bool) -> None:
    print()
    print(color("Recent ChatGPT chats (Projects excluded)", C.BOLD, use_color))
    print()
    for i, (thread_id, title, missing) in enumerate(rows, 1):
        title = title or "(untitled)"
        marker = (
            color("  [missing?]", C.YELLOW, use_color)
            if missing
            else ""
        )
        print(f"{i:>2}. {title}{marker}")
        print(color(f"    {thread_id}", C.DIM, use_color))
    print()


def resolve_selection(
    con: sqlite3.Connection,
    rows,
    selection: str,
):
    selection = selection.strip()

    if selection.isdigit():
        index = int(selection)
        if 1 <= index <= len(rows):
            return rows[index - 1]
        return None

    return fetch_by_id(con, selection)


def delete_thread(
    con: sqlite3.Connection,
    thread_id: str,
) -> tuple[int, list, tuple | None]:
    con.execute("BEGIN IMMEDIATE")
    cur = con.execute(
        """
        DELETE FROM local_thread_catalog
        WHERE source_kind='chatgpt'
          AND project_id IS NULL
          AND thread_id=?
        """,
        (thread_id,),
    )

    if cur.rowcount != 1:
        con.rollback()
        return cur.rowcount, [], None

    con.commit()

    remaining = con.execute(
        """
        SELECT thread_id, display_title
        FROM local_thread_catalog
        WHERE thread_id=?
        """,
        (thread_id,),
    ).fetchall()

    integrity = con.execute("PRAGMA integrity_check").fetchone()
    return cur.rowcount, remaining, integrity


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ghostchat",
        description=(
            "Remove a stale local ChatGPT Windows Recents entry by thread_id. "
            "This tool does not delete server-side conversations."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"{APP_NAME} {VERSION}",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help=f"number of recent non-Project chats to list (default: {DEFAULT_LIMIT})",
    )
    parser.add_argument(
        "--id",
        dest="thread_id",
        help="select a specific thread_id instead of choosing interactively",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="list recent non-Project chats and exit without deleting anything",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="disable ANSI terminal colors",
    )
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    enable_ansi()
    use_color = sys.stdout.isatty() and not args.no_color

    print_header(use_color)

    try:
        ensure_database_exists()
    except FileNotFoundError as exc:
        print()
        print(color("ERROR", C.RED + C.BOLD, use_color))
        print(exc)
        return 2

    if chatgpt_running():
        print()
        print(color("ChatGPT is still running.", C.YELLOW + C.BOLD, use_color))
        print("Close the Windows app completely and run ghostchat again.")
        return 3

    limit = max(1, min(args.limit, 200))

    # Read-only listing first.
    try:
        ro = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, timeout=3)
        rows = fetch_recent(ro, limit)
        ro.close()
    except sqlite3.Error as exc:
        print()
        print(color("Could not read the database.", C.RED + C.BOLD, use_color))
        print(exc)
        return 4

    if not rows:
        print("\nNo non-Project ChatGPT Recents were found.")
        return 0

    print_recent(rows, use_color)

    if args.list:
        return 0

    # Determine the exact target before making a backup or opening write mode.
    if args.thread_id:
        selected_id = args.thread_id.strip()
        selected = next((row for row in rows if row[0] == selected_id), None)
        if selected is None:
            try:
                ro = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, timeout=3)
                selected = fetch_by_id(ro, selected_id)
                ro.close()
            except sqlite3.Error:
                selected = None
    else:
        selection = input(
            "Select the Ghost chat NUMBER, or paste its thread_id "
            "(Q to cancel): "
        ).strip()
        if selection.lower() in {"q", "quit", "exit"}:
            print("Cancelled. Nothing was changed.")
            return 0

        try:
            ro = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, timeout=3)
            selected = resolve_selection(ro, rows, selection)
            ro.close()
        except sqlite3.Error:
            selected = None

    if not selected:
        print()
        print(color("No matching ChatGPT thread found.", C.YELLOW, use_color))
        print("Nothing was changed.")
        return 5

    thread_id, title, missing = selected
    print()
    print(color("Selected local Recents entry", C.BOLD, use_color))
    print(f"Title:              {title or '(untitled)'}")
    print(f"thread_id:          {thread_id}")
    print(f"missing_candidate:  {missing}")
    print()
    print(
        color(
            "Only continue if this conversation was already deleted "
            "and this is the stuck local Ghost entry.",
            C.YELLOW,
            use_color,
        )
    )

    confirm = input('Type DELETE to remove ONLY this local entry: ').strip()
    if confirm != "DELETE":
        print("Cancelled. Nothing was changed.")
        return 0

    try:
        backup = create_backup()
    except Exception as exc:
        print()
        print(color("Backup failed. Nothing will be deleted.", C.RED + C.BOLD, use_color))
        print(exc)
        return 6

    print()
    print(color("Backup created:", C.GREEN, use_color))
    print(backup)

    try:
        con = sqlite3.connect(DB_PATH, timeout=3)
        try:
            count, remaining, integrity = delete_thread(con, thread_id)
        finally:
            con.close()
    except sqlite3.Error as exc:
        print()
        print(color("SQLite error.", C.RED + C.BOLD, use_color))
        print(exc)
        print(f"Backup: {backup}")
        return 7

    if count != 1:
        print()
        print(color("Safety stop.", C.RED + C.BOLD, use_color))
        print(f"Expected to delete exactly 1 row; SQLite reported {count}.")
        print("The change was not committed.")
        return 8

    if remaining:
        print()
        print(color("Verification failed.", C.RED + C.BOLD, use_color))
        print("The selected thread still appears in local_thread_catalog.")
        print(f"Backup: {backup}")
        return 9

    if not integrity or integrity[0] != "ok":
        print()
        print(color("Database integrity warning.", C.RED + C.BOLD, use_color))
        print(f"PRAGMA integrity_check returned: {integrity}")
        print(f"Backup: {backup}")
        return 10

    print()
    print(color("SUCCESS", C.GREEN + C.BOLD, use_color))
    print("Ghost Recents entry removed.")
    print("Database integrity: ok")
    print()
    print("Reopen ChatGPT and check Recents.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nCancelled.")
        raise SystemExit(130)
