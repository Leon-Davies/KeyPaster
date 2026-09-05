from pathlib import Path

import pytest

from keypaster.config import ConfigError, ConfigStore
from keypaster.models import AppConfig, KeyMapping


def test_config_round_trip_preserves_unicode_and_multiline_text(tmp_path: Path) -> None:
    store = ConfigStore(tmp_path / "config.json")
    config = AppConfig(
        mappings=[
            KeyMapping.create(
                name="Review prompt",
                key="PAGE_DOWN",
                text="First line\nSecond line - café 🚀",
            )
        ]
    )
    store.save(config)
    loaded = store.load()
    assert loaded.mappings[0].name == "Review prompt"
    assert loaded.mappings[0].text == "First line\nSecond line - café 🚀"
    assert loaded.mappings[0].key == "PAGE_DOWN"
    assert loaded.mappings[0].action == "paste_text"


def test_old_config_without_action_defaults_to_paste_text_and_safe_tray_settings(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text(
        '{"version":1,"mappings":[{"id":"1","name":"Old","key":"PAGE_DOWN","text":"hello","enabled":true}],"settings":{"close_to_tray":true}}',
        encoding="utf-8",
    )
    loaded = ConfigStore(path).load()
    assert loaded.version == 2
    assert loaded.mappings[0].action == "paste_text"
    assert loaded.mappings[0].text == "hello"
    assert loaded.settings.minimize_to_tray is False
    assert loaded.settings.close_to_tray is False


def test_tray_settings_round_trip_for_current_config(tmp_path: Path) -> None:
    store = ConfigStore(tmp_path / "config.json")
    config = AppConfig()
    config.settings.minimize_to_tray = True
    config.settings.close_to_tray = True
    store.save(config)
    loaded = store.load()
    assert loaded.settings.minimize_to_tray is True
    assert loaded.settings.close_to_tray is True


def test_media_action_does_not_require_text(tmp_path: Path) -> None:
    store = ConfigStore(tmp_path / "config.json")
    config = AppConfig(
        mappings=[KeyMapping.create(name="Volume", key="PAGE_UP", action="volume_up")]
    )
    store.save(config)
    loaded = store.load()
    assert loaded.mappings[0].action == "volume_up"
    assert loaded.mappings[0].text == ""


def test_empty_store_returns_default_config(tmp_path: Path) -> None:
    config = ConfigStore(tmp_path / "missing.json").load()
    assert config.version == 2
    assert config.mappings == []
    assert config.settings.minimize_to_tray is False
    assert config.settings.close_to_tray is False


def test_duplicate_key_is_rejected(tmp_path: Path) -> None:
    store = ConfigStore(tmp_path / "config.json")
    config = AppConfig(
        mappings=[
            KeyMapping.create(name="One", key="PAGE_DOWN", text="one"),
            KeyMapping.create(name="Two", key="PAGE_DOWN", text="two"),
        ]
    )
    with pytest.raises(ConfigError, match="assigned more than once"):
        store.save(config)


def test_empty_text_is_rejected_for_text_action(tmp_path: Path) -> None:
    store = ConfigStore(tmp_path / "config.json")
    config = AppConfig(mappings=[KeyMapping.create(name="Empty", key="PAGE_UP", text="")])
    with pytest.raises(ConfigError, match="cannot be empty"):
        store.save(config)


def test_unknown_action_is_rejected(tmp_path: Path) -> None:
    store = ConfigStore(tmp_path / "config.json")
    config = AppConfig(
        mappings=[KeyMapping.create(name="Bad", key="PAGE_UP", action="not_an_action")]
    )
    with pytest.raises(ConfigError, match="Unsupported action"):
        store.save(config)
