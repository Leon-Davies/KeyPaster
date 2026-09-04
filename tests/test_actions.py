import pytest

from keypaster.actions import ACTION_BY_ID, PASTE_TEXT, action_label, action_vk


def test_text_action_has_no_virtual_key() -> None:
    assert action_label(PASTE_TEXT) == "Paste text"
    with pytest.raises(ValueError):
        action_vk(PASTE_TEXT)


def test_windows_media_virtual_keys_match_win32_values() -> None:
    assert action_vk("volume_mute") == 0xAD
    assert action_vk("volume_down") == 0xAE
    assert action_vk("volume_up") == 0xAF
    assert action_vk("media_next") == 0xB0
    assert action_vk("media_previous") == 0xB1
    assert action_vk("media_stop") == 0xB2
    assert action_vk("media_play_pause") == 0xB3


def test_action_catalogue_contains_text_and_media_actions() -> None:
    assert PASTE_TEXT in ACTION_BY_ID
    assert "media_play_pause" in ACTION_BY_ID
