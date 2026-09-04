from __future__ import annotations

import ctypes

from . import windows


def send_virtual_key(vk: int) -> None:
    """Send one Windows virtual-key press and release using SendInput."""
    windows._require_windows()
    events = (windows.INPUT * 2)(
        windows.INPUT(
            type=windows.INPUT_KEYBOARD,
            ki=windows.KEYBDINPUT(vk, 0, 0, 0, 0),
        ),
        windows.INPUT(
            type=windows.INPUT_KEYBOARD,
            ki=windows.KEYBDINPUT(vk, 0, windows.KEYEVENTF_KEYUP, 0, 0),
        ),
    )
    sent = int(
        windows.user32.SendInput(
            len(events),
            events,
            ctypes.sizeof(windows.INPUT),
        )
    )
    if sent != len(events):
        raise ctypes.WinError(ctypes.get_last_error())
