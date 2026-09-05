from __future__ import annotations

import ctypes
import os
import subprocess
import time
from dataclasses import dataclass

CHATGPT_AUMID = r"OpenAI.Codex_2p2nqsd0c76g0!App"


@dataclass
class NudgeResult:
    attempted: bool
    ok: bool
    mode: str
    detail: str


def _foreground_process_name() -> str | None:
    """Return the foreground process executable name on Windows, or None."""
    if os.name != "nt":
        return None
    try:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return None
        pid = ctypes.c_ulong(0)
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if not pid.value:
            return None

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
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
    except Exception:
        return None


def chatgpt_is_foreground() -> bool:
    name = _foreground_process_name()
    return name == "chatgpt.exe"


def reactivate_chatgpt_if_foreground() -> NudgeResult:
    """Request a normal Windows app activation, but only while ChatGPT is already foreground.

    This is intentionally conservative: it never steals focus from another app and it does
    not inject code, send keyboard input, or touch auth/session files. The hypothesis is that
    a normal app activation may trigger the same lifecycle/refetch path that outbound activity
    appears to trigger in the affected Desktop build.
    """
    if os.name != "nt":
        return NudgeResult(False, False, "activate", "not_windows")
    if not chatgpt_is_foreground():
        return NudgeResult(False, False, "activate", "chatgpt_not_foreground")
    try:
        subprocess.Popen(
            ["explorer.exe", f"shell:AppsFolder\\{CHATGPT_AUMID}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return NudgeResult(True, True, "activate", "activation_requested")
    except Exception as exc:
        return NudgeResult(True, False, "activate", f"activation_failed:{exc}")


def _send_key(vk: int, key_up: bool = False) -> None:
    flags = 0x0002 if key_up else 0
    ctypes.windll.user32.keybd_event(vk, 0, flags, 0)


def search_toggle_if_foreground() -> NudgeResult:
    """Experimental manual-only nudge: Ctrl+K then Escape while ChatGPT is foreground.

    It sends no text and is never called automatically by the watcher. It exists only so the
    user can test whether opening/closing the app's search surface causes the missing refetch.
    """
    if os.name != "nt":
        return NudgeResult(False, False, "search-toggle", "not_windows")
    if not chatgpt_is_foreground():
        return NudgeResult(False, False, "search-toggle", "chatgpt_not_foreground")
    try:
        VK_CONTROL = 0x11
        VK_K = 0x4B
        VK_ESCAPE = 0x1B
        _send_key(VK_CONTROL, False)
        _send_key(VK_K, False)
        _send_key(VK_K, True)
        _send_key(VK_CONTROL, True)
        time.sleep(0.20)
        _send_key(VK_ESCAPE, False)
        _send_key(VK_ESCAPE, True)
        return NudgeResult(True, True, "search-toggle", "ctrl_k_then_escape_sent")
    except Exception as exc:
        return NudgeResult(True, False, "search-toggle", f"sendkeys_failed:{exc}")
