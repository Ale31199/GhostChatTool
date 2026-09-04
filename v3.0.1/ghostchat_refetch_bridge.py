from __future__ import annotations

import ctypes
import os
import re
from ctypes import wintypes
from dataclasses import dataclass
from datetime import datetime

APP_NAME = "GhostChat Refetch Bridge"
VERSION = "3.0.1"

TRIGGER_REQUIRED = (
    "chatgpt_conversation_update_ignored",
    "conversation_not_loaded",
    "refetch",
)


@dataclass
class ReloadResult:
    attempted: bool
    ok: bool
    strategy: str
    detail: str
    window_title: str = ""
    command_text: str = ""
    command_id: int | None = None


def is_refetch_ignored_event(line: str) -> bool:
    """Strictly identify the early remote-update signal we want to react to.

    This event is NOT treated as deletion evidence. It only requests a benign
    window reload/reconcile attempt. Deletion still requires conversation_deleted
    evidence in the existing GhostChat repair layer.
    """
    low = line.lower()
    return all(part.lower() in low for part in TRIGGER_REQUIRED)


def compact_event(line: str, max_len: int = 500) -> str:
    text = re.sub(r"\s+", " ", line).strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def _not_windows() -> ReloadResult:
    return ReloadResult(False, False, "unsupported", "Windows-only reload bridge")


