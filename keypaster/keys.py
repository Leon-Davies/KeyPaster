from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class KeyOption:
    id: str
    label: str
    vk: int
    category: str


_BASE_KEYS: list[KeyOption] = [
    KeyOption("PAGE_DOWN", "Page Down", 0x22, "Navigation"),
    KeyOption("PAGE_UP", "Page Up", 0x21, "Navigation"),
    KeyOption("HOME", "Home", 0x24, "Navigation"),
    KeyOption("END", "End", 0x23, "Navigation"),
    KeyOption("INSERT", "Insert", 0x2D, "Navigation"),
    KeyOption("DELETE", "Delete", 0x2E, "Navigation"),
    KeyOption("UP", "Up Arrow", 0x26, "Navigation"),
    KeyOption("DOWN", "Down Arrow", 0x28, "Navigation"),
    KeyOption("LEFT", "Left Arrow", 0x25, "Navigation"),
    KeyOption("RIGHT", "Right Arrow", 0x27, "Navigation"),
    KeyOption("ESCAPE", "Escape", 0x1B, "Common"),
    KeyOption("TAB", "Tab", 0x09, "Common"),
    KeyOption("ENTER", "Enter", 0x0D, "Common"),
    KeyOption("SPACE", "Space", 0x20, "Common"),
    KeyOption("BACKSPACE", "Backspace", 0x08, "Common"),
    KeyOption("PAUSE", "Pause / Break", 0x13, "Common"),
]

_FUNCTION_KEYS = [
    KeyOption(f"F{number}", f"F{number}", 0x70 + number - 1, "Function")
    for number in range(1, 25)
    if number != 12  # F12 is reserved by Windows for debuggers.
]

_LETTER_KEYS = [
    KeyOption(letter, letter, ord(letter), "Letters") for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
]

_NUMBER_KEYS = [
    KeyOption(f"DIGIT_{number}", str(number), ord(str(number)), "Numbers") for number in range(10)
]

_NUMPAD_KEYS = [
    KeyOption(f"NUMPAD_{number}", f"Numpad {number}", 0x60 + number, "Numpad")
    for number in range(10)
] + [
    KeyOption("NUMPAD_MULTIPLY", "Numpad *", 0x6A, "Numpad"),
    KeyOption("NUMPAD_ADD", "Numpad +", 0x6B, "Numpad"),
    KeyOption("NUMPAD_SUBTRACT", "Numpad -", 0x6D, "Numpad"),
    KeyOption("NUMPAD_DECIMAL", "Numpad .", 0x6E, "Numpad"),
    KeyOption("NUMPAD_DIVIDE", "Numpad /", 0x6F, "Numpad"),
]

KEY_OPTIONS: tuple[KeyOption, ...] = tuple(
    _BASE_KEYS + _FUNCTION_KEYS + _LETTER_KEYS + _NUMBER_KEYS + _NUMPAD_KEYS
)
KEY_BY_ID = {option.id: option for option in KEY_OPTIONS}
KEY_ID_BY_LABEL = {option.label: option.id for option in KEY_OPTIONS}


def key_label(key_id: str) -> str:
    option = KEY_BY_ID.get(key_id)
    return option.label if option else key_id


def key_vk(key_id: str) -> int:
    try:
        return KEY_BY_ID[key_id].vk
    except KeyError as exc:
        raise ValueError(f"Unsupported key: {key_id}") from exc


def key_labels() -> list[str]:
    return [option.label for option in KEY_OPTIONS]
