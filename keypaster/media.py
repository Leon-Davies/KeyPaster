from __future__ import annotations

import ctypes

from .windows import INPUT, INPUT_KEYBOARD, KEYBDINPUT, KEYEVENTF_KEYUP, _require_windows, user32


def send_virtual_key(vk: int) -> None:
    """Send one Windows virtual-key press and release using SendInput."""
    _require_windows()
    events = (INPUT * 2)(
        INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(vk, 0, 0, 0, 0)),
        INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(vk, 0, KEYEVENTF_KEYUP, 0, 0)),
    )
    sent = int(user32.SendInput(len(events), events, ctypes.sizeof(INPUT)))
    if sent != len(events):
        raise ctypes.WinError(ctypes.get_last_error())