def attempt_reload_window() -> ReloadResult:
    """Try to invoke ChatGPT's native Reload Window command without key injection.

    Safety properties:
    - does not type into the composer;
    - does not send chat messages;
    - does not read cookies/tokens;
    - does not patch/inject into ChatGPT;
    - only posts WM_COMMAND if a native menu item explicitly named Reload Window
      (or Italian equivalent) is discoverable on the ChatGPT top-level window.

    If the current app build does not expose such a native menu command, this
    function fails closed and performs no action.
    """
    if os.name != "nt":
        return _not_windows()

    user32 = ctypes.WinDLL("user32", use_last_error=True)

    # `ctypes.wintypes.WNDENUMPROC` is not exposed by every Python build.
    # Define the callback signature ourselves when it is missing. This is the
    # documented Win32 EnumWindows callback shape: BOOL CALLBACK(HWND, LPARAM).
    WNDENUMPROC = getattr(wintypes, "WNDENUMPROC", None)
    if WNDENUMPROC is None:
        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    EnumWindows = user32.EnumWindows
    EnumWindows.argtypes = [WNDENUMPROC, wintypes.LPARAM]
    EnumWindows.restype = wintypes.BOOL

    IsWindowVisible = user32.IsWindowVisible
    IsWindowVisible.argtypes = [wintypes.HWND]
    IsWindowVisible.restype = wintypes.BOOL

    GetWindowTextLengthW = user32.GetWindowTextLengthW
    GetWindowTextLengthW.argtypes = [wintypes.HWND]
    GetWindowTextLengthW.restype = ctypes.c_int

    GetWindowTextW = user32.GetWindowTextW
    GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    GetWindowTextW.restype = ctypes.c_int

    GetWindowThreadProcessId = user32.GetWindowThreadProcessId
    GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    GetWindowThreadProcessId.restype = wintypes.DWORD

    GetMenu = user32.GetMenu
    GetMenu.argtypes = [wintypes.HWND]
    GetMenu.restype = wintypes.HMENU

    GetMenuItemCount = user32.GetMenuItemCount
    GetMenuItemCount.argtypes = [wintypes.HMENU]
    GetMenuItemCount.restype = ctypes.c_int

    GetSubMenu = user32.GetSubMenu
    GetSubMenu.argtypes = [wintypes.HMENU, ctypes.c_int]
    GetSubMenu.restype = wintypes.HMENU

    GetMenuItemID = user32.GetMenuItemID
    GetMenuItemID.argtypes = [wintypes.HMENU, ctypes.c_int]
    GetMenuItemID.restype = wintypes.UINT

    GetMenuStringW = user32.GetMenuStringW
    GetMenuStringW.argtypes = [wintypes.HMENU, wintypes.UINT, wintypes.LPWSTR, ctypes.c_int, wintypes.UINT]
    GetMenuStringW.restype = ctypes.c_int

    PostMessageW = user32.PostMessageW
    PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    PostMessageW.restype = wintypes.BOOL

    # Resolve ChatGPT.exe PIDs with tasklist through the Windows API-free standard
    # shell path. We intentionally avoid process memory inspection.
    import subprocess

    pids: set[int] = set()
    try:
        cp = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq ChatGPT.exe", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            errors="ignore",
            timeout=5,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        for raw in (cp.stdout or "").splitlines():
            # CSV shape: "ChatGPT.exe","1234",...
            m = re.match(r'\s*"ChatGPT\.exe"\s*,\s*"(\d+)"', raw, re.I)
            if m:
                pids.add(int(m.group(1)))
    except Exception as exc:
        return ReloadResult(True, False, "native-menu", f"could not enumerate ChatGPT processes: {exc}")

    if not pids:
        return ReloadResult(False, False, "native-menu", "ChatGPT.exe is not running")

    windows: list[tuple[int, str]] = []

    @WNDENUMPROC
    def enum_cb(hwnd, lparam):
        try:
            if not IsWindowVisible(hwnd):
                return True
            pid = wintypes.DWORD()
            GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if int(pid.value) not in pids:
                return True
            n = GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(max(1, n + 1))
            GetWindowTextW(hwnd, buf, len(buf))
            title = buf.value
            windows.append((int(hwnd), title))
        except Exception:
            pass
        return True

    EnumWindows(enum_cb, 0)
    if not windows:
        return ReloadResult(True, False, "native-menu", "no visible ChatGPT top-level window found")

    labels = (
        "reload window",
        "reload",
        "ricarica finestra",
        "ricarica",
    )
    MF_BYPOSITION = 0x00000400
    WM_COMMAND = 0x0111
    INVALID_ID = 0xFFFFFFFF

    def walk_menu(menu, depth: int = 0):
        if not menu or depth > 8:
            return None
        count = GetMenuItemCount(menu)
        if count < 0:
            return None
        for pos in range(count):
            buf = ctypes.create_unicode_buffer(512)
            GetMenuStringW(menu, pos, buf, len(buf), MF_BYPOSITION)
            text = buf.value.replace("&", "").split("\t", 1)[0].strip()
            low = text.lower()
            submenu = GetSubMenu(menu, pos)
            if submenu:
                found = walk_menu(submenu, depth + 1)
                if found:
                    return found
            if low in labels or any(low.startswith(x + " ") for x in labels):
                command_id = int(GetMenuItemID(menu, pos))
                if command_id != INVALID_ID:
                    return command_id, text
        return None

    # Prefer the largest-title window first, which is normally the main window.
    for hwnd_int, title in sorted(windows, key=lambda x: len(x[1]), reverse=True):
        hwnd = wintypes.HWND(hwnd_int)
        menu = GetMenu(hwnd)
        if not menu:
            continue
        found = walk_menu(menu)
        if not found:
            continue
        command_id, text = found
        ok = bool(PostMessageW(hwnd, WM_COMMAND, command_id, 0))
        if ok:
            return ReloadResult(
                True,
                True,
                "native-menu",
                f"posted native menu command {command_id}",
                window_title=title,
                command_text=text,
                command_id=command_id,
            )
        return ReloadResult(
            True,
            False,
            "native-menu",
            f"PostMessageW failed with WinError {ctypes.get_last_error()}",
            window_title=title,
            command_text=text,
            command_id=command_id,
        )

    titles = ", ".join(repr(t or "(untitled)") for _, t in windows[:4])
    return ReloadResult(
        True,
        False,
        "native-menu",
        "ChatGPT window found, but no native Reload Window menu item is exposed; no action taken"
        + (f"; windows={titles}" if titles else ""),
    )


if __name__ == "__main__":
    import json
    from dataclasses import asdict

    result = attempt_reload_window()
    print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
    raise SystemExit(0 if result.ok else 2)
