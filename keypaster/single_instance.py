from __future__ import annotations

import ctypes
import os
import threading
from ctypes import wintypes
from collections.abc import Callable


ERROR_ALREADY_EXISTS = 183
WAIT_OBJECT_0 = 0
WAIT_TIMEOUT = 258


if os.name == "nt":
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateEventW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.BOOL, wintypes.LPCWSTR]
    kernel32.CreateEventW.restype = wintypes.HANDLE
    kernel32.SetEvent.argtypes = [wintypes.HANDLE]
    kernel32.SetEvent.restype = wintypes.BOOL
    kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel32.WaitForSingleObject.restype = wintypes.DWORD
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
else:
    kernel32 = None


class SingleInstance:
    """Use a named auto-reset event to keep one KeyPaster instance per session.

    A second launch signals the existing instance to show its window and exits.
    """

    def __init__(self, name: str = r"Local\KeyPaster.ShowWindow.V1") -> None:
        if os.name != "nt":
            raise OSError("SingleInstance is Windows-only")
        ctypes.set_last_error(0)
        self._handle = kernel32.CreateEventW(None, False, False, name)
        if not self._handle:
            raise ctypes.WinError(ctypes.get_last_error())
        self.is_primary = ctypes.get_last_error() != ERROR_ALREADY_EXISTS
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def signal_existing(self) -> None:
        if self.is_primary:
            return
        if not kernel32.SetEvent(self._handle):
            raise ctypes.WinError(ctypes.get_last_error())

    def start_watcher(self, on_show_requested: Callable[[], None]) -> None:
        if not self.is_primary or self._thread:
            return

        def watch() -> None:
            while not self._stop.is_set():
                result = int(kernel32.WaitForSingleObject(self._handle, 250))
                if result == WAIT_OBJECT_0:
                    try:
                        on_show_requested()
                    except Exception:
                        pass
                elif result != WAIT_TIMEOUT:
                    return

        self._thread = threading.Thread(target=watch, name="KeyPasterSingleInstance", daemon=True)
        self._thread.start()

    def close(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1)
            self._thread = None
        if self._handle:
            kernel32.CloseHandle(self._handle)
            self._handle = None
