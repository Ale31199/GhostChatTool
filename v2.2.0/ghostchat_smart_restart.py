from __future__ import annotations

import argparse
import ctypes
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import ghostchat_patch as patch

VERSION = "2.2.0"
WM_CLOSE = 0x0010
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
STATUS_FILE = patch.PATCH_DIR / "smart-restart-status.json"
LOG_FILE = patch.PATCH_DIR / "smart-restart.log"
MUTEX_NAME = r"Local\GhostChatSmartRestart"


def log(message: str) -> None:
    patch.PATCH_DIR.mkdir(parents=True, exist_ok=True)
    line = f"{datetime.now().isoformat(timespec='seconds')} {message}"
    with LOG_FILE.open("a", encoding="utf-8", errors="replace") as fh:
        fh.write(line + "\n")


def write_status(**updates) -> None:
    patch.PATCH_DIR.mkdir(parents=True, exist_ok=True)
    state = {}
    if STATUS_FILE.exists():
        try:
            state = json.loads(STATUS_FILE.read_text(encoding="utf-8"))
        except Exception:
            state = {}
    state.update({
        "version": VERSION,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        **updates,
    })
    tmp = STATUS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(STATUS_FILE)


def _process_image_name(pid: int) -> str | None:
    if os.name != "nt":
        return None
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return None
    try:
        size = ctypes.c_ulong(32768)
        buf = ctypes.create_unicode_buffer(size.value)
        if not kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
            return None
        return os.path.basename(buf.value).lower()
    finally:
        kernel32.CloseHandle(handle)


def request_graceful_close() -> int:
    """Post WM_CLOSE only to top-level windows owned by ChatGPT.exe."""
    if os.name != "nt":
        return 0
    user32 = ctypes.windll.user32
    count = 0

    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    @WNDENUMPROC
    def enum_proc(hwnd, lparam):
        nonlocal count
        if not user32.IsWindowVisible(hwnd):
            return True
        pid = ctypes.c_ulong(0)
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value and _process_image_name(pid.value) == "chatgpt.exe":
            user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
            count += 1
        return True

    user32.EnumWindows(enum_proc, 0)
    return count


def wait_until_closed(timeout: float) -> bool:
    deadline = time.monotonic() + max(0.0, timeout)
    while time.monotonic() < deadline:
        if not patch.chatgpt_running():
            return True
        time.sleep(0.25)
    return not patch.chatgpt_running()


def ask_force_close() -> bool:
    if os.name != "nt":
        return False
    MB_YESNO = 0x00000004
    MB_ICONWARNING = 0x00000030
    MB_DEFBUTTON2 = 0x00000100
    IDYES = 6
    rc = ctypes.windll.user32.MessageBoxW(
        None,
        "ChatGPT non si è chiuso normalmente.\n\n"
        "Vuoi forzarne la chiusura? Il testo non ancora inviato potrebbe andare perso.",
        "GhostChat Sync Fix",
        MB_YESNO | MB_ICONWARNING | MB_DEFBUTTON2,
    )
    return rc == IDYES


