import pytest

from keypaster.keys import KEY_BY_ID, key_label, key_vk


def test_page_down_virtual_key() -> None:
    assert key_vk("PAGE_DOWN") == 0x22
    assert key_label("PAGE_DOWN") == "Page Down"


def test_f12_is_intentionally_not_available() -> None:
    assert "F12" not in KEY_BY_ID


def test_unknown_key_is_rejected() -> None:
    with pytest.raises(ValueError):
        key_vk("NOT_A_KEY")
