from __future__ import annotations

from dataclasses import dataclass


PASTE_TEXT = "paste_text"


@dataclass(frozen=True, slots=True)
class ActionOption:
    id: str
    label: str
    vk: int | None = None


ACTION_OPTIONS: tuple[ActionOption, ...] = (
    ActionOption(PASTE_TEXT, "Paste text"),
    ActionOption("volume_up", "Volume up", 0xAF),
    ActionOption("volume_down", "Volume down", 0xAE),
    ActionOption("volume_mute", "Mute / unmute", 0xAD),
    ActionOption("media_play_pause", "Play / pause", 0xB3),
    ActionOption("media_next", "Next track", 0xB0),
    ActionOption("media_previous", "Previous track", 0xB1),
    ActionOption("media_stop", "Stop media", 0xB2),
)

ACTION_BY_ID = {option.id: option for option in ACTION_OPTIONS}
ACTION_ID_BY_LABEL = {option.label: option.id for option in ACTION_OPTIONS}


def action_label(action_id: str) -> str:
    option = ACTION_BY_ID.get(action_id)
    return option.label if option else action_id


def action_labels() -> list[str]:
    return [option.label for option in ACTION_OPTIONS]


def action_vk(action_id: str) -> int:
    try:
        option = ACTION_BY_ID[action_id]
    except KeyError as exc:
        raise ValueError(f"Unsupported action: {action_id}") from exc
    if option.vk is None:
        raise ValueError(f"Action has no virtual key: {action_id}")
    return option.vk


def is_media_action(action_id: str) -> bool:
    return action_id in ACTION_BY_ID and action_id != PASTE_TEXT
