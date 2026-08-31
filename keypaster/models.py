from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
from uuid import uuid4


@dataclass(slots=True)
class KeyMapping:
    id: str
    name: str
    key: str
    text: str
    enabled: bool = True

    @classmethod
    def create(cls, *, name: str, key: str, text: str) -> "KeyMapping":
        return cls(id=str(uuid4()), name=name.strip(), key=key, text=text, enabled=True)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "KeyMapping":
        return cls(
            id=str(data.get("id") or uuid4()),
            name=str(data.get("name", "")).strip(),
            key=str(data["key"]),
            text=str(data.get("text", "")),
            enabled=bool(data.get("enabled", True)),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AppSettings:
    start_with_windows: bool = False
    close_to_tray: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "AppSettings":
        data = data or {}
        return cls(
            start_with_windows=bool(data.get("start_with_windows", False)),
            close_to_tray=bool(data.get("close_to_tray", True)),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AppConfig:
    version: int = 1
    mappings: list[KeyMapping] = field(default_factory=list)
    settings: AppSettings = field(default_factory=AppSettings)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppConfig":
        return cls(
            version=int(data.get("version", 1)),
            mappings=[KeyMapping.from_dict(item) for item in data.get("mappings", [])],
            settings=AppSettings.from_dict(data.get("settings")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "mappings": [mapping.to_dict() for mapping in self.mappings],
            "settings": self.settings.to_dict(),
        }
