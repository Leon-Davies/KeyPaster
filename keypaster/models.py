from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
from uuid import uuid4

from .actions import PASTE_TEXT


CURRENT_CONFIG_VERSION = 2


@dataclass(slots=True)
class KeyMapping:
    id: str
    name: str
    key: str
    text: str
    enabled: bool = True
    action: str = PASTE_TEXT

    @classmethod
    def create(
        cls,
        *,
        name: str,
        key: str,
        text: str = "",
        action: str = PASTE_TEXT,
    ) -> "KeyMapping":
        return cls(
            id=str(uuid4()),
            name=name.strip(),
            key=key,
            text=text,
            enabled=True,
            action=action,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "KeyMapping":
        return cls(
            id=str(data.get("id") or uuid4()),
            name=str(data.get("name", "")).strip(),
            key=str(data["key"]),
            text=str(data.get("text", "")),
            enabled=bool(data.get("enabled", True)),
            action=str(data.get("action", PASTE_TEXT)),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AppSettings:
    start_with_windows: bool = False
    minimize_to_tray: bool = False
    close_to_tray: bool = False

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any] | None,
        *,
        legacy_config: bool = False,
    ) -> "AppSettings":
        data = data or {}
        if legacy_config:
            # Earlier releases silently defaulted close-to-tray on and had no
            # minimize setting. Reset both to the safer taskbar behaviour.
            return cls(start_with_windows=bool(data.get("start_with_windows", False)))
        return cls(
            start_with_windows=bool(data.get("start_with_windows", False)),
            minimize_to_tray=bool(data.get("minimize_to_tray", False)),
            close_to_tray=bool(data.get("close_to_tray", False)),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AppConfig:
    version: int = CURRENT_CONFIG_VERSION
    mappings: list[KeyMapping] = field(default_factory=list)
    settings: AppSettings = field(default_factory=AppSettings)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppConfig":
        source_version = int(data.get("version", 1))
        return cls(
            version=CURRENT_CONFIG_VERSION,
            mappings=[KeyMapping.from_dict(item) for item in data.get("mappings", [])],
            settings=AppSettings.from_dict(
                data.get("settings"),
                legacy_config=source_version < CURRENT_CONFIG_VERSION,
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "mappings": [mapping.to_dict() for mapping in self.mappings],
            "settings": self.settings.to_dict(),
        }
