from __future__ import annotations

import ctypes
import os
import sys
import threading
import time
from ctypes import wintypes
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

from .keys import key_vk
from .models import KeyMapping


if os.name != "nt":
    # Constants/classes can still be imported by tests on non-Windows systems.
    user32 = kernel32 = None
else:
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)


WM_HOTKEY = 0x0312
WM_APP = 0x8000
WM_RELOAD = WM_APP + 41
WM_STOP = WM_APP + 42
MOD_NOREPEAT = 0x4000
PM_NOREMOVE = 0x0000
CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002
GMEM_ZEROINIT = 0x0040
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
VK_CONTROL = 0x11
VK_V = 0x56


if os.name == "nt":
    ULONG_PTR = ctypes.c_size_t


    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [
            ("dx", wintypes.LONG),
            ("dy", wintypes.LONG),
            ("mouseData", wintypes.DWORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ULONG_PTR),
        ]


    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [
            ("wVk", wintypes.WORD),
            ("wScan", wintypes.WORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ULONG_PTR),
        ]


    class HARDWAREINPUT(ctypes.Structure):
        _fields_ = [
            ("uMsg", wintypes.DWORD),
            ("wParamL", wintypes.WORD),
            ("wParamH", wintypes.WORD),
        ]


    class INPUT_UNION(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]


    class INPUT(ctypes.Structure):
        _anonymous_ = ("union",)
        _fields_ = [("type", wintypes.DWORD), ("union", INPUT_UNION)]


    user32.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT]
    user32.RegisterHotKey.restype = wintypes.BOOL
    user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.UnregisterHotKey.restype = wintypes.BOOL
    user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
    user32.GetMessageW.restype = wintypes.BOOL
    user32.PeekMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT, wintypes.UINT]
    user32.PeekMessageW.restype = wintypes.BOOL
    user32.PostThreadMessageW.argtypes = [wintypes.DWORD, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.PostThreadMessageW.restype = wintypes.BOOL
    user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
    user32.SendInput.restype = wintypes.UINT

    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.OpenClipboard.restype = wintypes.BOOL
    user32.CloseClipboard.argtypes = []
    user32.CloseClipboard.restype = wintypes.BOOL
    user32.EmptyClipboard.argtypes = []
    user32.EmptyClipboard.restype = wintypes.BOOL
    user32.EnumClipboardFormats.argtypes = [wintypes.UINT]
    user32.EnumClipboardFormats.restype = wintypes.UINT
    user32.GetClipboardData.argtypes = [wintypes.UINT]
    user32.GetClipboardData.restype = wintypes.HANDLE
    user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    user32.SetClipboardData.restype = wintypes.HANDLE

    kernel32.GetCurrentThreadId.argtypes = []
    kernel32.GetCurrentThreadId.restype = wintypes.DWORD
    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
    kernel32.GlobalFree.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalFree.restype = wintypes.HGLOBAL
    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalLock.restype = wintypes.LPVOID
    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalUnlock.restype = wintypes.BOOL
    kernel32.GlobalSize.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalSize.restype = ctypes.c_size_t


def _require_windows() -> None:
    if os.name != "nt":
        raise OSError("KeyPaster's desktop runtime is supported on Windows only.")


@dataclass(frozen=True, slots=True)
class ClipboardFormatData:
    format_id: int
    data: bytes


@dataclass(frozen=True, slots=True)
class ClipboardSnapshot:
    formats: tuple[ClipboardFormatData, ...]
    skipped_formats: tuple[int, ...] = ()


class ClipboardController:
    """Copies HGLOBAL-backed clipboard formats so they can be restored after a paste.

    This covers the common Windows clipboard payloads used for Unicode/plain text,
    HTML/RTF, DIB images, file-drop payloads and many registered custom formats.
    Handle-only formats (for example a raw CF_BITMAP handle) are skipped rather than
    copied unsafely; common applications generally expose a DIB representation too.
    """

    def __init__(self, retries: int = 12, retry_delay: float = 0.02) -> None:
        _require_windows()
        self.retries = retries
        self.retry_delay = retry_delay

    def _open(self) -> None:
        for _ in range(self.retries):
            if user32.OpenClipboard(None):
                return
            time.sleep(self.retry_delay)
        error = ctypes.get_last_error()
        raise OSError(error, "Could not open the Windows clipboard")

    def snapshot(self) -> ClipboardSnapshot:
        self._open()
        captured: list[ClipboardFormatData] = []
        skipped: list[int] = []
        try:
            fmt = 0
            while True:
                ctypes.set_last_error(0)
                fmt = int(user32.EnumClipboardFormats(fmt))
                if fmt == 0:
                    break
                handle = user32.GetClipboardData(fmt)
                if not handle:
                    skipped.append(fmt)
                    continue
                size = int(kernel32.GlobalSize(handle))
                if size <= 0:
                    skipped.append(fmt)
                    continue
                pointer = kernel32.GlobalLock(handle)
                if not pointer:
                    skipped.append(fmt)
                    continue
                try:
                    captured.append(ClipboardFormatData(fmt, ctypes.string_at(pointer, size)))
                finally:
                    kernel32.GlobalUnlock(handle)
        finally:
            user32.CloseClipboard()
        return ClipboardSnapshot(tuple(captured), tuple(skipped))

    def set_text(self, text: str) -> None:
        payload = (text + "\0").encode("utf-16-le")
        self._open()
        try:
            if not user32.EmptyClipboard():
                raise ctypes.WinError(ctypes.get_last_error())
            self._set_global_data(CF_UNICODETEXT, payload)
        finally:
            user32.CloseClipboard()

    def restore(self, snapshot: ClipboardSnapshot) -> None:
        self._open()
        try:
            if not user32.EmptyClipboard():
                raise ctypes.WinError(ctypes.get_last_error())
            failures: list[int] = []
            for item in snapshot.formats:
                try:
                    self._set_global_data(item.format_id, item.data)
                except OSError:
                    failures.append(item.format_id)
            if failures:
                raise OSError(f"Could not restore clipboard formats: {failures}")
        finally:
            user32.CloseClipboard()

    @staticmethod
    def _set_global_data(format_id: int, data: bytes) -> None:
        handle = kernel32.GlobalAlloc(GMEM_MOVEABLE | GMEM_ZEROINIT, len(data))
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        pointer = kernel32.GlobalLock(handle)
        if not pointer:
            kernel32.GlobalFree(handle)
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            ctypes.memmove(pointer, data, len(data))
        finally:
            kernel32.GlobalUnlock(handle)
        if not user32.SetClipboardData(format_id, handle):
            kernel32.GlobalFree(handle)
            raise ctypes.WinError(ctypes.get_last_error())
        # Ownership transfers to the system after SetClipboardData succeeds.


def send_ctrl_v() -> None:
    _require_windows()
    events = (INPUT * 4)(
        INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(VK_CONTROL, 0, 0, 0, 0)),
        INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(VK_V, 0, 0, 0, 0)),
        INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(VK_V, 0, KEYEVENTF_KEYUP, 0, 0)),
        INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0, 0)),
    )
    sent = int(user32.SendInput(len(events), events, ctypes.sizeof(INPUT)))
    if sent != len(events):
        raise ctypes.WinError(ctypes.get_last_error())


