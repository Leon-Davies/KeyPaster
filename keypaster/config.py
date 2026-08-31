from __future__ import annotations

import json
import os
from pathlib import Path

from .keys import KEY_BY_ID
from .models import AppConfig


class ConfigError(ValueError):
    pass


def default_config_path() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "KeyPaster" / "config.json"


class ConfigStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path) if path else default_config_path()

    def load(self) -> AppConfig:
        if not self.path.exists():
            return AppConfig()
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ConfigError(f"Could not read KeyPaster configuration: {exc}") from exc
        config = AppConfig.from_dict(raw)
        self.validate(config)
        return config

    def save(self, config: AppConfig) -> None:
        self.validate(config)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        payload = json.dumps(config.to_dict(), indent=2, ensure_ascii=False) + "\n"
        temporary.write_text(payload, encoding="utf-8")
        os.replace(temporary, self.path)

    @staticmethod
    def validate(config: AppConfig) -> None:
        seen_ids: set[str] = set()
        seen_keys: set[str] = set()
        for mapping in config.mappings:
            if not mapping.id:
                raise ConfigError("Every mapping requires an id.")
            if mapping.id in seen_ids:
                raise ConfigError("Duplicate mapping id found.")
            seen_ids.add(mapping.id)
            if mapping.key not in KEY_BY_ID:
                raise ConfigError(f"Unsupported key in configuration: {mapping.key}")
            if mapping.key in seen_keys:
                raise ConfigError(
                    f"The key '{mapping.key}' is assigned more than once. Each key can have one mapping."
                )
            seen_keys.add(mapping.key)
            if not mapping.text:
                raise ConfigError("Mapped text cannot be empty.")