def force_close() -> bool:
    if os.name != "nt":
        return False
    try:
        proc = subprocess.run(
            ["taskkill", "/F", "/T", "/IM", "ChatGPT.exe"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return proc.returncode == 0 or not patch.chatgpt_running()
    except Exception:
        return False


def wait_until_running(timeout: float) -> bool:
    deadline = time.monotonic() + max(0.0, timeout)
    while time.monotonic() < deadline:
        if patch.chatgpt_running():
            return True
        time.sleep(0.25)
    return patch.chatgpt_running()


def post_launch_reconcile(wait_seconds: float) -> tuple[int, list[str]]:
    """Give the app time to sync, then conservatively scan/repair confirmed ghosts."""
    deadline = time.monotonic() + max(0.0, wait_seconds)
    removed_total = 0
    titles: list[str] = []
    # Several small passes catch logs written just after startup without keeping the
    # command alive for long. Every repair still requires exact deletion evidence.
    while time.monotonic() < deadline:
        time.sleep(min(3.0, max(0.2, deadline - time.monotonic())))
        try:
            result = patch.repair_once(allow_running=True, dry_run=False)
        except Exception as exc:
            log(f"post-launch reconcile skipped safely: {exc}")
            continue
        count = int(result.get("removed") or 0)
        if count:
            removed_total += count
            titles.extend(r.display_title for r in result.get("confirmed", []))
            log(f"post-launch repair removed={count} titles={titles!r}")
    return removed_total, titles


def acquire_mutex():
    if os.name != "nt":
        return None
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.CreateMutexW(None, False, MUTEX_NAME)
    if not handle:
        return None
    ERROR_ALREADY_EXISTS = 183
    if kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
        kernel32.CloseHandle(handle)
        return False
    return handle


def release_mutex(handle) -> None:
    if os.name == "nt" and handle not in (None, False):
        ctypes.windll.kernel32.CloseHandle(handle)


def run(close_timeout: float, startup_timeout: float, reconcile_wait: float) -> int:
    if os.name != "nt":
        print("GhostChat Smart Restart is Windows-only.")
        return 2

    mutex = acquire_mutex()
    if mutex is False:
        log("another smart restart is already running")
        return 0

    started = datetime.now().isoformat(timespec="seconds")
    write_status(running=True, started_at=started, stage="starting")
    log("smart restart started")
    try:
        # Catch already-confirmed ghosts before restarting. This is read/repair only
        # and never treats missing_candidate alone as proof.
        try:
            pre = patch.repair_once(allow_running=True, dry_run=False)
            pre_removed = int(pre.get("removed") or 0)
        except Exception as exc:
            pre_removed = 0
            log(f"pre-restart reconcile skipped safely: {exc}")

        if patch.chatgpt_running():
            write_status(stage="closing_chatgpt", pre_removed=pre_removed)
            windows = request_graceful_close()
            log(f"graceful close requested windows={windows}")
            if not wait_until_closed(close_timeout):
                log("graceful close timed out")
                if not ask_force_close():
                    write_status(running=False, stage="cancelled", result="force_close_declined")
                    return 3
                if not force_close() or not wait_until_closed(5.0):
                    log("force close failed")
                    write_status(running=False, stage="failed", result="could_not_close_chatgpt")
                    return 4
                log("ChatGPT force-closed after user confirmation")

        # With ChatGPT closed, perform one more safe pass. If startup from the previous
        # session had already emitted deletion evidence, this cleans it before reopen.
        write_status(stage="closed_reconcile")
        try:
            mid = patch.repair_once(allow_running=False, dry_run=False)
            mid_removed = int(mid.get("removed") or 0)
        except Exception as exc:
            mid_removed = 0
            log(f"closed reconcile skipped safely: {exc}")

        write_status(stage="launching_chatgpt", pre_removed=pre_removed, mid_removed=mid_removed)
        if not patch.launch_chatgpt():
            log("launch failed")
            write_status(running=False, stage="failed", result="launch_failed")
            return 5
        if not wait_until_running(startup_timeout):
            log("ChatGPT did not appear within startup timeout")
            write_status(running=False, stage="failed", result="startup_timeout")
            return 6

        write_status(stage="post_launch_reconcile")
        post_removed, titles = post_launch_reconcile(reconcile_wait)
        total = pre_removed + mid_removed + post_removed
        log(f"smart restart complete removed_total={total} titles={titles!r}")
        write_status(
            running=False,
            stage="complete",
            completed_at=datetime.now().isoformat(timespec="seconds"),
            result="ok",
            removed_total=total,
            post_removed=post_removed,
            post_repair_titles=titles,
        )
        return 0
    finally:
        release_mutex(mutex)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="One-click ChatGPT restart + conservative GhostChat reconcile")
    p.add_argument("--close-timeout", type=float, default=8.0)
    p.add_argument("--startup-timeout", type=float, default=20.0)
    p.add_argument("--reconcile-wait", type=float, default=12.0)
    p.add_argument("--version", action="version", version=f"GhostChat Smart Restart {VERSION}")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return run(args.close_timeout, args.startup_timeout, args.reconcile_wait)


if __name__ == "__main__":
    raise SystemExit(main())