class HotkeyManager:
    def __init__(self, on_hotkey: Callable[[KeyMapping], None]) -> None:
        _require_windows()
        self._on_hotkey = on_hotkey
        self._thread: threading.Thread | None = None
        self._thread_id = 0
        self._ready = threading.Event()
        self._reload_done = threading.Event()
        self._lock = threading.Lock()
        self._desired: list[KeyMapping] = []
        self._registered: dict[int, KeyMapping] = {}
        self._suspended = False
        self._last_errors: dict[str, str] = {}

    @property
    def suspended(self) -> bool:
        with self._lock:
            return self._suspended

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, name="KeyPasterHotkeys", daemon=True)
        self._thread.start()
        if not self._ready.wait(timeout=3):
            raise RuntimeError("Windows hotkey thread did not start.")

    def reload(self, mappings: Iterable[KeyMapping]) -> dict[str, str]:
        with self._lock:
            self._desired = [mapping for mapping in mappings if mapping.enabled]
        return self._request_reload()

    def set_suspended(self, suspended: bool) -> dict[str, str]:
        with self._lock:
            if self._suspended == suspended:
                return dict(self._last_errors)
            self._suspended = suspended
        return self._request_reload()

    def stop(self) -> None:
        if not self._thread or not self._thread.is_alive():
            return
        if self._thread_id:
            user32.PostThreadMessageW(self._thread_id, WM_STOP, 0, 0)
        self._thread.join(timeout=3)

    def _request_reload(self) -> dict[str, str]:
        if not self._thread or not self._thread.is_alive():
            return {}
        self._reload_done.clear()
        if not user32.PostThreadMessageW(self._thread_id, WM_RELOAD, 0, 0):
            raise ctypes.WinError(ctypes.get_last_error())
        self._reload_done.wait(timeout=3)
        with self._lock:
            return dict(self._last_errors)

    def _run(self) -> None:
        message = wintypes.MSG()
        # Creating a message queue is required before PostThreadMessage can target us.
        user32.PeekMessageW(ctypes.byref(message), None, 0, 0, PM_NOREMOVE)
        self._thread_id = int(kernel32.GetCurrentThreadId())
        self._ready.set()
        self._apply_registration()
        while True:
            result = int(user32.GetMessageW(ctypes.byref(message), None, 0, 0))
            if result <= 0:
                break
            if message.message == WM_HOTKEY:
                mapping = self._registered.get(int(message.wParam))
                if mapping:
                    try:
                        self._on_hotkey(mapping)
                    except Exception:
                        # The hotkey loop must remain alive even if a callback fails.
                        pass
            elif message.message == WM_RELOAD:
                self._apply_registration()
            elif message.message == WM_STOP:
                break
        self._unregister_all()

    def _unregister_all(self) -> None:
        for hotkey_id in list(self._registered):
            user32.UnregisterHotKey(None, hotkey_id)
        self._registered.clear()

    def _apply_registration(self) -> None:
        self._unregister_all()
        with self._lock:
            desired = list(self._desired)
            suspended = self._suspended
        errors: dict[str, str] = {}
        if not suspended:
            for hotkey_id, mapping in enumerate(desired, start=1):
                ctypes.set_last_error(0)
                if user32.RegisterHotKey(None, hotkey_id, MOD_NOREPEAT, key_vk(mapping.key)):
                    self._registered[hotkey_id] = mapping
                else:
                    code = ctypes.get_last_error()
                    errors[mapping.id] = f"Windows could not register this key (error {code})."
        with self._lock:
            self._last_errors = errors
        self._reload_done.set()


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def startup_command() -> str:
    if not is_frozen():
        raise RuntimeError("Start with Windows is available in the packaged KeyPaster.exe build.")
    return f'"{Path(sys.executable)}" --minimized'


def set_start_with_windows(enabled: bool) -> None:
    _require_windows()
    import winreg

    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
        if enabled:
            winreg.SetValueEx(key, "KeyPaster", 0, winreg.REG_SZ, startup_command())
        else:
            try:
                winreg.DeleteValue(key, "KeyPaster")
            except FileNotFoundError:
                pass
